# Herramientas externas

Coloca aquí `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe` y `deno.exe` de Windows x64.
No se añaden binarios a Git. Se conservan separados del ejecutable de la GUI para actualizarlos.

Preparación automática desde la raíz, con Python instalado:

```powershell
python scripts/setup_tools.py
```

El script descarga versiones actuales, verifica SHA256 y conserva procedencia y licencias.
Cierra la aplicación antes de actualizar. También puedes elegir rutas en Ajustes.

Descarga manual:

- yt-dlp: https://github.com/yt-dlp/yt-dlp/releases
- FFmpeg y FFprobe: https://www.gyan.dev/ffmpeg/builds/ (release essentials ZIP)
- Deno: https://github.com/denoland/deno/releases (x86_64-pc-windows-msvc ZIP)

Conserva las licencias que acompañan a las herramientas al distribuirlas.
Para desarrollar en macOS/Linux usa sus ejecutables nativos sin `.exe`, en esta carpeta o PATH.
