#!/usr/bin/env python3
"""Dynamic multilingual Playwright task runner for GitHub Actions."""
import argparse, ipaddress, json, os, re, shutil, socket, subprocess, sys, tempfile, traceback, uuid
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path.cwd()
OUTPUT = ROOT / 'output.json'
ARTIFACTS = ROOT / 'artifacts'
MAX_REPAIRS = 5

def sandbox_environment():
    """Return a minimal host environment for Docker CLI and syntax checks."""
    root = ROOT / ".agent-runner-host"
    home, temporary = root / "home", root / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    temporary.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(home),
        "TMPDIR": str(temporary),
        "TEMP": str(temporary),
        "TMP": str(temporary),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def build_sandbox_command(workspace, container_name):
    """Build a no-secret, least-privilege Playwright container invocation."""
    image = os.getenv(
        "BROWSER_SANDBOX_IMAGE",
        "mcr.microsoft.com/playwright/python:v1.52.0-noble",
    )
    network = os.getenv("BROWSER_SANDBOX_NETWORK", "uba-agent-sandbox")
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    gid = os.getgid() if hasattr(os, "getgid") else 1000
    return [
        "docker", "run", "--rm", "--name", container_name,
        "--network", network,
        "--read-only", "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=128", "--memory=2g", "--cpus=2", "--shm-size=1g",
        "--ulimit", "nofile=256:256",
        "--ulimit", "fsize=26214400:26214400",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=512m",
        "--user", f"{uid}:{gid}",
        "--env", "HOME=/tmp",
        "--env", "TMPDIR=/tmp",
        "--env", "TEMP=/tmp",
        "--env", "TMP=/tmp",
        "--env", "LANG=C.UTF-8",
        "--env", "LC_ALL=C.UTF-8",
        "--env", "PYTHONNOUSERSITE=1",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        "--volume", f"{workspace}:/work",
        "--workdir", "/work",
        "--entrypoint", "python",
        image, "/work/generated_task.py",
    ]


def validate_public_target(value):
    """Resolve every DNS answer and reject any non-global IPv4/IPv6 target."""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError):
        raise ValueError("Target URL is malformed.") from None
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("Only absolute public HTTP(S) URLs without credentials are allowed.")

    host = parsed.hostname.rstrip(".").lower()
    if "%" in host or host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Local and internal targets are blocked.")

    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError:
            raise ValueError("Target hostname could not be resolved.") from None
        addresses = set()
        for record in records:
            try:
                addresses.add(ipaddress.ip_address(record[4][0].split("%", 1)[0]))
            except (ValueError, IndexError, TypeError):
                continue

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private, loopback, link-local, multicast, reserved, and non-global targets are blocked.")
    return value


def _copy_sandbox_artifacts(workspace):
    source = workspace / "artifacts"
    if not source.is_dir() or source.is_symlink():
        return
    for current, directories, files in os.walk(source, followlinks=False):
        current_path = Path(current)
        directories[:] = [
            name for name in directories
            if not (current_path / name).is_symlink()
        ]
        for name in files:
            item = current_path / name
            if item.is_symlink() or not item.is_file():
                continue
            relative = item.relative_to(source)
            destination = ARTIFACTS / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, destination)


def main():
    parser = argparse.ArgumentParser(description='Dynamic multilingual browser task executor')
    parser.add_argument('--task-prompt', default=os.getenv('TASK_PROMPT', ''))
    parser.add_argument('--target-url', default=os.getenv('TARGET_URL', ''))
    parser.add_argument('--fallback-provider', default=os.getenv('FALLBACK_PROVIDER', 'none'))
    parser.add_argument('--provider', default=os.getenv('PRIMARY_PROVIDER', ''))
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if not args.task_prompt.strip(): parser.error('task_prompt is required')
    try:\n        args.target_url = validate_public_target(args.target_url)\n    except ValueError as exc:\n        parser.error(str(exc))
    if not args.provider: parser.error('PRIMARY_PROVIDER is required')
    ARTIFACTS.mkdir(exist_ok=True)
    history, code, error = [], '', ''
    providers = [args.provider]
    if args.fallback_provider and args.fallback_provider.lower() not in ('none', args.provider.lower()): providers.append(args.fallback_provider)
    for attempt in range(MAX_REPAIRS + 1):
        provider = providers[1] if attempt > 0 and len(providers) > 1 else providers[0]
        try:
            code = extract_code(ask_model(provider, build_prompt(args.task_prompt, args.target_url, code, error)))
            if not code: raise RuntimeError('Provider returned empty script')
            success, logs = execute_script(code, args.timeout)
            history.append({'attempt': attempt, 'provider': provider, 'success': success, 'log': logs[-3000:]})
            (ARTIFACTS / 'browser.log').write_text('\\n\\n'.join(item['log'] for item in history), encoding='utf-8')
            if success:
                data = json.loads(OUTPUT.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    data.update({'success': True, 'provider': provider, 'repair_attempts': attempt})
                    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps({'success': True, 'provider': provider, 'repair_attempts': attempt}))
                return 0
            error = logs
        except Exception:
            error = traceback.format_exc()
            history.append({'attempt': attempt, 'provider': provider, 'success': False, 'log': error[-3000:]})
            (ARTIFACTS / 'browser.log').write_text('\\n\\n'.join(item['log'] for item in history), encoding='utf-8')
    OUTPUT.write_text(json.dumps({'success': False, 'error': error, 'attempts': history}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'success': False, 'error': error[-4000:]}))
    return 1

if __name__ == '__main__': raise SystemExit(main())
