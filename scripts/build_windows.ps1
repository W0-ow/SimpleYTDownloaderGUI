param([switch]$DownloadTools)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PreviousQtPlatform = $env:QT_QPA_PLATFORM
Push-Location $ProjectRoot
try {
    if (-not [Environment]::Is64BitOperatingSystem -or $env:OS -ne 'Windows_NT') {
        throw 'Este script necesita Windows de 64 bits.'
    }
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        & py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.12 de 64 bits con el lanzador py.' }
    }
    $PythonExe = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    & $PythonExe -m pip install -e '.[dev]'
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    if ($DownloadTools) {
        & $PythonExe scripts/setup_tools.py --destination bin
        if ($LASTEXITCODE -ne 0) { throw 'Falló la preparación de herramientas.' }
    }
    & $PythonExe -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw 'Falló la comprobación de código.' }
    $env:QT_QPA_PLATFORM = 'offscreen'
    & $PythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas.' }
    & $PythonExe scripts/make_icon.py
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo generar el icono.' }
    & $PythonExe -m PyInstaller --noconfirm --clean --windowed --onedir `
        --name SuperYTDownloader --paths src --collect-data superyt `
        --icon build/app.ico SuperYT.py
    if ($LASTEXITCODE -ne 0) { throw 'Falló el empaquetado.' }
    if ($DownloadTools) {
        New-Item -ItemType Directory -Path 'dist\SuperYTDownloader\bin' -Force | Out-Null
        foreach ($Tool in @('yt-dlp.exe', 'ffmpeg.exe', 'ffprobe.exe', 'deno.exe', 'tools-manifest.json')) {
            Copy-Item "bin\$Tool" 'dist\SuperYTDownloader\bin' -Force
        }
        Copy-Item 'bin\licenses' 'dist\SuperYTDownloader\bin\licenses' -Recurse -Force
    }
    Copy-Item README.md 'dist\SuperYTDownloader\LEEME.md' -Force
    Copy-Item THIRD_PARTY.md 'dist\SuperYTDownloader\THIRD_PARTY.md' -Force
    & $PythonExe -m pip freeze | Out-File 'dist\SuperYTDownloader\build-dependencies.txt' -Encoding utf8
    Compress-Archive -Path 'dist\SuperYTDownloader\*' -DestinationPath 'dist\SuperYTDownloader-windows-x64.zip' -Force
    Write-Host 'Paquete listo: dist\SuperYTDownloader-windows-x64.zip'
} finally {
    if ($null -eq $PreviousQtPlatform) {
        Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    } else {
        $env:QT_QPA_PLATFORM = $PreviousQtPlatform
    }
    Pop-Location
}
