"""
Start All Agent Services
Utility script to start all 10 agent services simultaneously.

Fixes vs previous version:
- Uses the current Python interpreter (or AGENT_PYTHON env var) consistently
- Fails fast if any service crashes on startup
- Verifies each service is actually listening by calling /health
"""
import subprocess
import sys
import os
import time
import urllib.request
import urllib.error

def _python_bin() -> str:
    return os.environ.get("AGENT_PYTHON") or sys.executable

def _wait_health(url: str, timeout_s: int = 20) -> None:
    deadline = time.time() + timeout_s
    last_err = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise RuntimeError(f"Health check failed for {url}: {last_err}")

def start_service(script_name: str, port: int) -> subprocess.Popen:
    """Start a service in a separate process and return the process handle."""
    py = _python_bin()
    print(f"Starting {script_name} on port {port} using: {py}")
    return subprocess.Popen(
        [py, script_name],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

def _drain_output(p: subprocess.Popen, max_lines: int = 200) -> str:
    if not p.stdout:
        return ""
    lines = []
    # non-blocking-ish read: small sleep loop
    start = time.time()
    while time.time() - start < 1.0:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)

def main():
    print("=" * 60)
    print("Starting All Agent Services")
    print("=" * 60)

    processes: list[subprocess.Popen] = []

    services = [
        ("matching_agent_service.py", 8001, "http://localhost:8001/health"),
        ("bias_agent_service.py", 8002, "http://localhost:8002/health"),
        ("skill_agent_service.py", 8003, "http://localhost:8003/health"),
        ("ats_service.py", 8004, "http://localhost:8004/health"),
        ("github_service.py", 8005, "http://localhost:8005/health"),
        ("leetcode_service.py", 8006, "http://localhost:8006/health"),
        ("linkedin_service.py", 8007, "http://localhost:8007/health"),
        ("passport_service.py", 8008, "http://localhost:8008/health"),
        ("conditional_test_service.py", 8009, "http://localhost:8009/health"),
        ("codeforce_service.py", 8011, "http://localhost:8011/health"),
    ]

    try:
        for script, port, health in services:
            p = start_service(script, port)
            processes.append(p)

            # Give the process a moment to import + bind
            time.sleep(0.8)

            # If it already exited, show logs and abort.
            if p.poll() is not None:
                out = _drain_output(p)
                raise RuntimeError(
                    f"{script} exited early with code {p.returncode}.\n"
                    f"--- last output ---\n{out}\n-------------------"
                )

            # Wait until health endpoint responds.
            _wait_health(health, timeout_s=20)

        print("\n" + "=" * 60)
        print("All services are up ✅")
        print("=" * 60)
        print("Matching Agent:       http://localhost:8001")
        print("Bias Agent:          http://localhost:8002")
        print("Skill Agent:         http://localhost:8003")
        print("ATS Agent:            http://localhost:8004")
        print("GitHub Agent:         http://localhost:8005")
        print("LeetCode Agent:       http://localhost:8006")
        print("LinkedIn Agent:        http://localhost:8007")
        print("Passport Agent:       http://localhost:8008")
        print("Conditional Test:      http://localhost:8009")
        print("Codeforces Agent:      http://localhost:8011")
        print("=" * 60)
        print("\nPress Ctrl+C to stop all services\n")

        # Tail outputs (optional). For now, just block.
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all services...")
    except Exception as e:
        print("\n❌ Failed to start agent services.")
        print(str(e))
    finally:
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass

if __name__ == "__main__":
    main()
