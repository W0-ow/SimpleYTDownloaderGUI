# Componentes de desarrollo y empaquetado

Los usuarios Windows no necesitan copiar archivos aquí: la aplicación prepara y actualiza
sus componentes en `%LOCALAPPDATA%\SuperYTDownloader\tools`.

Para exportar herramientas Windows al construir un portable con componentes incluidos:

```powershell
python scripts/setup_tools.py --destination bin
```

Descarga las últimas publicaciones estables, verifica SHA256 y guarda las licencias y el
manifiesto de versiones. El empaquetado habitual no necesita esta carpeta; `-DownloadTools`
la incluye como alternativa para usar el programa aunque falle la comprobación inicial.

Para pruebas locales en macOS: `python scripts/setup_dev_macos.py`. Prepara ejecutables nativos
sin `.exe`, manteniendo los de Windows separados. No es un instalador ni una distribución Mac.

Los binarios no se añaden a Git. Conserva sus licencias al compartir paquetes que los incluyan.
