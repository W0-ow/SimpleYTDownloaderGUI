param([int]$AppProcessId, [string]$Installer, [string]$InstallDir)
$ErrorActionPreference = 'Stop'
try {
    $AppProcess = Get-Process -Id $AppProcessId -ErrorAction SilentlyContinue
    if ($AppProcess) { $AppProcess.WaitForExit() }
    $LogPath = Join-Path (Split-Path $Installer) 'installation.log'
    $Arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART',
        '/RESTARTEXITCODE=3010', '/NOCLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS',
        ('/DIR="' + $InstallDir + '"'), ('/LOG="' + $LogPath + '"'))
    $Setup = Start-Process -FilePath $Installer -ArgumentList $Arguments -Wait -PassThru
    if ($Setup.ExitCode -ne 0) {
        throw "No se pudo completar la actualización (código $($Setup.ExitCode)). Registro: $LogPath"
    }
    Start-Process -FilePath (Join-Path $InstallDir 'SuperYTDownloader.exe')
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Super YT Downloader') | Out-Null
}
