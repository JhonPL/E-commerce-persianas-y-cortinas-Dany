param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "identity",
        "catalog",
        "cart",
        "orders",
        "notifications",
        "billing",
        "payments-simulator"
    )]
    [string]$Service,
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$serviceDirectory = Join-Path $PSScriptRoot $Service
$configName = if ($Service -eq "payments-simulator") { "payments" } else { $Service }
$configPath = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config\$configName.json"
$pythonPath = Join-Path $repositoryRoot "backend\venv\Scripts\python.exe"
$portMap = @{
    identity = 8004
    catalog = 8001
    cart = 8002
    orders = 8003
    notifications = 8005
    billing = 8006
    "payments-simulator" = 8007
}

if (-not (Test-Path -LiteralPath $serviceDirectory -PathType Container)) {
    throw "No existe el directorio del servicio '$Service'."
}
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "No existe la configuración local protegida para '$Service'."
}
if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "No se encontró el entorno Python del proyecto."
}

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$requiredKeys = @(
    "DJANGO_SECRET_KEY",
    "DJANGO_DEBUG",
    "DJANGO_ALLOWED_HOSTS"
)
foreach ($key in $requiredKeys) {
    if (-not $config.PSObject.Properties[$key] -or -not $config.$key) {
        throw "La configuración protegida de '$Service' no contiene '$key'."
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

if ($Port -le 0) {
    $Port = $portMap[$Service]
}

Set-Location -LiteralPath $serviceDirectory
& $pythonPath manage.py runserver "127.0.0.1:$Port" --noreload
exit $LASTEXITCODE
