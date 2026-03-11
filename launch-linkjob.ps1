$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Fill in LinkedIn credentials before the first real run."
}

Write-Host ""
Write-Host "LinkJob Launcher"
Write-Host "1. Run bot"
Write-Host "2. Open dashboard"
Write-Host "3. Start scheduler"
Write-Host "4. Start scheduler in background"
Write-Host "5. Bootstrap session key"
Write-Host "6. Dry run"
Write-Host ""

$choice = Read-Host "Select an option"

switch ($choice) {
    "1" { python main.py run }
    "2" { python main.py dashboard }
    "3" { python main.py scheduler }
    "4" { Start-Process python -ArgumentList 'main.py scheduler' -WorkingDirectory $PSScriptRoot }
    "5" { python main.py bootstrap }
    "6" { python main.py run --dry-run }
    default { Write-Host "Invalid option"; exit 1 }
}
