<#
Purpose: launch SmartBrew and automatically start/reuse its optional local Ollama server on Windows.
Inputs: Port (default 8765), optional Database path, and SkipAI to omit model-server preparation.
Outputs: foreground SmartBrew HTTP process; Ctrl+C stops the app. Ollama stays available for later sessions.
#>
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8765,
    [string]$Database = '',
    [switch]$SkipAI
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $taskRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install requirements.txt first; see README.md.'
}
if (-not $Database) { $Database = Join-Path $taskRoot 'data/smartbrew.sqlite3' }

if (-not $SkipAI) {
    try {
        # Ordinary startup uses installed weights and skips warm-up so the website can become ready promptly.
        & (Join-Path $PSScriptRoot 'start_local_ai.ps1') -NoDownload -SkipWarmup
    } catch {
        Write-Warning ('Optional drink assistant is not ready: ' + $_.Exception.Message)
        Write-Output 'Starting SmartBrew; manual ordering remains available.'
    }
}

Write-Output ('Starting SmartBrew at http://127.0.0.1:' + $Port + '/. Press Ctrl+C to stop the app.')
# Direct argument passing preserves paths containing spaces; the existing database is used unless overridden.
& $pythonPath (Join-Path $taskRoot 'app.py') --port $Port --database $Database
if ($LASTEXITCODE -ne 0) { throw ('SmartBrew exited with code ' + $LASTEXITCODE + '.') }
