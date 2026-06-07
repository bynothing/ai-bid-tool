param(
    [string] $Version = 'latest'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$downloadsDir = Join-Path $repoRoot '.tools\downloads'
$targetDir = Join-Path $repoRoot '.tools\drawio-msi'
New-Item -ItemType Directory -Force -Path $downloadsDir, $targetDir | Out-Null

$headers = @{ 'User-Agent' = 'bid-tool-drawio-installer' }
$releaseUri = if ($Version -eq 'latest') {
    'https://api.github.com/repos/jgraph/drawio-desktop/releases/latest'
} else {
    "https://api.github.com/repos/jgraph/drawio-desktop/releases/tags/$Version"
}

$release = Invoke-RestMethod -Headers $headers -Uri $releaseUri
$asset = $release.assets | Where-Object { $_.name -like 'draw.io-*.msi' } | Select-Object -First 1
if (-not $asset) {
    throw "No Windows MSI asset found in release $($release.tag_name)."
}

$msiPath = Join-Path $downloadsDir $asset.name
if (-not (Test-Path -LiteralPath $msiPath)) {
    Write-Host "Downloading $($asset.name) from GitHub..."
    Invoke-WebRequest -Headers $headers -Uri $asset.browser_download_url -OutFile $msiPath
}

if ($asset.digest -and $asset.digest.StartsWith('sha256:')) {
    $expectedHash = $asset.digest.Substring('sha256:'.Length).ToLowerInvariant()
    $actualHash = (Get-FileHash -Algorithm SHA256 -Path $msiPath).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "SHA256 mismatch for $($asset.name): $actualHash != $expectedHash"
    }
}

$logPath = Join-Path $downloadsDir 'drawio-msi-extract.log'
$process = Start-Process -FilePath 'msiexec.exe' `
    -ArgumentList @('/a', $msiPath, '/qn', "TARGETDIR=$targetDir", '/L*v', $logPath) `
    -Wait `
    -PassThru `
    -WindowStyle Hidden

if ($process.ExitCode -ne 0) {
    throw "MSI extraction failed with exit code $($process.ExitCode). See $logPath"
}

$exe = Get-ChildItem -Path $targetDir -Recurse -Filter 'draw.io.exe' | Select-Object -First 1
if (-not $exe) {
    throw "MSI extraction completed but draw.io.exe was not found."
}

Write-Host "Draw.io $($release.tag_name) is ready:"
Write-Host "  $($exe.FullName)"
