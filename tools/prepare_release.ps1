param(
    [string]$DistDirectory = 'dist',
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $releaseJson = & $python -m cropper.release_artifacts names
    if ($LASTEXITCODE -ne 0) { throw 'Could not resolve distribution names' }
    $release = $releaseJson | ConvertFrom-Json
    $versions = @{}
    foreach ($name in @($release.standalone, $release.installer)) {
        $path = Join-Path $DistDirectory $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing release binary: $path" }
        $version = (Get-Item -LiteralPath $path).VersionInfo.ProductVersion.Trim()
        if ($version -ne $release.version) { throw "Product version mismatch: $name ($version)" }
        $versions[$name] = $version
    }
    if ($ValidateOnly) {
        $releaseJson
        return
    }
    $gitRoot = $projectRoot.Replace('\', '/')
    $commit = & git -c "safe.directory=$gitRoot" rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Could not determine source commit' }
    ($versions | ConvertTo-Json -Compress) | & $python -m cropper.release_artifacts manifest --directory $DistDirectory --commit $commit
    if ($LASTEXITCODE -ne 0) { throw 'Release manifest generation failed' }
} finally {
    Pop-Location
}
