$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$configPath = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config\payments.json"
if (-not (Test-Path $configPath)) {
    throw "No existe la configuración protegida del simulador. Ejecuta provision-local.ps1 primero."
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
foreach ($property in $config.PSObject.Properties) {
    if ($property.Value -is [System.Array]) {
        $value = $property.Value -join ","
    }
    else {
        $value = [string]$property.Value
    }
    [Environment]::SetEnvironmentVariable($property.Name, $value, "Process")
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "No se encontró Python; configura el entorno virtual antes de iniciar el simulador."
    }
    $python = $pythonCommand.Source
}

Push-Location $PSScriptRoot
try {
    & $python manage.py runserver 127.0.0.1:8007 --noreload
    if ($LASTEXITCODE -ne 0) {
        throw "El simulador de pagos terminó con error."
    }
}
finally {
    Pop-Location
    foreach ($property in $config.PSObject.Properties) {
        Remove-Item "Env:$($property.Name)" -ErrorAction SilentlyContinue
    }
}
