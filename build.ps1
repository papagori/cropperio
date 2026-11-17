param([switch]$Plan)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if ($Plan) {
    & .\.venv\Scripts\python.exe -m cropper.release_artifacts names
    if ($LASTEXITCODE -ne 0) { throw 'Could not resolve distribution names' }
    return
}
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment' }
}
& .\.venv\Scripts\python.exe -c "import PIL, PySide6, PyInstaller, pillow_heif; from PIL import features; assert tuple(map(int, PIL.__version__.split('.')[:2])) >= (12, 1); assert PIL.__version__.split('.')[0] == '12'; assert PySide6.__version__ == '6.11.0'; assert PyInstaller.__version__ == '6.20.0'; assert pillow_heif.__version__ == '1.8.1'; assert features.check('avif'); assert pillow_heif.libheif_info()['decoders']"
if ($LASTEXITCODE -ne 0) {
    & .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check --no-input -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
}
& .\.venv\Scripts\python.exe tools\build_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Application icon generation failed' }
$releaseJson = & .\.venv\Scripts\python.exe -m cropper.release_artifacts names
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve distribution names' }
$release = $releaseJson | ConvertFrom-Json
$appVersion = $release.version
$standalonePath = Join-Path $PSScriptRoot (Join-Path 'dist' $release.standalone)
$previousQtPlatform = $env:QT_QPA_PLATFORM
$env:QT_QPA_PLATFORM = 'offscreen'
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
$testExitCode = $LASTEXITCODE
$env:QT_QPA_PLATFORM = $previousQtPlatform
if ($testExitCode -ne 0) { throw 'Tests failed' }
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean Cropperio.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
$startup = Start-Process -FilePath $standalonePath -ArgumentList '--startup-test', 'test-results\startup-frozen.json' -WindowStyle Hidden -PassThru -Wait
if ($startup.ExitCode -ne 0) { throw 'Frozen splash/startup verification failed' }
$startupReport = Get-Content -LiteralPath 'test-results\startup-frozen.json' -Raw | ConvertFrom-Json
if (-not $startupReport.passed -or -not $startupReport.frozen -or -not $startupReport.imports_deferred) { throw 'Frozen startup did not pass' }
$verification = Start-Process -FilePath $standalonePath -ArgumentList '--self-test', 'test-results\compiled-v2.json' -WindowStyle Hidden -PassThru -Wait
if ($verification.ExitCode -ne 0) { throw 'Standalone verification failed; see test-results\compiled-v2.json' }
$report = Get-Content -LiteralPath 'test-results\compiled-v2.json' -Raw | ConvertFrom-Json
if (-not $report.passed -or -not $report.frozen) { throw 'Standalone verification did not pass' }
$innoCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe')
)
$iscc = $innoCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if ($iscc) {
    & $iscc "/DAppVersion=$appVersion" "/DStandaloneFileName=$($release.standalone)" "/DSetupBaseName=$($release.installer_base)" 'installer\Cropperio.iss'
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed' }
    & .\tools\prepare_release.ps1
    Write-Host "Ready: dist\$($release.installer)"
} else {
    Write-Warning 'Inno Setup 6 was not found; installer build skipped.'
}
Write-Host "Ready: dist\$($release.standalone)"
