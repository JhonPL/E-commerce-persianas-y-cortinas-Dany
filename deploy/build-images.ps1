param(
    [string]$ImagePrefix = "cortinas",
    [string]$Tag = "demo"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$dockerfile = Join-Path $PSScriptRoot "Dockerfile"
$billingDockerfile = Join-Path $PSScriptRoot "Dockerfile.billing"

$services = @(
    @{ Name = "gateway"; Path = "gateway"; Wsgi = "gateway.wsgi:application" }
    @{ Name = "identity"; Path = "services/identity"; Wsgi = "auth_service.wsgi:application" }
    @{ Name = "catalog"; Path = "services/catalog"; Wsgi = "catalog_service.wsgi:application" }
    @{ Name = "cart"; Path = "services/cart"; Wsgi = "cart_service.wsgi:application" }
    @{ Name = "orders"; Path = "services/orders"; Wsgi = "orders_service.wsgi:application" }
    @{ Name = "notifications"; Path = "services/notifications"; Wsgi = "notification_service.wsgi:application" }
    @{ Name = "billing"; Path = "services/billing"; Wsgi = "billing_service.wsgi:application"; Billing = $true }
    @{ Name = "payments-simulator"; Path = "services/payments-simulator"; Wsgi = "payments_service.wsgi:application" }
)

foreach ($service in $services) {
    $image = "$ImagePrefix/$($service.Name):$Tag"
    $selectedDockerfile = if ($service.Billing) { $billingDockerfile } else { $dockerfile }
    Write-Host "Building $image"

    & docker build `
        --file $selectedDockerfile `
        --build-arg "SERVICE_PATH=$($service.Path)" `
        --build-arg "WSGI_MODULE=$($service.Wsgi)" `
        --tag $image `
        $repositoryRoot

    if ($LASTEXITCODE -ne 0) {
        throw "La construcción de la imagen '$image' falló."
    }
}

Write-Host "Las ocho imágenes se construyeron correctamente."
