param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $DrawioArgs
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$candidates = @()

if ($env:DRAWIO_EXE) {
    $candidates += $env:DRAWIO_EXE
}

$candidates += @(
    (Join-Path $repoRoot '.tools\drawio-msi\draw.io\draw.io.exe'),
    (Join-Path $repoRoot '.tools\drawio\draw.io.exe')
)

$pathCommand = Get-Command 'draw.io.exe' -ErrorAction SilentlyContinue
if ($pathCommand) {
    $candidates += $pathCommand.Source
}

$drawioExe = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $drawioExe) {
    throw "Draw.io executable not found. Run tools\install-drawio.ps1 first, or set DRAWIO_EXE."
}

if (-not $DrawioArgs -or $DrawioArgs.Count -eq 0) {
    @"
Draw.io wrapper for bid-tool.

Examples:
  .\tools\drawio.ps1 --export --format png --output output\diagram.png input\diagram.drawio
  .\tools\drawio.ps1 -x -f svg -o output\diagram.svg input\diagram.drawio
  .\tools\drawio.ps1 input\diagram.drawio

Executable:
  $drawioExe
"@ | Write-Host
    exit 0
}

$outputPath = $null
for ($i = 0; $i -lt $DrawioArgs.Count; $i++) {
    if (($DrawioArgs[$i] -eq '--output' -or $DrawioArgs[$i] -eq '-o') -and ($i + 1) -lt $DrawioArgs.Count) {
        $outputPath = $DrawioArgs[$i + 1]
    }
}

if ($outputPath) {
    if (-not [System.IO.Path]::IsPathRooted($outputPath)) {
        $outputPath = Join-Path (Get-Location) $outputPath
    }

    $outputDir = Split-Path -Parent $outputPath
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
}

& $drawioExe @DrawioArgs
$exitCode = $LASTEXITCODE

if ($outputPath) {
    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        $outputItem = Get-Item -LiteralPath $outputPath -ErrorAction SilentlyContinue
        if ($outputItem -and $outputItem.Length -gt 0) {
            break
        }
        Start-Sleep -Milliseconds 250
    }
}

exit $exitCode
