# Super YT Downloader 1.1.0

## Instalación en Windows

Para **Windows 10/11 de 64 bits**:

**Opción recomendada: instalador `.exe`**

1. Despliega **Assets** de esta release y descarga exactamente **`SuperYTDownloader-Setup.exe`**. El `.exe` que lleva **Setup** en el nombre es el instalador.
2. Haz doble clic en el archivo descargado y sigue los pasos del asistente. Crea accesos directos y un desinstalador. No necesitas Python ni permisos de administrador.
3. Abre **Super YT Downloader** desde el acceso directo. En el primer inicio, espera a que termine **Preparando aplicación…**; necesita conexión a Internet.

**Alternativa: ZIP portable, sin instalación**

1. En **Assets**, descarga exactamente **`SuperYTDownloader-windows-x64.zip`**.
2. Haz clic derecho sobre el ZIP y selecciona **Extraer todo…**.
3. Abre la carpeta extraída y haz doble clic en **`SuperYTDownloader.exe`**.

Conserva toda la carpeta, incluida `_internal/` junto al ejecutable. Ejecuta la aplicación desde la carpeta extraída.
La actualización automática de la aplicación requiere la versión instalada.

Los archivos **Source code (zip)** y **Source code (tar.gz)** contienen el código fuente; para usar la aplicación, descarga el instalador recomendado o el ZIP portable indicado arriba.

## Novedades

- Instalador para Windows x64 con accesos directos y desinstalador, sin Python ni permisos de administrador.
- Un único botón para actualizar los componentes y comprobar nuevas versiones de la aplicación.
- Descarga del instalador con verificación SHA256 y actualización con reinicio desde la interfaz.
- Cada enlace conserva formato, calidad y carpeta; los reintentos mantienen esas preferencias.
- Cambio explícito de opciones para las filas seleccionadas de la cola.
- En Mac de pruebas: actualización de yt-dlp y Deno y consulta de FFmpeg gestionado por Homebrew.
- Comprobaciones de instalación, sustitución y arranque en el flujo de Windows.

# Super YT Downloader 1.0.0

Primera versión estable para Windows 10 y 11 de 64 bits.

- Interfaz en español para descargas individuales y colas de enlaces.
- Vídeo y audio unidos, audio original y MP3.
- Selector de resolución máxima y consulta de formatos disponibles.
- Barra de progreso, cancelación, mensajes de error y reintentos.
- Preparación automática de yt-dlp, FFmpeg/FFprobe y Deno en el primer inicio.
- Comprobación automática de actualizaciones a diario y botón para buscar actualizaciones.
- Verificación SHA256, instalación con activación segura y conservación de la versión anterior.
- Paquete portable: no requiere instalar Python en el ordenador de uso.
