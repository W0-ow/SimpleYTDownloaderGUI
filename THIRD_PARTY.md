# Componentes externos

La GUI utiliza [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html).
Los módulos Qt incluidos se distribuyen como bibliotecas separadas en `_internal/`.

Las herramientas se ejecutan como procesos independientes:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): incluye componentes de terceros en su ejecutable.
- [FFmpeg y FFprobe](https://ffmpeg.org/): el paquete de Gyan essentials incluye su licencia y README.
- [Deno](https://github.com/denoland/deno): licencia MIT y componentes de terceros.

`scripts/setup_tools.py` guarda licencias de las herramientas en `bin/licenses/` y las URLs,
versiones disponibles y SHA256 de los paquetes descargados en `bin/tools-manifest.json`.
No elimines estos archivos al compartir el paquete. Consulta los proyectos originales para
el código fuente, las licencias completas y las condiciones de distribución de cada componente.
