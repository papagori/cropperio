$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$setupPath = Join-Path $projectRoot 'dist\Cropperio_Setup.exe'
$installTarget = Join-Path $env:TEMP "Cropperio-distribution-test-$PID"
$reportPath = Join-Path $projectRoot 'test-results\installer-smoke.json'

if (-not (Test-Path -LiteralPath $setupPath)) {
    throw "Installer not found: $setupPath"
}
if (Test-Path -LiteralPath $installTarget) {
    throw "Refusing to overwrite existing test target: $installTarget"
}

$install = Start-Process -FilePath $setupPath -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', '/NOICONS',
    "/DIR=$installTarget"
) -WindowStyle Hidden -PassThru -Wait
if ($install.ExitCode -ne 0) {
    throw "Installer exited with code $($install.ExitCode)"
}

$installedExe = Join-Path $installTarget 'Cropperio.exe'
$uninstaller = Join-Path $installTarget 'unins000.exe'
if (-not (Test-Path -LiteralPath $installedExe) -or
    -not (Test-Path -LiteralPath $uninstaller)) {
    throw 'Installed application or uninstaller is missing'
}

$previousPath = $env:PATH
try {
    # Prove that developer Python/codec directories on PATH are not required.
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    $startupPath = Join-Path $projectRoot 'test-results\startup-installed.json'
    $startup = Start-Process -FilePath $installedExe -ArgumentList @(
        '--startup-test', $startupPath
    ) -WindowStyle Hidden -PassThru -Wait
    if ($startup.ExitCode -ne 0) { throw 'Installed splash/startup test failed' }
    $startupReport = Get-Content -LiteralPath $startupPath -Raw | ConvertFrom-Json
    if (-not $startupReport.passed -or -not $startupReport.frozen -or -not $startupReport.splash_closed) {
        throw 'Installed splash did not close when the application became ready'
    }
    $application = Start-Process -FilePath $installedExe -ArgumentList @(
        '--self-test', $reportPath
    ) -WindowStyle Hidden -PassThru -Wait
} finally {
    $env:PATH = $previousPath
}
if ($application.ExitCode -ne 0) {
    throw "Installed application self-test exited with code $($application.ExitCode)"
}
$report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if (-not $report.passed -or -not $report.frozen -or
    $report.runtime.external_python_required) {
    throw 'Installed application did not pass the frozen runtime checks'
}
$checkedInputs = @($report.input_validation.files | ForEach-Object { $_.file })
foreach ($requiredInput in @('oriented.heic', 'primary-second.heif', 'sequence.avif')) {
    if ($checkedInputs -notcontains $requiredInput) {
        throw "Installed application did not process required input: $requiredInput"
    }
}
if (-not $report.native_avif -or -not $report.input_validation.raw_ignored -or
    $report.input_validation.windows_codec_required) {
    throw 'Installed image codec or RAW exclusion checks failed'
}
if ($report.version -ne (Get-Item -LiteralPath $installedExe).VersionInfo.ProductVersion) {
    throw 'Installed executable version and application version differ'
}
if (@($report.custom_validation).Count -ne 4 -or
    @($report.custom_validation | Where-Object { $_.processed -ne 14 -or $_.errors -ne 0 }).Count) {
    throw 'Installed Custom width/height processing did not pass'
}

$uninstall = Start-Process -FilePath $uninstaller -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'
) -WindowStyle Hidden -PassThru -Wait
if ($uninstall.ExitCode -ne 0) {
    throw "Uninstaller exited with code $($uninstall.ExitCode)"
}
Start-Sleep -Seconds 2
if (Test-Path -LiteralPath $installTarget) {
    throw "Uninstaller left the installation directory behind: $installTarget"
}

Write-Host 'Installer distribution test passed.'
