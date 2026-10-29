param(
    [Parameter(Mandatory = $true)]
    [uri]$FrontendUrl,
    [Parameter(Mandatory = $true)]
    [uri]$GatewayUrl,
    [Parameter(Mandatory = $true)]
    [uri]$IdentityUrl,
    [Parameter(Mandatory = $true)]
    [uri]$CatalogUrl,
    [Parameter(Mandatory = $true)]
    [uri]$CartUrl,
    [Parameter(Mandatory = $true)]
    [uri]$OrdersUrl,
    [Parameter(Mandatory = $true)]
    [uri]$NotificationsUrl,
    [Parameter(Mandatory = $true)]
    [uri]$BillingUrl,
    [Parameter(Mandatory = $true)]
    [uri]$PaymentsUrl,
    [ValidateRange(60, 900)]
    [int]$TimeoutSeconds = 600,
    [ValidateRange(2, 60)]
    [int]$RetryIntervalSeconds = 5
)

$ErrorActionPreference = "Stop"

$targets = @(
    [pscustomobject]@{ Name = "frontend"; Url = $FrontendUrl.AbsoluteUri }
    [pscustomobject]@{ Name = "gateway"; Url = "$($GatewayUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "identity"; Url = "$($IdentityUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "catalog"; Url = "$($CatalogUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "cart"; Url = "$($CartUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "orders"; Url = "$($OrdersUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "notifications"; Url = "$($NotificationsUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "billing"; Url = "$($BillingUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
    [pscustomobject]@{ Name = "payments-simulator"; Url = "$($PaymentsUrl.AbsoluteUri.TrimEnd('/'))/health/ready/" }
)

foreach ($target in $targets) {
    $uri = [uri]$target.Url
    if (-not $uri.IsAbsoluteUri -or $uri.Scheme -ne "https") {
        throw "La URL de '$($target.Name)' debe ser HTTPS."
    }
}

$jobs = foreach ($target in $targets) {
    Start-Job -Name "warm-$($target.Name)" -ArgumentList @(
        $target.Name,
        $target.Url,
        $TimeoutSeconds,
        $RetryIntervalSeconds
    ) -ScriptBlock {
        param($name, $url, $timeoutSeconds, $retryIntervalSeconds)

        $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
        $lastStatus = "Sin respuesta"
        $delaySeconds = $retryIntervalSeconds
        while ([DateTime]::UtcNow -lt $deadline) {
            try {
                $response = Invoke-WebRequest `
                    -Uri $url `
                    -Method Get `
                    -TimeoutSec 30 `
                    -UseBasicParsing
                if ($response.StatusCode -eq 200) {
                    return [pscustomobject]@{
                        Name   = $name
                        Status = "READY"
                        Detail = "HTTP 200"
                    }
                }
                $lastStatus = "HTTP $($response.StatusCode)"
            }
            catch {
                $statusCode = $_.Exception.Response.StatusCode.value__
                if ($statusCode) {
                    $lastStatus = "HTTP $statusCode"
                }
                else {
                    $lastStatus = $_.Exception.Message
                }
            }

            Start-Sleep -Seconds $delaySeconds
            $delaySeconds = [Math]::Min($delaySeconds * 2, 60)
        }

        [pscustomobject]@{
            Name   = $name
            Status = "TIMEOUT"
            Detail = $lastStatus
        }
    }
}

try {
    Wait-Job -Job $jobs -Timeout $TimeoutSeconds | Out-Null
    $results = foreach ($job in $jobs) {
        if ($job.State -eq "Completed") {
            Receive-Job -Job $job
        }
        else {
            [pscustomobject]@{
                Name   = $job.Name -replace "^warm-", ""
                Status = "TIMEOUT"
                Detail = "No respondió dentro de $TimeoutSeconds segundos."
            }
        }
    }

    $results | Sort-Object Name | Format-Table -AutoSize
    if (@($results | Where-Object Status -ne "READY").Count -gt 0) {
        throw "Uno o más componentes no están listos; revisa su estado y los logs antes de la exposición."
    }
}
finally {
    $jobs | Stop-Job -ErrorAction SilentlyContinue
    $jobs | Remove-Job -Force -ErrorAction SilentlyContinue
}
