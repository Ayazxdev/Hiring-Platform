"""
Run All Agent Services - Enhanced Version
Starts all 10 agent services with improved error handling, health checks, and logging.
"""
import subprocess
import sys
import os
import time
import urllib.request
import urllib.error
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_python_bin() -> str:
    """Get the Python binary to use."""
    return os.environ.get("AGENT_PYTHON") or sys.executable

def wait_for_health(url: str, timeout_s: int = 30, service_name: str = "") -> bool:
    """Wait for a service to become healthy."""
    deadline = time.time() + timeout_s
    last_err = None
    
    print(f"  ⏳ Waiting for {service_name} health check at {url}...")
    
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {service_name} is healthy!")
                    return True
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    
    print(f"  {Colors.FAIL}✗{Colors.ENDC} {service_name} health check failed: {last_err}")
    return False

def log_reader(pipe, prefix: str, color: str):
    """Read logs from a pipe and print with colored prefix."""
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"{color}[{timestamp}][{prefix}]{Colors.ENDC} {line.rstrip()}")
    except Exception:
        pass

def start_service(script_name: str, port: int, prefix: str, color: str) -> subprocess.Popen:
    """Start a service and return the process handle."""
    py = get_python_bin()
    
    print(f"\n{Colors.BOLD}Starting {prefix}{Colors.ENDC}")
    print(f"  📄 Script: {script_name}")
    print(f"  🔌 Port: {port}")
    
    env = os.environ.copy()
    env["PORT"] = str(port)
    
    try:
        p = subprocess.Popen(
            [py, script_name],
            cwd=os.path.dirname(__file__),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )
        
        # Start log streaming thread
        thread = threading.Thread(
            target=log_reader, 
            args=(p.stdout, prefix, color), 
            daemon=True
        )
        thread.start()
        
        return p
        
    except Exception as e:
        print(f"  {Colors.FAIL}✗{Colors.ENDC} Failed to start {prefix}: {e}")
        raise

def main():
    """Main function to start all services."""
    print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 Starting All Agent Services{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")
    
    processes: List[subprocess.Popen] = []
    
    # Define all services with their configurations
    # Format: (script, port, health_url, display_name, color)
    services = [
        ("ats_service.py", 8004, "http://localhost:8004/health", "ATS Fraud Detection", Colors.OKCYAN),
        ("github_service.py", 8005, "http://localhost:8005/health", "GitHub Analysis", Colors.OKBLUE),
        ("leetcode_service.py", 8006, "http://localhost:8006/health", "LeetCode Service", Colors.OKGREEN),
        ("codeforce_service.py", 8011, "http://localhost:8011/health", "Codeforces Service", Colors.WARNING),
        ("linkedin_service.py", 8007, "http://localhost:8007/health", "LinkedIn Service", Colors.OKCYAN),
        ("skill_agent_service.py", 8003, "http://localhost:8003/health", "Skill Agent", Colors.OKBLUE),
        ("conditional_test_service.py", 8009, "http://localhost:8009/health", "JD Assessment", Colors.OKGREEN),
        ("bias_agent_service.py", 8002, "http://localhost:8002/health", "Bias Detection", Colors.WARNING),
        ("matching_agent_service.py", 8001, "http://localhost:8001/health", "Matching Agent", Colors.OKCYAN),
        ("passport_service.py", 8008, "http://localhost:8008/health", "Passport Service", Colors.OKBLUE),
    ]
    
    failed_services = []
    
    try:
        # Start all services
        for script, port, health, name, color in services:
            try:
                p = start_service(script, port, name, color)
                processes.append((p, name, script))
                
                # Give the process time to start
                time.sleep(2.0)
                
                # Check if it crashed immediately
                if p.poll() is not None:
                    error_msg = f"{name} ({script}) exited early with code {p.returncode}"
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {error_msg}")
                    failed_services.append(name)
                    continue
                
                # Wait for health check
                if not wait_for_health(health, timeout_s=30, service_name=name):
                    failed_services.append(name)
                    
            except Exception as e:
                print(f"  {Colors.FAIL}✗{Colors.ENDC} Failed to start {name}: {e}")
                failed_services.append(name)
        
        # Summary
        print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
        successful = len(services) - len(failed_services)
        
        if failed_services:
            print(f"{Colors.WARNING}⚠️  {successful}/{len(services)} services started successfully{Colors.ENDC}")
            print(f"{Colors.FAIL}Failed services:{Colors.ENDC}")
            for service in failed_services:
                print(f"  • {service}")
        else:
            print(f"{Colors.OKGREEN}✅ All {len(services)} services started successfully!{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")
        
        # Display service endpoints
        print(f"{Colors.BOLD}📡 Service Endpoints:{Colors.ENDC}")
        for script, port, health, name, color in services:
            if name not in failed_services:
                print(f"  {color}•{Colors.ENDC} {name}: http://localhost:{port}")
        
        print(f"\n{Colors.BOLD}Press Ctrl+C to stop all services{Colors.ENDC}\n")
        
        # Monitor services
        while True:
            time.sleep(2)
            
            # Check if any process died
            for i, (p, name, script) in enumerate(processes):
                if p.poll() is not None and name not in failed_services:
                    print(f"\n{Colors.FAIL}❌ CRITICAL: {name} died with code {p.returncode}{Colors.ENDC}")
                    failed_services.append(name)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}🛑 Stopping all services...{Colors.ENDC}")
    
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Error: {str(e)}{Colors.ENDC}")
    
    finally:
        # Cleanup: terminate all processes
        print(f"{Colors.WARNING}Terminating processes...{Colors.ENDC}")
        for p, name, script in processes:
            try:
                p.terminate()
                print(f"  • Stopped {name}")
            except Exception as e:
                print(f"  • Error stopping {name}: {e}")
        
        # Wait a bit for graceful shutdown
        time.sleep(1)
        
        # Force kill any remaining processes
        for p, name, script in processes:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass
        
        print(f"\n{Colors.OKGREEN}All services stopped. Goodbye! 👋{Colors.ENDC}\n")

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    main()
