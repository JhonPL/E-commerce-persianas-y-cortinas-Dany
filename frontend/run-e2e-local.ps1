param(
    [string[]]$TestFiles = @()
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repositoryRoot "backend\venv\Scripts\python.exe"
$playwrightCli = Join-Path $PSScriptRoot "node_modules\@playwright\test\cli.js"
$configDirectory = Join-Path $env:LOCALAPPDATA "CortinasPersianas\config"
$runId = [Guid]::NewGuid().ToString("N")
$emailPrefix = "e2e.$runId."
$adminEmail = "${emailPrefix}admin@example.test"
$adminPassword = "E2E-$runId-Admin!"
$adminCreated = $false
$testExitCode = 1
$cleanupErrors = @()

$env:E2E_RUN_ID = $runId
$env:E2E_EMAIL_PREFIX = $emailPrefix
$env:E2E_ADMIN_EMAIL = $adminEmail
$env:E2E_ADMIN_PASSWORD = $adminPassword

function Import-ServiceConfig([string]$Name) {
    $path = Join-Path $configDirectory "$Name.json"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "No existe la configuración local protegida para '$Name'."
    }
    $config = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    foreach ($property in $config.PSObject.Properties) {
        if ($null -eq $property.Value) { continue }
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
}

function Invoke-ServiceShell([string]$Service, [string]$ConfigName, [string]$Settings, [string]$Code) {
    Import-ServiceConfig $ConfigName
    $env:DJANGO_SETTINGS_MODULE = $Settings
    Push-Location (Join-Path $repositoryRoot "services\$Service")
    try {
        $output = & $pythonPath manage.py shell -v 0 -c $Code
        if ($LASTEXITCODE -ne 0) {
            throw "La operación local de limpieza/preparación falló en '$Service'."
        }
        return $output
    }
    finally {
        Pop-Location
    }
}

function Invoke-CleanupStep([string]$Name, [scriptblock]$Action) {
    try {
        & $Action
    }
    catch {
        $script:cleanupErrors += "${Name}: $($_.Exception.Message)"
    }
}

try {
    if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
        throw "No se encontró el entorno Python del proyecto."
    }
    if (-not (Test-Path -LiteralPath $playwrightCli -PathType Leaf)) {
        throw "No se encontró @playwright/test; instala las dependencias del frontend."
    }

    $env:E2E_TEMP_ADMIN_EMAIL = $adminEmail
    $env:E2E_TEMP_ADMIN_PASSWORD = $adminPassword
    $createAdmin = @'
import os
from usuarios.models import Rol, Usuario
email = os.environ["E2E_TEMP_ADMIN_EMAIL"]
if Usuario.objects.filter(email=email).exists():
    raise RuntimeError("Temporary E2E admin already exists.")
Usuario.objects.create_user(
    email=email,
    nombre="Administrador E2E temporal",
    password=os.environ["E2E_TEMP_ADMIN_PASSWORD"],
    rol=Rol.objects.get(nombre=Rol.ADMIN),
)
print("Temporary administrator ready.")
'@
    Invoke-ServiceShell "identity" "identity" "auth_service.settings" $createAdmin | Out-Host
    $adminCreated = $true

    Set-Location -LiteralPath $PSScriptRoot
    $playwrightArguments = @("test") + $TestFiles
    & node $playwrightCli @playwrightArguments
    $testExitCode = $LASTEXITCODE
}
catch {
    Write-Error $_
    $testExitCode = 1
}
finally {
    $env:E2E_USER_IDS = ""
    $env:E2E_ORDER_IDS = ""
    try {
        $userIdsCode = @'
import os
from usuarios.models import Usuario
prefix = os.environ["E2E_EMAIL_PREFIX"]
print(",".join(str(value) for value in Usuario.objects.filter(email__startswith=prefix).values_list("usuario_id", flat=True)))
'@
        $userIds = @(Invoke-ServiceShell "identity" "identity" "auth_service.settings" $userIdsCode | Where-Object { $_ -match '^\d+(,\d+)*$' } | Select-Object -Last 1)
        $env:E2E_USER_IDS = if ($userIds.Count) { $userIds[0] } else { "" }
    }
    catch {
        $cleanupErrors += "Buscando usuarios temporales: $($_.Exception.Message)"
    }

    if ($env:E2E_USER_IDS) {
        $cleanupCart = @'
import os
from carrito.models import CarritoItem
ids = [int(value) for value in os.environ["E2E_USER_IDS"].split(",") if value]
CarritoItem.objects.filter(usuario__in=ids).delete()
'@
        Invoke-CleanupStep "Limpiando carritos" {
            Invoke-ServiceShell "cart" "cart" "cart_service.settings" $cleanupCart | Out-Null
        }

        $listOrders = @'
import os
from pedidos.models import Pedido
prefix = os.environ["E2E_EMAIL_PREFIX"]
orders = Pedido.objects.filter(cliente_email__startswith=prefix)
print(",".join(str(value) for value in orders.values_list("pedido_id", flat=True)))
'@
        Invoke-CleanupStep "Buscando pedidos temporales" {
            $orderIds = @(Invoke-ServiceShell "orders" "orders" "orders_service.settings" $listOrders | Where-Object { $_ -match '^\d+(,\d+)*$' } | Select-Object -Last 1)
            $env:E2E_ORDER_IDS = if ($orderIds.Count) { $orderIds[0] } else { "" }
        }
        if ($env:E2E_ORDER_IDS) {
            $cleanupNotifications = @'
import os
from notificaciones.models import NotificacionAdmin
ids = [int(value) for value in os.environ["E2E_ORDER_IDS"].split(",") if value]
NotificacionAdmin.objects.filter(pedido_id__in=ids, evento_id__startswith="pedido:").delete()
'@
            Invoke-CleanupStep "Limpiando notificaciones" {
                Invoke-ServiceShell "notifications" "notifications" "notification_service.settings" $cleanupNotifications | Out-Null
            }
        }
        $cleanupOrders = @'
import os
from pedidos.models import Direccion, Pedido
ids = [int(value) for value in os.environ["E2E_USER_IDS"].split(",") if value]
prefix = os.environ["E2E_EMAIL_PREFIX"]
Pedido.objects.filter(cliente_email__startswith=prefix).delete()
Direccion.objects.filter(usuario__in=ids).delete()
'@
        Invoke-CleanupStep "Limpiando pedidos y direcciones" {
            Invoke-ServiceShell "orders" "orders" "orders_service.settings" $cleanupOrders | Out-Null
        }

        $cleanupPayments = @'
import os
from simulador.models import PaymentAttempt
ids = [int(value) for value in os.environ["E2E_USER_IDS"].split(",") if value]
PaymentAttempt.objects.filter(usuario_id__in=ids).delete()
'@
        Invoke-CleanupStep "Limpiando intentos de pago" {
            Invoke-ServiceShell "payments-simulator" "payments" "payments_service.settings" $cleanupPayments | Out-Null
        }
    }

    if ($adminCreated -or $env:E2E_USER_IDS) {
        $deleteUsers = @'
import os
from usuarios.models import Usuario
Usuario.objects.filter(email__startswith=os.environ["E2E_EMAIL_PREFIX"]).delete()
'@
        Invoke-CleanupStep "Eliminando usuarios temporales" {
            Invoke-ServiceShell "identity" "identity" "auth_service.settings" $deleteUsers | Out-Null
        }
    }
}

if ($cleanupErrors.Count -gt 0) {
    $cleanupErrors | ForEach-Object { Write-Error $_ }
    exit 1
}
exit $testExitCode
