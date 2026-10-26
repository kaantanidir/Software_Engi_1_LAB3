<#
Purpose: start a local Ollama process and prepare the optional drink model.
Inputs: installed Ollama or the verified portable runtime in data/local-ai/runtime; NoDownload and SkipWarmup switches.
Outputs: running loopback model server and available qwen3:4b, optionally downloaded/warmed; no Windows service or global PATH change.
#>
param(
    [switch]$NoDownload,
    [switch]$SkipWarmup
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$portable = Join-Path $root 'data/local-ai/runtime/ollama.exe'
$installed = Get-Command ollama -ErrorAction SilentlyContinue
if (Test-Path -LiteralPath $portable) { $executable = $portable }
elseif ($installed) { $executable = $installed.Source }
else { throw 'Install Ollama first: https://docs.ollama.com/windows' }

$folder = Join-Path $root 'data/local-ai'
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
$running = $false
try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 2; $running = $true } catch { }
if (-not $running) {
    if ($executable -eq $portable) {
        $models = Join-Path $folder 'models'
        New-Item -ItemType Directory -Force -Path $models | Out-Null
        $env:OLLAMA_MODELS = $models
    }
    Start-Process -FilePath $executable -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $folder 'server.out.log') -RedirectStandardError (Join-Path $folder 'server.err.log') | Out-Null
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 1; $running = $true; break } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $running) { throw 'Ollama did not start. Inspect data/local-ai/server.err.log.' }
}
$available = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5
$modelPresent = @($available.models | Where-Object { $_.name -eq 'qwen3:4b' -or $_.model -eq 'qwen3:4b' }).Count -gt 0
if (-not $modelPresent) {
    if ($NoDownload) { throw 'qwen3:4b is not installed. Run tools/start_local_ai.ps1 once to download it, then start SmartBrew again.' }
    & $executable pull qwen3:4b
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
}
if (-not $SkipWarmup) {
    & $executable run qwen3:4b 'Reply READY'
    if ($LASTEXITCODE -ne 0) { throw 'Model warm-up failed.' }
}
Write-Output 'Local drink assistant available at http://127.0.0.1:11434 (qwen3:4b).'
