# Super YT Downloader

Aplicación de escritorio en español para descargar vídeos de YouTube o guardar solo el audio.
Interfaz PySide6 y herramientas externas actualizables, orientada a **Windows 10/11 x64**.

## Uso en Windows

Descomprime **toda** la carpeta portable y abre `SuperYTDownloader.exe`. No necesita una instalación
separada de Python. Conserva `_internal/` y `bin/` junto al ejecutable.

1. Añade un enlace o pega varios, uno por línea.
2. Elige **Vídeo + audio**, **Audio original** o **Audio MP3**.
3. Selecciona resolución máxima, perfil o bitrate, y carpeta de destino.
4. Pulsa **Descargar pendientes**. Puedes cancelar y reintentar fallidos/cancelados.

Selecciona una fila y pulsa **Ver formatos** para consultar resoluciones y códecs disponibles.
Doble clic en una descarga completada abre su archivo; en una fallida muestra su error.
Las descargas se ejecutan de una en una. Los enlaces añadidos durante una tanda quedan para la siguiente.
Las opciones se aplican a todos los pendientes al iniciar cada tanda; reintentar usa los ajustes actuales.

- **Hasta 1080p**, por ejemplo, permite 720p si no hay 1080p; nunca aumenta la resolución.
- **MP4 compatible · H.264** selecciona vídeo H.264 y audio M4A. Si no está disponible, muestra
  un error: selecciona **Máxima calidad** para admitir otros códecs. H.264 puede limitar 1440p/4K.
- **Máxima calidad** usa los mejores formatos dentro del límite y MKV cuando hay que unir pistas.
  Un formato que ya trae audio y vídeo puede conservar su contenedor original.
- **Audio original** conserva la pista disponible (por ejemplo, M4A/WebM) sin recodificar.
- **Audio MP3** convierte con FFmpeg a 128, 192, 256 o 320 kbps. Un bitrate mayor no mejora la fuente.
- Durante vídeo + audio, el porcentaje corresponde a la pista actual y puede reiniciarse al pasar
  de vídeo a audio. La unión/conversión tiene un indicador indeterminado.
- Las playlists completas no se importan: un enlace con vídeo y playlist descarga solo ese vídeo.
- Se conservan archivos parciales al cancelar y se intenta continuar al reintentar con las mismas
  opciones. No se sobrescriben archivos terminados. La cola no se conserva al cerrar esta versión.

## Herramientas

En `bin/`, junto al ejecutable de la GUI:

```text
SuperYTDownloader/
├── SuperYTDownloader.exe
├── _internal/
├── bin/
│   ├── yt-dlp.exe
│   ├── ffmpeg.exe
│   ├── ffprobe.exe
│   ├── deno.exe
│   ├── licenses/
│   └── tools-manifest.json
└── LEEME.md
```

Se busca primero la ruta elegida en **Ajustes**, después `bin/`, y por último `PATH`.
Una ruta explícita incorrecta da un error, sin seleccionar silenciosamente otra instalación.
FFprobe debe acompañar a FFmpeg en su misma carpeta. yt-dlp y Deno se necesitan para todos los modos;
FFmpeg y FFprobe son obligatorios para vídeo y MP3. Ajustes permite comprobar las versiones sin bloquear la GUI.
La aplicación ignora archivos de configuración externos de yt-dlp para respetar las opciones de la interfaz.

Para descargar las herramientas Windows x64 automáticamente, con Python instalado:

```powershell
python scripts/setup_tools.py
```

Descarga desde los proyectos yt-dlp y Deno en GitHub y desde Gyan para FFmpeg. Verifica SHA256
antes de copiar; guarda URLs, hashes y licencias en `bin/`. Repite el comando con la aplicación
cerrada para actualizar. No se descargan actualizaciones al abrir la GUI.
Consulta [bin/README.md](bin/README.md) para preparación manual.

## Desarrollo

Python 3.11 o posterior; para construir Windows se usa Python 3.12 x64.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m superyt
```

También se conserva `python SuperYT.py` como lanzador después de instalar el proyecto.
En macOS/Linux usa `python3 -m venv .venv`, `.venv/bin/python` y las herramientas **nativas** en
`bin/` (sin `.exe`), PATH o Ajustes. El script de herramientas descarga binarios Windows, incluso
cuando se ejecuta desde otro sistema, y no sirven para ejecutar descargas en macOS/Linux.

## Construir el portable en Windows

Desde PowerShell, con Python 3.12 x64 instalado:

```powershell
.\scripts\build_windows.ps1 -DownloadTools
```

El script prepara el entorno, instala dependencias, descarga herramientas, ejecuta comprobaciones,
genera el icono y empaqueta con PyInstaller. Resultado:
`dist/SuperYTDownloader-windows-x64.zip`.
Si ya has preparado `bin/`, omite `-DownloadTools`.
La construcción registra las dependencias instaladas en `build-dependencies.txt`.

También hay un flujo **Windows checks and portable build** de GitHub Actions: push/PR ejecutan
comprobaciones, y **Run workflow** con `bundle_tools` genera el ZIP descargable como artefacto.
No publica releases. El ejecutable Windows se construye en Windows, no directamente en macOS.

## Pruebas

```powershell
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m pytest -q
```

Las pruebas no descargan contenido: comprueban selección de formatos, URLs, rutas, preferencias,
procesos reales simulados, errores, cancelación y cola de la GUI con Qt offscreen.
Antes de distribuir, prueba en Windows con las herramientas reales: vídeo 720p/1080p, audio MP3,
rutas con espacios/acentos, enlace no disponible, cancelación durante descarga y unión con FFmpeg.

## Estructura

```text
src/superyt/
├── app.py           # Arranque y registro
├── models.py        # Opciones, cola y eventos
├── formats.py       # URLs, selección y protocolo de progreso
├── downloader.py    # Procesos, consulta y cancelación
├── settings.py      # Preferencias y rutas
├── tools.py         # Detección y versiones
├── assets/          # Icono SVG
└── ui/              # Ventanas, estilos y workers Qt
scripts/             # Herramientas y empaquetado Windows
tests/               # Pruebas de lógica, procesos e interfaz
bin/                 # Ejecutables externos, excluidos de Git
```

Preferencias y registros: `%LOCALAPPDATA%\SuperYTDownloader` en Windows. Registro rotativo:
`superyt.log` (hasta tres archivos de aproximadamente 1 MB). No se escriben ajustes junto al `.exe`.
En macOS se usa `~/Library/Application Support/SuperYTDownloader`; en Linux, `$XDG_CONFIG_HOME`
o `~/.config/SuperYTDownloader`.

Consulta [THIRD_PARTY.md](THIRD_PARTY.md) para componentes externos.
