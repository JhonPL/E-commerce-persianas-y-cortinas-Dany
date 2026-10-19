$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$serviceName = "payments_simulator_service"
$databaseName = "cortinas_payments_simulator"
$configDirectory = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config"
$paymentsConfigPath = Join-Path $configDirectory "payments.json"
$backendConfigPath = Join-Path $configDirectory "backend.json"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path $backendConfigPath)) {
    throw "No existe la configuración protegida del backend: $backendConfigPath"
}

$backendConfig = Get-Content $backendConfigPath -Raw | ConvertFrom-Json
$ordersConfigPath = Join-Path $configDirectory "orders.json"
if (-not (Test-Path $ordersConfigPath)) {
    throw "No existe la configuración protegida de pedidos: $ordersConfigPath"
}
$ordersConfig = Get-Content $ordersConfigPath -Raw | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($backendConfig.INTERNAL_SERVICE_TOKEN)) {
    throw "La configuración del backend no contiene el token interno compartido."
}

$psqlPath = $null
$postgresRoot = "C:\Program Files\PostgreSQL"
if (Test-Path $postgresRoot) {
    $psqlPath = Get-ChildItem $postgresRoot -Directory |
        Where-Object { $_.Name -match '^\d+(\.\d+)*$' } |
        Sort-Object { [int]$_.Name.Split(".")[0] } -Descending |
        ForEach-Object {
            $candidate = Join-Path $_.FullName "bin\psql.exe"
            if (Test-Path $candidate) { return $candidate }
        } |
        Select-Object -First 1
}
if (-not $psqlPath) {
    $psqlCommand = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($psqlCommand) { $psqlPath = $psqlCommand.Source }
}
if (-not $psqlPath) {
    throw "No se encontró psql.exe. Instala PostgreSQL o agrega su carpeta bin al PATH."
}

$hostName = [string]$ordersConfig.ORDERS_DB_HOST
$port = [string]$ordersConfig.ORDERS_DB_PORT
$adminUser = Read-Host "Usuario administrador PostgreSQL [postgres]"
if ([string]::IsNullOrWhiteSpace($adminUser)) { $adminUser = "postgres" }
$adminPassword = Read-Host "Contraseña del administrador PostgreSQL" -AsSecureString
$adminPasswordPointer = [IntPtr]::Zero
$adminPasswordPlain = $null
$originalPgPassword = $env:PGPASSWORD
$script:servicePassword = ""
$originalServiceEnvironment = @{}

function New-RandomHex([int]$ByteCount) {
    $bytes = New-Object byte[] $ByteCount
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $random.GetBytes($bytes)
        return -join ($bytes | ForEach-Object { $_.ToString("x2") })
    }
    finally {
        [Array]::Clear($bytes, 0, $bytes.Length)
        $random.Dispose()
    }
}

function Invoke-Psql([string[]]$Arguments, [string]$Sql = $null) {
    if ($null -eq $Sql) {
        $output = & $script:psqlPath @Arguments 2>&1
    }
    else {
        $output = $Sql | & $script:psqlPath @Arguments 2>&1
    }
    if ($LASTEXITCODE -ne 0) {
        $safeOutput = ($output -join "`n").Replace($script:servicePassword, "[redacted]")
        throw "Falló una operación de PostgreSQL. Revisa el acceso administrativo y los permisos. $safeOutput"
    }
    return ($output -join "`n").Trim()
}

function Set-ServiceEnvironment($Configuration) {
    foreach ($property in $Configuration.PSObject.Properties) {
        if (-not $script:originalServiceEnvironment.ContainsKey($property.Name)) {
            $script:originalServiceEnvironment[$property.Name] =
                [Environment]::GetEnvironmentVariable($property.Name, "Process")
        }
        if ($property.Value -is [System.Array]) {
            $value = $property.Value -join ","
        }
        else {
            $value = [string]$property.Value
        }
        [Environment]::SetEnvironmentVariable($property.Name, $value, "Process")
    }
}

