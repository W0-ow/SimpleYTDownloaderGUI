# Super YT Downloader

Aplicación en español para descargar vídeos de YouTube o guardar solo audio.
**Distribución para Windows 10/11 x64.** La aplicación prepara y actualiza sus componentes
sin elegir motores, instalar Python ni configurar rutas.

## Instalación en Windows

Para **Windows 10/11 de 64 bits**, elige una de estas opciones:

### Opción recomendada: instalador `.exe`

1. Abre [Releases](https://github.com/W0-ow/SimpleYTDownloaderGUI/releases/latest) y despliega **Assets** si los archivos no aparecen.
2. Descarga exactamente **`SuperYTDownloader-Setup.exe`**. El `.exe` que lleva **Setup** en el nombre es el instalador.
3. Haz doble clic en el archivo descargado y sigue los pasos del asistente.
4. Abre **Super YT Downloader** desde el acceso directo creado por el instalador.

Instala la aplicación para tu usuario, crea accesos directos y añade un desinstalador.
No necesitas Python ni permisos de administrador. Las releases incluyen los componentes de descarga.
En el primer inicio, espera a que termine **Preparando aplicación…**; necesita Internet.

### Alternativa: ZIP portable, sin instalación

1. En **Assets**, descarga exactamente **`SuperYTDownloader-windows-x64.zip`**.
2. Haz clic derecho sobre el ZIP y selecciona **Extraer todo…**.
3. Abre la carpeta extraída y haz doble clic en **`SuperYTDownloader.exe`**.

Conserva toda la carpeta, incluida `_internal/` junto al ejecutable. Ejecuta la aplicación
desde la carpeta extraída. La actualización automática de la aplicación requiere el instalador.

Los archivos **Source code (zip)** y **Source code (tar.gz)** contienen el código fuente.
Para usar la aplicación, descarga el instalador recomendado o el ZIP portable indicado arriba.

## Uso en Windows

Abre **Super YT Downloader** desde su acceso directo.

1. La primera vez muestra **Preparando aplicación…** y descarga los componentes necesarios.
   Necesita Internet; puede tardar unos minutos.
2. Elige vídeo, audio original o MP3, calidad y carpeta de destino.
3. Añade un enlace o pega varios, uno por línea; se guardarán con esas opciones.
4. Pulsa **Descargar pendientes**.

Las descargas se ejecutan de una en una. Puedes cancelarlas, reintentar fallidos/cancelados
y quitar filas seleccionadas. Los enlaces añadidos durante una tanda quedan para la siguiente.
Cada enlace conserva el formato, calidad y carpeta elegidos al añadirlo. Reintentar conserva esas
opciones. Para cambiarlas, selecciona filas pendientes/fallidas/canceladas, ajusta los controles y
pulsa **Aplicar opciones a seleccionados**. Las filas completadas no se modifican.
Doble clic abre un archivo completado o muestra el detalle de un error.

## Un solo botón para actualizar todo

En la parte inferior aparecen la versión y **Buscar actualizaciones**. Este único botón primero
comprueba y actualiza los componentes y después consulta la última release estable de la aplicación,
incluso si la actualización de componentes falla. Si hay una versión nueva ofrece
**Actualizar y reiniciar**, con sus notas de versión. Cancelar detiene también la comprobación restante.
Descarga y verifica SHA256 antes de cerrar la aplicación. Un proceso auxiliar espera al cierre,
ejecuta el instalador sin asistente y vuelve a abrir el programa si la instalación termina correctamente.
Las preferencias y los archivos descargados se conservan; la cola de enlaces no se conserva al reiniciar.
Durante una descarga o consulta activa, la comprobación queda pendiente hasta que termine.
Si falla la instalación, muestra el error y la ubicación del registro; no garantiza revertir una
instalación parcialmente aplicada. Puedes volver a ejecutar el instalador de la release.

En Mac de desarrollo y en el portable se pueden consultar las versiones, pero no instalarlas automáticamente.
Sin una release publicada, GitHub devolverá un error de consulta; no se simula una actualización.

## Actualizaciones de componentes

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
- Las comprobaciones automáticas al abrir actualizan los componentes; el botón manual comprueba también la aplicación.

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
con el lanzador `py` e **Inno Setup 6** en su ubicación estándar. Los usuarios del portable terminado no necesitan Python.

```powershell
.\scripts\build_windows.ps1 -Installer -DownloadTools
```

Si PowerShell bloquea los scripts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

El script crea el entorno, instala dependencias, ejecuta comprobaciones y empaqueta la GUI.
Los componentes se descargarán automáticamente cuando el usuario abra el programa.
Resultados:

- `dist/SuperYTDownloader-Setup.exe` (con `-Installer`)
- `dist/SuperYTDownloader/SuperYTDownloader.exe`
- `dist/SuperYTDownloader-windows-x64.zip`

Opcionalmente, `-DownloadTools` incorpora una copia de las herramientas al portable,
para poder utilizar esa copia aunque falle la comprobación inicial. El actualizador sigue funcionando.

GitHub Actions ejecuta las pruebas y comprueba la construcción en Windows. Ejecuta manualmente
el flujo **Windows x64** para obtener un artefacto de prueba. Al publicar un tag `v*.*.*`,
la acción genera el instalador, el portable, sus SHA256 y la GitHub Release correspondiente en borrador para revisión.
El tag debe coincidir con `src/superyt/__init__.py` (por ejemplo, `v1.1.0`); mantén también
la versión de `pyproject.toml` sincronizada.

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
En Mac, **Buscar actualizaciones** actualiza yt-dlp y Deno nativos y consulta la versión
de FFmpeg en Homebrew. FFmpeg/FFprobe se actualizan con `brew upgrade ffmpeg`; las versiones
se muestran en los detalles de la sesión. El mismo botón consulta después las releases de la aplicación.

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
