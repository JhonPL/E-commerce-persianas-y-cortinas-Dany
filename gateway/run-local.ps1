param(
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config\gateway.json"
$pythonPath = Join-Path $repositoryRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "No existe la configuración local protegida del gateway."
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "No se encontró .venv en la raíz del proyecto."
}

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$requiredKeys = @(
    "INTERNAL_SERVICE_TOKEN",
    "IDENTITY_SERVICE_URL",
    "CATALOGO_SERVICE_URL",
    "CART_SERVICE_URL",
    "ORDERS_SERVICE_URL",
    "PAYMENTS_SERVICE_URL"
)
foreach ($key in $requiredKeys) {
    if (-not $config.PSObject.Properties[$key] -or -not $config.$key) {
        throw "La configuración protegida del gateway no contiene '$key'."
    }
}

foreach ($property in $config.PSObject.Properties) {
    if ($null -eq $property.Value) {
        continue
    }
    if ($property.Value -is [System.Array]) {
        $value = $property.Value -join ","
    }
    elseif ($property.Value -is [bool]) {
        $value = $property.Value.ToString().ToLowerInvariant()
    }
    else {
        $value = [string]$property.Value
    }
    [Environment]::SetEnvironmentVariable($property.Name, $value, "Process")
}

if (-not $env:DJANGO_SECRET_KEY) {
    $bytes = [byte[]]::new(48)
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $random.GetBytes($bytes)
    }
    finally {
        $random.Dispose()
    }
    $env:DJANGO_SECRET_KEY = [Convert]::ToBase64String($bytes)
}
if (-not $env:DJANGO_DEBUG) {
    $env:DJANGO_DEBUG = "false"
}
if (-not $env:DJANGO_ALLOWED_HOSTS) {
    $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
}
$env:DJANGO_SETTINGS_MODULE = "gateway.settings"

Set-Location -LiteralPath $PSScriptRoot
& $pythonPath manage.py runserver "127.0.0.1:$Port" --noreload
exit $LASTEXITCODE
