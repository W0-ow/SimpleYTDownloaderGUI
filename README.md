# Super YT Downloader

Aplicación en español para descargar vídeos de YouTube o guardar solo audio.
**Distribución para Windows 10/11 x64.** La aplicación prepara y actualiza sus componentes
sin elegir motores, instalar Python ni configurar rutas.

## Uso en Windows

Descomprime toda la carpeta portable y abre `SuperYTDownloader.exe`.
Conserva `_internal/` junto al ejecutable.

1. La primera vez muestra **Preparando aplicación…** y descarga los componentes necesarios.
   Necesita Internet; puede tardar unos minutos.
2. Añade un enlace o pega varios, uno por línea.
3. Elige vídeo, audio original o MP3, calidad y carpeta de destino.
4. Pulsa **Descargar pendientes**.

Las descargas se ejecutan de una en una. Puedes cancelarlas, reintentar fallidos/cancelados
y quitar filas seleccionadas. Los enlaces añadidos durante una tanda quedan para la siguiente.
Las opciones se aplican al iniciar cada tanda; reintentar utiliza los ajustes actuales.
Doble clic abre un archivo completado o muestra el detalle de un error.

## Actualizaciones automáticas

- Al abrir, comprueba las últimas publicaciones estables de yt-dlp, FFmpeg/FFprobe y Deno.
  Una comprobación correcta se guarda durante 24 horas; no descarga todo en cada apertura.
- **Buscar actualizaciones** permite comprobar e instalar las novedades cuando quieras.
  Si hay una descarga o consulta en curso, espera a que termine.
- Solo descarga los componentes nuevos o dañados. Comprueba SHA256 y que los ejecutables
  funcionen antes de activar una instalación completa.
- Si hay un fallo de red, verificación o ejecución, conserva la instalación anterior.
  Puedes seguir usándola y reintentar la actualización después.
- La interfaz sigue respondiendo durante la preparación. Puedes añadir enlaces y cancelar;
  las descargas esperan a que termine la actualización.
- La actualización afecta a los componentes de descarga, no al código de la aplicación.

Los componentes se guardan en `%LOCALAPPDATA%\SuperYTDownloader\tools`, con una copia
anterior de respaldo. No necesita modificar la carpeta del programa ni permisos de administrador.
Las versiones empaquetadas en `bin/`, si las hubiera, sirven como alternativa cuando no se
puede preparar una instalación nueva. Las antiguas rutas personalizadas dejan de utilizarse.
Solo se abre una instancia de la aplicación por usuario para evitar operaciones simultáneas.

## Formatos

- **Vídeo + audio:** resolución máxima (360p a 2160p) o mejor disponible. «Hasta 1080p»
  permite 720p cuando no hay 1080p; nunca aumenta artificialmente la resolución.
- **MP4 compatible · H.264:** vídeo H.264 y audio M4A. Si no está disponible, selecciona
  **Máxima calidad**, que admite otros códecs y usa MKV al unir pistas.
- **Audio original:** conserva la pista disponible (por ejemplo, M4A/WebM), sin convertirla.
- **Audio MP3:** conversión a 128, 192, 256 o 320 kbps. No mejora la calidad de la fuente.
- **Ver formatos:** consulta resoluciones y códecs disponibles del enlace seleccionado.

El porcentaje corresponde a la pista actual y puede reiniciarse al pasar de vídeo a audio.
La unión/conversión muestra un indicador indeterminado. Un enlace con vídeo y playlist descarga
solo ese vídeo. Se conservan archivos parciales para reintentar con las mismas opciones;
no se sobrescriben archivos terminados. La cola no se conserva al cerrar esta versión.

## Construir el programa en Windows (desarrollo)

Este paso es para crear el portable desde el código fuente. Necesita **Python 3.12 x64**
con el lanzador `py`. Los usuarios del portable terminado no necesitan Python.

```powershell
.\scripts\build_windows.ps1
```

Si PowerShell bloquea los scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

El script crea el entorno, instala dependencias, ejecuta comprobaciones y empaqueta la GUI.
Los componentes se descargarán automáticamente cuando el usuario abra el programa.
Resultados:

- `dist/SuperYTDownloader/SuperYTDownloader.exe`
- `dist/SuperYTDownloader-windows-x64.zip`

Opcionalmente, `-DownloadTools` incorpora una copia de las herramientas al portable,
para poder utilizar esa copia aunque falle la comprobación inicial. El actualizador sigue funcionando.

GitHub Actions ejecuta pruebas en Windows en push/PR. El flujo manual
**Windows checks and portable build**, con `bundle_tools`, genera un ZIP con componentes
como artefacto descargable. No publica releases.

## Ejecutar desde el código

En Windows:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m superyt
```

El primer arranque prepara las herramientas automáticamente. También se puede ejecutar
`.venv\Scripts\python scripts/setup_tools.py` para prepararlas/actualizarlas sin abrir la GUI.
Para exportar herramientas destinadas a un portable: `scripts/setup_tools.py --destination bin`.

### Pruebas locales en este Mac

La distribución `.app` y las actualizaciones automáticas para macOS quedan para otra versión.
Para trabajar con el código y probar descargas se admite el entorno nativo local:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
# FFmpeg/FFprobe deben estar disponibles; si faltan: brew install ffmpeg
.venv/bin/python scripts/setup_dev_macos.py
.venv/bin/python -m superyt
```

El script descarga y verifica yt-dlp y Deno nativos en `bin/`, detectando Intel o Apple Silicon,
y comprueba el FFmpeg local. Puedes repetirlo para actualizar esas dos herramientas de pruebas.
No modifica los binarios Windows de la misma carpeta ni instala una aplicación Mac.
El botón de actualización de Windows se oculta en este modo de desarrollo.

## Pruebas y estructura

```sh
python -m ruff check .
python -m pytest -q
```

Las pruebas no descargan contenido: comprueban formatos con yt-dlp real, procesos simulados,
cola Qt, cancelación, instalación inicial, caché de versiones, reparación, fallos y activación atómica.
La ejecución final de los `.exe` y el portable debe verificarse en Windows.

`src/superyt/` separa interfaz (`ui/`), descargas (`downloader.py`), formatos (`formats.py`),
preferencias (`settings.py`), detección (`tools.py`), fuentes de componentes (`releases.py`)
y actualizaciones (`updater.py`). `scripts/` contiene preparación y empaquetado; `tests/`, las pruebas.
Los ejecutables y las carpetas de construcción quedan excluidos de Git.

Preferencias y registro rotativo: `%LOCALAPPDATA%\SuperYTDownloader` en Windows,
`~/Library/Application Support/SuperYTDownloader` en este Mac.
Consulta [THIRD_PARTY.md](THIRD_PARTY.md) para componentes externos.
