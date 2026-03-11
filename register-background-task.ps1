$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonCmd = (Get-Command python -ErrorAction Stop).Source
$taskName = "LinkJob Background Scheduler"
$scriptPath = Join-Path $PSScriptRoot "main.py"
$workDir = $PSScriptRoot

$action = New-ScheduledTaskAction `
    -Execute $pythonCmd `
    -Argument "`"$scriptPath`" scheduler" `
    -WorkingDirectory $workDir

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Runs the LinkJob scheduler in the background at user logon." `
    -Force | Out-Null

Write-Host "Registered scheduled task: $taskName"
