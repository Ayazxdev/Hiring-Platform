$PROJECT_ROOT = $PSScriptRoot
Set-Location $PROJECT_ROOT

$env:PYTHONPATH="$PROJECT_ROOT\backend;$PROJECT_ROOT"
$env:ZYND_REGISTRY_URL="https://registry.zynd.ai"
$env:ZYND_WEBHOOK_HOST="127.0.0.1"
$env:USE_ZYND="1"
$env:LLM_BACKEND="ollama"
$env:OLLAMA_MODEL="llama3.2"
$env:LLM_MODEL="meta-llama/llama-3.1-8b-instruct:free"
$env:OPENROUTER_MODEL="meta-llama/llama-3.1-8b-instruct:free"
$env:OPENROUTER_SCRAPER_MODEL="meta-llama/llama-3.1-8b-instruct:free"

# Automatically detect venv or system python
$VENV_PY = "$PROJECT_ROOT\.venv\Scripts\python.exe"
if (Test-Path $VENV_PY) {
    $PYTHON_CMD = $VENV_PY
} else {
    $PYTHON_CMD = "python"
}

$ports = 5100, 5101, 5102, 5103, 5104, 5105, 5106, 5107
foreach ($port in $ports) {
    Write-Host "Checking port $port..."
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $proc_id = $conn.OwningProcess
            if ($proc_id -gt 0) {
                Write-Host "Killing process $proc_id on port $port"
                Stop-Process -Id $proc_id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# Write-Host "🧹 Resetting agent state to avoid unauthorized errors..." -ForegroundColor Yellow
# & $PYTHON_CMD reset_for_demo.py

Start-Sleep -s 3

# Start Ollama if not already running (check via TCP port, not HTTP, to avoid false negatives)
Write-Host "Checking Ollama..."
$ollamaPort = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
if (-not $ollamaPort) {
    Write-Host "Starting Ollama server..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$Host.UI.RawUI.WindowTitle = 'OLLAMA SERVER'; ollama serve }" -WorkingDirectory $PROJECT_ROOT
    Start-Sleep -s 5
    Write-Host "Ollama started."
} else {
    Write-Host "Ollama already running on port 11434."
}

# Function to start a visible agent window with auto-hold on error
function Start-VisibleAgent {
    param (
        [string]$Name,
        [string]$Command,
        [string]$Port
    )
    Write-Host "Starting $Name ($Port)..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$env:PYTHONPATH='$PROJECT_ROOT\backend;$PROJECT_ROOT'; `$env:USE_ZYND='1'; `$env:LLM_BACKEND='ollama'; `$env:OLLAMA_MODEL='llama3.2'; `$env:LLM_MODEL='meta-llama/llama-3.1-8b-instruct:free'; `$env:OPENROUTER_MODEL='meta-llama/llama-3.1-8b-instruct:free'; `$env:OPENROUTER_SCRAPER_MODEL='meta-llama/llama-3.1-8b-instruct:free'; `$Host.UI.RawUI.WindowTitle = '$Name ($Port)'; & '$PYTHON_CMD' -m $Command }" -WorkingDirectory $PROJECT_ROOT
    Start-Sleep -s 3
}

# 1. Backend (needs to run from backend/ so uvicorn finds app.main)
Write-Host "Starting BACKEND API (8012)..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$env:PYTHONPATH='$PROJECT_ROOT\backend;$PROJECT_ROOT'; `$env:USE_ZYND='1'; `$Host.UI.RawUI.WindowTitle = 'BACKEND API (8012)'; & '$PYTHON_CMD' -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --log-level info }" -WorkingDirectory "$PROJECT_ROOT\backend"
Start-Sleep -s 5

# 2. Matching Agent
Start-VisibleAgent -Name "MATCHING AGENT" -Command "zynd_integration.agents.matching_agent" -Port "5101"

# 3. Bias Agent
Start-VisibleAgent -Name "BIAS AGENT" -Command "zynd_integration.agents.bias_agent" -Port "5102"

# 4. Skill Agent
Start-VisibleAgent -Name "SKILL AGENT" -Command "zynd_integration.agents.skill_agent" -Port "5103"

# 5. ATS Agent
Start-VisibleAgent -Name "ATS AGENT" -Command "zynd_integration.agents.ats_agent" -Port "5104"
# 6. Passport Agent
Start-VisibleAgent -Name "PASSPORT AGENT" -Command "zynd_integration.agents.passport_agent" -Port "5105"

# 7. GitHub Agent
Start-VisibleAgent -Name "GITHUB AGENT" -Command "zynd_integration.agents.github_agent" -Port "5106"

# 8. LinkedIn Agent
Start-VisibleAgent -Name "LINKEDIN AGENT" -Command "zynd_integration.agents.linkedin_agent" -Port "5107"

# 9. LeetCode Agent
Start-VisibleAgent -Name "LEETCODE AGENT" -Command "zynd_integration.agents.leetcode_agent" -Port "5108"

# 10. Codeforce Agent
Start-VisibleAgent -Name "CODEFORCE AGENT" -Command "zynd_integration.agents.codeforce_agent" -Port "5109"

Write-Host "
================================================================
 DEMO MODE STARTED
================================================================
All agents are running in separate windows.
Arrange them on your screen to show activity during the demo.
Backend API: http://localhost:8012
Frontend:    http://localhost:5173 (run 'npm run dev' separately)
================================================================
"
