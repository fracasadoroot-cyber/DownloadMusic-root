### Fracasadoroot
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Args
)

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $here ".venv\Scripts\python.exe"

if (!(Test-Path $venvPython)) {
  Write-Host "No encuentro .venv. Crea el entorno e instala deps:" -ForegroundColor Yellow
  Write-Host "  py -m venv .venv"
  Write-Host "  .\.venv\Scripts\Activate.ps1"
  Write-Host "  pip install -r requirements.txt"
  exit 2
}

& $venvPython (Join-Path $here "ytmusic_dl.py") @Args
exit $LASTEXITCODE

