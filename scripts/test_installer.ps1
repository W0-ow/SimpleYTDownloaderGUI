$ErrorActionPreference = 'Stop'
$InstallDir = Join-Path $env:RUNNER_TEMP 'SuperYT installer test'
$Setup = (Resolve-Path 'dist\SuperYTDownloader-Setup.exe').Path
$Arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', ('/DIR="' + $InstallDir + '"'))
# Install twice to exercise the same in-place replacement used for updates.
foreach ($Pass in 1..2) {
    $Process = Start-Process -FilePath $Setup -ArgumentList $Arguments -Wait -PassThru
    if ($Process.ExitCode -ne 0) { throw "Installer failed on pass $Pass : $($Process.ExitCode)" }
    foreach ($File in @('SuperYTDownloader.exe', 'installed.txt', '_internal\superyt\assets\apply_update.ps1')) {
        if (-not (Test-Path (Join-Path $InstallDir $File))) { throw "Missing installed file: $File" }
    }
}
$App = Start-Process -FilePath (Join-Path $InstallDir 'SuperYTDownloader.exe') -PassThru
try {
    Start-Sleep -Seconds 8
    if ($App.HasExited) { throw "Installed app exited early: $($App.ExitCode)" }
} finally {
    if (-not $App.HasExited) { Stop-Process -Id $App.Id -Force }
}
$Uninstall = Start-Process -FilePath (Join-Path $InstallDir 'unins000.exe') -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait -PassThru
if ($Uninstall.ExitCode -ne 0) { throw 'Uninstall failed' }