try {
    $adminPasswordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR(
        $adminPassword
    )
    $adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR(
        $adminPasswordPointer
    )
    $env:PGPASSWORD = $adminPasswordPlain

    $connectionArguments = @(
        "-X", "-w", "-t", "-A", "-h", $hostName, "-p", $port, "-U", $adminUser,
        "-d", "postgres", "-v", "ON_ERROR_STOP=1"
    )
    Invoke-Psql $connectionArguments "SELECT 1;" | Out-Null

    $existingConfig = $null
    if (Test-Path $paymentsConfigPath) {
        $existingConfig = Get-Content $paymentsConfigPath -Raw | ConvertFrom-Json
        if (
            $existingConfig.PAYMENTS_DB_NAME -ne $databaseName -or
            $existingConfig.PAYMENTS_DB_USER -ne $serviceName
        ) {
            throw "La configuración payments.json existe con otra base o rol; no se modificó."
        }
        $script:servicePassword = [string]$existingConfig.PAYMENTS_DB_PASSWORD
        $djangoSecret = [string]$existingConfig.DJANGO_SECRET_KEY
    }
    else {
        $roleExists = Invoke-Psql $connectionArguments `
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$serviceName');"
        if ($roleExists -eq "t") {
            throw "El rol de pagos ya existe sin configuración local protegida; revisa el estado antes de continuar."
        }
        $script:servicePassword = New-RandomHex 32
        $djangoSecret = New-RandomHex 64
    }
    if (
        [string]::IsNullOrWhiteSpace($script:servicePassword) -or
        [string]::IsNullOrWhiteSpace($djangoSecret)
    ) {
        throw "payments.json no contiene las claves necesarias para el servicio."
    }

    $databaseOwner = Invoke-Psql $connectionArguments `
        "SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = '$databaseName';"
    if ($databaseOwner -and $databaseOwner -ne $serviceName) {
        throw "La base $databaseName ya existe con otro propietario; no se alteró."
    }

    New-Item -ItemType Directory -Path $configDirectory -Force | Out-Null
    $paymentsConfig = [ordered]@{
        DJANGO_SECRET_KEY = $djangoSecret
        DJANGO_DEBUG = $true
        DJANGO_ALLOWED_HOSTS = @("localhost", "127.0.0.1")
        PAYMENTS_DB_NAME = $databaseName
        PAYMENTS_DB_USER = $serviceName
        PAYMENTS_DB_PASSWORD = $script:servicePassword
        PAYMENTS_DB_HOST = $hostName
        PAYMENTS_DB_PORT = $port
        INTERNAL_SERVICE_TOKEN = [string]$backendConfig.INTERNAL_SERVICE_TOKEN
        AUTH_SERVICE_URL = ([string]$backendConfig.IDENTITY_SERVICE_URL).TrimEnd("/") + "/api/v1/auth/me/"
        ORDERS_SERVICE_URL = [string]$backendConfig.ORDERS_SERVICE_URL
        SERVICE_TIMEOUT_SECONDS = 5
        PAYMENT_SIMULATOR_ENABLED = $true
    }
    $paymentsConfig |
        ConvertTo-Json -Depth 5 |
        Set-Content -Path $paymentsConfigPath -Encoding utf8

    $roleExists = Invoke-Psql $connectionArguments `
        "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$serviceName');"
    $roleSql = if ($roleExists -eq "t") {
        "ALTER ROLE $serviceName WITH LOGIN PASSWORD '$script:servicePassword';"
    }
    else {
        "CREATE ROLE $serviceName WITH LOGIN PASSWORD '$script:servicePassword';"
    }
    Invoke-Psql $connectionArguments $roleSql | Out-Null

    if (-not $databaseOwner) {
        Invoke-Psql $connectionArguments `
            "CREATE DATABASE $databaseName OWNER $serviceName ENCODING 'UTF8';" |
            Out-Null
    }

    if ($null -eq $originalPgPassword) {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    else {
        $env:PGPASSWORD = $originalPgPassword
    }

    $backendConfig | Add-Member -NotePropertyName PAYMENTS_SERVICE_URL `
        -NotePropertyValue "http://127.0.0.1:8007/api/v1/payments" -Force
    $backendConfig | Add-Member -NotePropertyName PAYMENTS_SERVICE_TIMEOUT_SECONDS `
        -NotePropertyValue 10 -Force
    $backendConfig |
        ConvertTo-Json -Depth 8 |
        Set-Content -Path $backendConfigPath -Encoding utf8

    $python = Join-Path $repoRoot "backend\venv\Scripts\python.exe"
    if (-not (Test-Path $python)) {
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        if (-not $pythonCommand) {
            throw "No se encontró Python; configura el entorno antes de ejecutar migraciones."
        }
        $python = $pythonCommand.Source
    }

    if (-not $ordersConfig.PSObject.Properties["CART_SERVICE_URL"]) {
            $ordersConfig | Add-Member -NotePropertyName CART_SERVICE_URL `
                -NotePropertyValue "http://127.0.0.1:8002/api/v1/carrito"
            $ordersConfig |
                ConvertTo-Json -Depth 8 |
                Set-Content -Path $ordersConfigPath -Encoding utf8
    }
    Set-ServiceEnvironment $ordersConfig
    Push-Location (Join-Path $repoRoot "services\orders")
    try {
            & $python manage.py migrate --noinput
            if ($LASTEXITCODE -ne 0) {
                throw "Fallaron las migraciones del servicio de pedidos."
            }
    }
    finally {
            Pop-Location
    }

    $serviceEnvironment = Get-Content $paymentsConfigPath -Raw | ConvertFrom-Json
    Set-ServiceEnvironment $serviceEnvironment

    Push-Location $PSScriptRoot
    try {
        & $python manage.py migrate --noinput
        if ($LASTEXITCODE -ne 0) {
            throw "Fallaron las migraciones del servicio de pagos."
        }
    }
    finally {
        Pop-Location
    }

    Write-Host "Base y rol del simulador preparados; migraciones de pedidos y pagos aplicadas."
    Write-Host "Configuración guardada fuera del repositorio en $paymentsConfigPath"
    Write-Host "El backend apunta al simulador local en el puerto 8007."
}
finally {
    if ($adminPasswordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($adminPasswordPointer)
    }
    $adminPasswordPlain = $null
    $adminPassword = $null
    if ($null -eq $originalPgPassword) {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    else {
        $env:PGPASSWORD = $originalPgPassword
    }
    foreach ($key in $originalServiceEnvironment.Keys) {
        $originalValue = $originalServiceEnvironment[$key]
        if ($null -eq $originalValue) {
            Remove-Item "Env:$key" -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($key, $originalValue, "Process")
        }
    }
    $script:servicePassword = $null
    $djangoSecret = $null
}
