# Start the Obsei prototype service (PowerShell helper)
param(
    [int]$Port = 5001,
    [string]$Host = '127.0.0.1'
)

Write-Host "Starting Obsei prototype service on http://$Host`:$Port"

if (Test-Path -Path .venv-obsei) {
    Write-Host "Activating venv .venv-obsei"
    . .\.venv-obsei\Scripts\Activate.ps1
} else {
    Write-Host ".venv-obsei not found. Create it with:`n  python -m venv .venv-obsei; . .\.venv-obsei\Scripts\Activate.ps1; pip install -r requirements-obsei.txt"
}

# Run uvicorn
python -m uvicorn services.obsei_service.main:app --host $Host --port $Port --reload
