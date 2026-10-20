$ErrorActionPreference = "Stop"

$repositoryRoot = $PSScriptRoot
$configDirectory = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config"
$pythonPath = Join-Path $repositoryRoot "backend\venv\Scripts\python.exe"
$frontendDirectory = Join-Path $repositoryRoot "frontend"
$servicesScript = Join-Path $repositoryRoot "services\run-local.ps1"
$gatewayScript = Join-Path $repositoryRoot "gateway\run-local.ps1"
$serviceNames = @(
    "identity",
    "catalog",
    "cart",
    "orders",
    "notifications",
    "billing",
    "payments-simulator"
)

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "No se encontró backend\venv. Prepara primero el entorno Python del proyecto."
}
if (-not (Test-Path -LiteralPath (Join-Path $frontendDirectory "node_modules") -PathType Container)) {
    throw "No se encontraron las dependencias del frontend. Ejecuta 'npm ci' en frontend."
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "No se encontró npm. Instala Node.js y vuelve a abrir PowerShell."
}
if (-not (Test-Path -LiteralPath (Join-Path $configDirectory "backend.json") -PathType Leaf)) {
    throw "Falta la configuración protegida del gateway en %LOCALAPPDATA%\CortinasPersianas\config."
}
foreach ($service in $serviceNames) {
    $configName = if ($service -eq "payments-simulator") { "payments" } else { $service }
    $configPath = Join-Path $configDirectory "$configName.json"
    if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
        throw "Falta la configuración protegida de '$service' en %LOCALAPPDATA%\CortinasPersianas\config."
    }
}

$frontendEnvPath = Join-Path $frontendDirectory ".env"
if (-not (Test-Path -LiteralPath $frontendEnvPath -PathType Leaf)) {
    throw "Falta frontend\.env. Configura VITE_API_URL=http://127.0.0.1:8010/api/v1."
}
$apiUrlLine = Get-Content -LiteralPath $frontendEnvPath |
    Where-Object { $_ -match '^\s*VITE_API_URL=' } |
    Select-Object -First 1
if ($apiUrlLine -notmatch '^\s*VITE_API_URL=http://127\.0\.0\.1:8010/api/v1\s*$') {
    throw "Configura VITE_API_URL=http://127.0.0.1:8010/api/v1 en frontend\.env."
}

$powerShell = Get-Command pwsh.exe -ErrorAction SilentlyContinue
if (-not $powerShell) {
    $powerShell = Get-Command powershell.exe -ErrorAction SilentlyContinue
}
if (-not $powerShell) {
    throw "No se encontró PowerShell para abrir las terminales de los servicios."
}

Write-Host "Aplicando migraciones del servicio de pedidos..."
& $powerShell.Source -NoProfile -ExecutionPolicy Bypass `
    -File $servicesScript -Service orders -MigrateOnly
if ($LASTEXITCODE -ne 0) {
    throw "No fue posible aplicar las migraciones del servicio de pedidos."
}

Write-Host "Iniciando servicios y frontend en ventanas separadas..."
foreach ($service in $serviceNames) {
    Start-Process -FilePath $powerShell.Source `
        -WorkingDirectory $repositoryRoot `
        -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-File", "`"$servicesScript`"",
            "-Service", $service
        ) | Out-Null
}

Start-Process -FilePath $powerShell.Source `
    -WorkingDirectory $repositoryRoot `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$servicesScript`"",
        "-Service", "orders",
        "-ExpireUnpaidOrders"
    ) | Out-Null

Start-Process -FilePath $powerShell.Source `
    -WorkingDirectory $repositoryRoot `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$gatewayScript`""
    ) | Out-Null

$quotedFrontendDirectory = $frontendDirectory.Replace("'", "''")
$frontendCommand = "Set-Location -LiteralPath '$quotedFrontendDirectory'; npm run dev -- --host 127.0.0.1"
Start-Process -FilePath $powerShell.Source `
    -WorkingDirectory $frontendDirectory `
    -ArgumentList "-NoExit -Command `"$frontendCommand`"" | Out-Null

Write-Host ""
Write-Host "Arranque solicitado. Abre la tienda en http://localhost:5173"
Write-Host "El gateway/API está en http://127.0.0.1:8010"
Write-Host "El monitor de pagos vencidos está en una ventana adicional de PowerShell."
Write-Host "Deja abiertas las ventanas de PowerShell mientras uses la aplicación."
