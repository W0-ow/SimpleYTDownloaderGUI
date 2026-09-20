# Componentes externos

La GUI utiliza [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/licenses.html).
Los módulos Qt incluidos se distribuyen como bibliotecas separadas en `_internal/`.

Las herramientas se ejecutan como procesos independientes:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): incluye componentes de terceros en su ejecutable.
- [FFmpeg y FFprobe](https://ffmpeg.org/): se utilizan los paquetes de [Gyan](https://github.com/GyanD/codexffmpeg).
- [Deno](https://github.com/denoland/deno): licencia MIT y componentes de terceros.

El actualizador guarda las licencias junto a cada instalación de componentes, en `licenses/`,
y sus versiones, URLs y SHA256 en `tools-manifest.json`. La exportación para un portable
hace lo mismo dentro de `bin/`. No elimines estos archivos al compartir el paquete.
Consulta los proyectos originales para el código fuente, las licencias completas y las
condiciones de distribución de cada componente.
