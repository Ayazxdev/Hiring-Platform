"""
Start All Agent Services (Complete Pipeline)
Utility script to start all 10 agent services simultaneously with real-time log streaming.
"""
import subprocess
import sys
import os
import time
import urllib.request
import urllib.error
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root directory (parent of agents_services)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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

def log_reader(pipe, prefix):
    """Read logs from a pipe and print with a prefix."""
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                if line:
                    print(f"[{prefix}] {line.rstrip()}")
    except Exception:
        pass

def start_service(script_name: str, port: int, prefix: str) -> subprocess.Popen:
    """Start a service and return the process handle."""
    py = _python_bin()
    print(f"Starting {prefix} ({script_name}) on port {port}...")
    env = os.environ.copy()
    env["PORT"] = str(port)
    p = subprocess.Popen(
        [py, script_name],
        cwd=os.path.dirname(__file__),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1, # Line buffered
    )
    
    # Start log streaming thread immediately
    thread = threading.Thread(target=log_reader, args=(p.stdout, prefix), daemon=True)
    thread.start()
    
    return p

def main():
    print("=" * 80)
    print("Starting All Agent Services - Complete Pipeline (10 Services)")
    print("=" * 80)

    processes: list[subprocess.Popen] = []

    services = [
        # Stage: (script, port, health_url, prefix)
        ("ats_service.py", 8004, "http://localhost:8004/health", "ATS"),
        ("github_service.py", 8005, "http://localhost:8005/health", "GitHub"),
        ("leetcode_service.py", 8006, "http://localhost:8006/health", "LeetCode"),
        ("codeforce_service.py", 8011, "http://localhost:8011/health", "Codeforce"),
        ("linkedin_service.py", 8007, "http://localhost:8007/health", "LinkedIn"),
        ("skill_agent_service.py", 8003, "http://localhost:8003/health", "Skill"),
        ("conditional_test_service.py", 8009, "http://localhost:8009/health", "JD-Assessment"),
        ("bias_agent_service.py", 8002, "http://localhost:8002/health", "Bias"),
        ("matching_agent_service.py", 8001, "http://localhost:8001/health", "Match"),
        ("passport_service.py", 8008, "http://localhost:8008/health", "Passport"),
    ]

    try:
        for script, port, health, prefix in services:
            p = start_service(script, port, prefix)
            processes.append(p)

            # Give the process a moment to import + bind
            time.sleep(1.0)

            # If it already exited, abort
            if p.poll() is not None:
                raise RuntimeError(f"{prefix} ({script}) exited early with code {p.returncode}.")

            # Wait until health endpoint responds
            _wait_health(health, timeout_s=30)

        print("\n" + "=" * 80)
        print("All agent services are up and streaming logs ✅")
        print("=" * 80)
        print("\n🔄 PIPELINE STAGES READY\n")
        
        # Block until interrupted
        while True:
            time.sleep(1)
            # Check if any process died
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    script, port, health, prefix = services[i]
                    print(f"\n❌ CRITICAL: Service {prefix} died with code {p.returncode}")
                    return

    except KeyboardInterrupt:
        print("\n\nStopping all services...")
    except Exception as e:
        print("\n❌ Failed to start agent services.")
        print(str(e))
    finally:
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        
        time.sleep(1)
        print("\nAll services stopped. Goodbye! 👋")

if __name__ == "__main__":
    main()
