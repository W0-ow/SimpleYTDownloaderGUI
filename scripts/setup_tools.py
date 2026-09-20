"""Prepare/update Windows components. --destination exports tools for portable builds."""

import argparse
import shutil
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from superyt.updater import prepare_windows, update_lock, update_windows


def export_tools(destination):
    destination.mkdir(parents=True, exist_ok=True)
    with update_lock(destination):
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=destination) as temporary:
            staging = Path(temporary) / "ready"
            changed = prepare_windows(
                staging,
                threading.Event(),
                print,
                previous=destination,
                validate=sys.platform == "win32",
            )
            if changed:
                for path in staging.iterdir():
                    if path.is_dir():
                        shutil.copytree(path, destination / path.name, dirs_exist_ok=True)
                    else:
                        path.replace(destination / path.name)
    print(f"Componentes Windows listos en {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, help="Exportar binarios Windows a esta carpeta")
    args = parser.parse_args()
    try:
        if args.destination:
            export_tools(args.destination.resolve())
        else:
            changed = update_windows(threading.Event(), print)
            print("Actualización completada." if changed else "Todo está actualizado.")
    except KeyboardInterrupt:
        sys.exit("Preparación cancelada.")
    except Exception as exc:
        sys.exit(f"No se pudieron preparar los componentes: {exc}")
