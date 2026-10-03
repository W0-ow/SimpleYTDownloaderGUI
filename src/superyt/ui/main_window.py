import logging
import sys
from pathlib import Path
from tempfile import TemporaryFile

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from superyt import __version__
from superyt.app_update import AppRelease, can_install, launch_installer
from superyt.formats import normalize_url, progress_detail
from superyt.models import DownloadItem, DownloadOptions
from superyt.settings import Settings
from superyt.tools import resolve_tools
from superyt.ui.dialogs import PasteDialog, show_formats
from superyt.ui.workers import AppUpdateWorker, DownloadWorker, InspectWorker, UpdateWorker
from superyt.updater import update_due

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.items: list[DownloadItem] = []
        self.worker = None
        self.probe = None
        self.updater = None
        self.app_updater = None
        self.check_application_after_tools = False
        self.component_update_summary = ""
        self.update_pending = False
        self.start_after_update = False
        self.update_succeeded = False
        self.closing = False
        self.setWindowTitle("Super YT Downloader")
        self.setWindowIcon(QIcon(str(Path(__file__).parents[1] / "assets/app.svg")))
        self.resize(1080, 760)
        self.setMinimumSize(880, 640)
        self.build_ui()
        self.load_settings()
        self.update_tools_notice()
        self.update_controls()

    def button(self, text, callback, primary=False):
        button = QPushButton(text)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        return button

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(16)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Super YT Downloader")
        title.setObjectName("heading")
        subtitle = QLabel("Tus vídeos y tu audio, en una sola cola.")
        subtitle.setObjectName("subheading")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.update_button = self.button("Buscar actualizaciones", self.request_all_updates)
        self.update_button.setVisible(sys.platform in ("win32", "darwin"))
        layout.addLayout(header)

        card = QFrame()
        card.setObjectName("card")
        form = QVBoxLayout(card)
        form.setContentsMargins(18, 16, 18, 16)
        section = QLabel("01   AÑADE TUS ENLACES")
        section.setObjectName("section")
        form.addWidget(section)
        links = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("Pega un enlace de YouTube, Shorts o youtu.be")
        self.url.setAccessibleName("Enlace de YouTube")
        self.url.returnPressed.connect(self.add_url)
        links.addWidget(self.url, 1)
        links.addWidget(self.button("Añadir", self.add_url, True))
        links.addWidget(self.button("Varios enlaces", self.paste_many))
        form.addLayout(links)
        section = QLabel("02   ELIGE CÓMO GUARDARLOS")
        section.setObjectName("section")
        form.addWidget(section)
        options = QGridLayout()
        self.mode = QComboBox()
        for label, value in (
            ("Vídeo + audio", "video"),
            ("Audio original", "original"),
            ("Audio MP3", "mp3"),
        ):
            self.mode.addItem(label, value)
        self.height = QComboBox()
        self.height.addItem("Mejor disponible", None)
        for height in (2160, 1440, 1080, 720, 480, 360):
            self.height.addItem(f"Hasta {height}p", height)
        self.profile = QComboBox()
        self.profile.addItem("MP4 compatible · H.264", True)
        self.profile.addItem("Máxima calidad · MKV al unir", False)
        self.profile.setToolTip(
            "H.264 prioriza compatibilidad. Si no está disponible, prueba Máxima calidad."
        )
        self.bitrate = QComboBox()
        for bitrate in (128, 192, 256, 320):
            self.bitrate.addItem(f"{bitrate} kbps", bitrate)
        for col, (label, widget) in enumerate(
            (
                ("Contenido", self.mode),
                ("Resolución máxima", self.height),
                ("Perfil de vídeo", self.profile),
                ("Calidad MP3", self.bitrate),
            )
        ):
            options.addWidget(QLabel(label), 0, col)
            options.addWidget(widget, 1, col)
        form.addLayout(options)
        form.addWidget(QLabel("Las opciones se guardan en cada enlace al añadirlo a la cola."))
        self.mode.currentIndexChanged.connect(self.update_mode)
        self.destination = QLineEdit()
        self.destination.setAccessibleName("Carpeta de destino")
        destination = QHBoxLayout()
        destination.addWidget(QLabel("Guardar en"))
        destination.addWidget(self.destination, 1)
        self.browse_button = self.button("Examinar", self.choose_folder)
        destination.addWidget(self.browse_button)
        form.addLayout(destination)
        layout.addWidget(card)

        queue_header = QHBoxLayout()
        self.queue_label = QLabel("COLA DE DESCARGAS · 0 elementos")
        self.queue_label.setObjectName("section")
        queue_header.addWidget(self.queue_label, 1)
        self.inspect_button = self.button("Ver formatos", self.inspect_selected)
        self.apply_options_button = self.button(
            "Aplicar opciones a seleccionados", self.apply_options_to_selected
        )
        queue_header.addWidget(self.apply_options_button)
        queue_header.addWidget(self.inspect_button)
        layout.addLayout(queue_header)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Vídeo / enlace", "Opciones", "Estado", "Progreso"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col, width in ((1, 170), (2, 130), (3, 140)):
            self.table.setColumnWidth(col, width)
        self.table.itemSelectionChanged.connect(self.update_controls)
        self.table.cellDoubleClicked.connect(self.open_item)
        layout.addWidget(self.table, 1)
        controls = QHBoxLayout()
        self.download_button = self.button("Descargar pendientes", self.start_downloads, True)
        self.cancel_button = self.button("Cancelar", self.cancel)
        self.retry_button = self.button("Reintentar fallidos", self.retry_failed)
        self.remove_button = self.button("Quitar seleccionados", self.remove_selected)
        for button in (
            self.download_button,
            self.cancel_button,
            self.retry_button,
            self.remove_button,
        ):
            controls.addWidget(button)
        controls.addStretch()
        controls.addWidget(self.button("Abrir carpeta", self.open_folder))
        layout.addLayout(controls)
        self.notice = QLabel()
        self.notice.setObjectName("notice")
        self.notice.setWordWrap(True)
        self.notice.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.notice)
        self.details_toggle = QCheckBox("Mostrar detalles de la sesión")
        layout.addWidget(self.details_toggle)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(1200)
        self.log.setMaximumHeight(140)
        self.log.hide()
        self.details_toggle.toggled.connect(self.log.setVisible)
        layout.addWidget(self.log)
        footer = QHBoxLayout()
        suffix = " · Pruebas Mac" if sys.platform == "darwin" else ""
        footer.addWidget(QLabel(f"Versión {__version__}{suffix}"))
        footer.addStretch()
        footer.addWidget(self.update_button)
        layout.addLayout(footer)

    def load_settings(self):
        self.destination.setText(self.settings.destination)
        for combo, value in (
            (self.mode, self.settings.mode),
            (self.height, self.settings.height),
            (self.profile, self.settings.compatible),
            (self.bitrate, self.settings.bitrate),
        ):
            combo.setCurrentIndex(max(0, combo.findData(value)))
        self.update_mode()

    def save_settings(self):
        self.settings.destination = self.destination.text().strip()
        self.settings.mode = self.mode.currentData()
        self.settings.height = self.height.currentData()
        self.settings.compatible = self.profile.currentData()
        self.settings.bitrate = self.bitrate.currentData()
        try:
            self.settings.save()
        except OSError as exc:
            self.append_log(f"No se pudieron guardar las preferencias: {exc}")

    def update_mode(self):
        busy = self.worker is not None or self.probe is not None or self.updater is not None
        self.height.setEnabled(not busy and self.mode.currentData() == "video")
        self.profile.setEnabled(not busy and self.mode.currentData() == "video")
        self.bitrate.setEnabled(not busy and self.mode.currentData() == "mp3")

    def update_tools_notice(self):
        try:
            resolve_tools()
            self.notice.setText("Listo. Añade enlaces para empezar.")
        except ValueError:
            self.notice.setText(
                "Prepararemos los componentes necesarios automáticamente."
                if sys.platform == "win32"
                else "Faltan componentes para las pruebas locales."
            )

    def request_all_updates(self):
        if self.closing or self.updater is not None or self.app_updater is not None:
            return
        self.check_application_after_tools = True
        self.request_update()

    def check_app_update(self, info=None):
        if self.closing or self.app_updater is not None:
            return
        if self.worker is not None or self.probe is not None or self.updater is not None:
            self.notice.setText("Espera a que termine la tarea para actualizar la aplicación.")
            return
        self.app_update_value = None
        self.app_update_error = None
        self.app_updater = AppUpdateWorker(info, self)
        self.app_updater.result.connect(self.app_update_result)
        self.app_updater.error.connect(self.app_update_failed)
        self.app_updater.progress.connect(self.notice.setText)
        self.app_updater.finished.connect(self.app_update_finished)
        self.notice.setText("Descargando actualización…" if info else "Buscando nueva versión…")
        self.centralWidget().setEnabled(False)
        self.app_updater.start()

    def app_update_result(self, value):
        self.app_update_value = value

    def app_update_failed(self, message):
        self.app_update_error = message

    def app_update_finished(self):
        self.app_updater.deleteLater()
        self.app_updater = None
        self.centralWidget().setEnabled(True)
        if self.closing:
            self.close()
            return
        if self.app_update_error:
            self.notice.setText(self.component_update_summary +
                                " No se pudo comprobar o actualizar la aplicación.")
            self.append_log(self.app_update_error)
            QMessageBox.warning(self, "Actualizaciones", self.app_update_error)
            return
        value = self.app_update_value
        if isinstance(value, AppRelease):
            if not can_install():
                QMessageBox.information(
                    self, "Nueva versión disponible",
                    f"Disponible: {value.version}.\n\n{value.notes[:3000]}\n\n"
                    "La instalación automática está disponible en la app instalada de Windows. "
                    "Esta versión de pruebas/portable solo comprueba las publicaciones.")
                self.notice.setText(f"Nueva versión disponible: {value.version}.")
                return
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Nueva versión disponible")
            dialog.setTextFormat(Qt.TextFormat.PlainText)
            dialog.setText(f"Versión {value.version}\n\n{value.notes[:3000]}\n\n"
                           "Se reiniciará la aplicación. La cola de enlaces no se conserva.")
            install = dialog.addButton("Actualizar y reiniciar", QMessageBox.ButtonRole.AcceptRole)
            dialog.addButton("Ahora no", QMessageBox.ButtonRole.RejectRole)
            dialog.exec()
            if dialog.clickedButton() == install:
                self.check_app_update(value)
        elif isinstance(value, Path):
            try:
                self.save_settings()
                launch_installer(value)
            except Exception as exc:
                QMessageBox.warning(self, "No se pudo iniciar la actualización", str(exc))
                return
            self.close()
        else:
            self.notice.setText(self.component_update_summary +
                                f" Aplicación al día (versión {__version__}).")

    def startup_update(self):
        if self.app_updater is None and sys.platform == "win32" and update_due():
            self.request_update()

    def request_update(self):
        if (self.closing or self.updater is not None or self.app_updater is not None
                or sys.platform not in ("win32", "darwin")):
            return
        if self.worker is not None or self.probe is not None:
            self.update_pending = True
            self.update_button.setText("Actualización pendiente")
            self.update_button.setEnabled(False)
            self.notice.setText("Buscaremos actualizaciones cuando termine la tarea en curso.")
            return
        self.update_pending = False
        self.update_succeeded = False
        self.update_button.setText("Actualizando…")
        self.updater = UpdateWorker(self)
        self.updater.progress.connect(self.notice.setText)
        self.updater.progress.connect(self.append_log)
        self.updater.result.connect(self.update_result)
        self.updater.error.connect(self.update_error)
        self.updater.finished.connect(self.update_finished)
        self.notice.setText("Preparando aplicación…")
        self.update_controls()
        self.updater.start()

    def update_result(self, changed):
        self.update_succeeded = True
        self.notice.setText(
            "Componentes actualizados. Listo para descargar."
            if changed
            else "Componentes comprobados. Listo para descargar."
        )

        if sys.platform == "darwin":
            self.notice.setText(
                "yt-dlp y Deno actualizados. FFmpeg/FFprobe se gestionan con Homebrew; "
                "consulta Mostrar detalles de la sesión para ver las versiones.")

    def update_error(self, message):
        self.append_log(message)
        if self.updater is not None and self.updater.cancel_event.is_set():
            self.notice.setText("Actualización cancelada. Se conserva la versión instalada.")
            return
        try:
            resolve_tools()
            self.notice.setText("No se pudo actualizar. Puedes continuar con la versión instalada.")
        except ValueError:
            self.notice.setText(
                "No se pudo preparar la aplicación. Comprueba la conexión y pulsa Buscar actualizaciones."
            )

    def update_finished(self):
        check_application = (
            self.check_application_after_tools and not self.updater.cancel_event.is_set()
        )
        self.check_application_after_tools = False
        self.component_update_summary = self.notice.text()
        self.updater.deleteLater()
        self.updater = None
        self.update_button.setText("Buscar actualizaciones")
        resume = self.start_after_update and self.update_succeeded
        self.start_after_update = False
        self.update_controls()
        if self.closing:
            QTimer.singleShot(0, self.close)
        elif check_application:
            self.check_app_update()
        elif resume:
            QTimer.singleShot(0, self.start_downloads)

    def run_pending_update(self):
        if self.update_pending and not self.closing:
            QTimer.singleShot(0, self.request_update)

    def update_controls(self):
        busy = self.worker is not None or self.probe is not None or self.updater is not None
        selected = bool(self.table.selectionModel().selectedRows())
        self.download_button.setEnabled(
            not busy and any(i.status == "Pendiente" for i in self.items)
        )
        self.cancel_button.setEnabled(busy and not self.closing)
        self.retry_button.setEnabled(
            not busy and any(i.status in ("Error", "Cancelado") for i in self.items)
        )
        self.remove_button.setEnabled(not busy and selected)
        self.inspect_button.setEnabled(not busy and selected)
        self.apply_options_button.setEnabled(
            not busy and selected and all(
                self.items[index.row()].status in ("Pendiente", "Error", "Cancelado")
                for index in self.table.selectionModel().selectedRows()
            )
        )
        for widget in (self.mode, self.destination, self.browse_button):
            widget.setEnabled(not busy)
        self.update_button.setEnabled(
            self.updater is None and not self.update_pending and not self.closing
        )
        self.update_mode()
        self.queue_label.setText(f"COLA DE DESCARGAS · {len(self.items)} elementos")

    def add_url(self):
        if self.add_links([self.url.text()]):
            self.url.clear()

    def selected_options(self):
        if not self.destination.text().strip():
            raise ValueError("Selecciona una carpeta de destino.")
        return DownloadOptions(
            Path(self.destination.text()).expanduser().resolve(),
            self.mode.currentData(), self.height.currentData(),
            self.profile.currentData(), self.bitrate.currentData(),
        )

    def options_label(self, options):
        if options.mode == "original":
            return "Audio original"
        if options.mode == "mp3":
            return f"MP3 · {options.bitrate} kbps"
        quality = f"≤ {options.height}p" if options.height else "Mejor disponible"
        profile = "MP4 H.264" if options.compatible else "Máxima calidad"
        return f"Vídeo · {quality} · {profile}"

    def refresh_options(self, row):
        options = self.items[row].options
        label = self.options_label(options)
        self.table.item(row, 1).setText(label)
        self.table.item(row, 1).setToolTip(f"{label}\n{options.destination}")

    def apply_options_to_selected(self):
        if self.worker is not None or self.probe is not None or self.updater is not None:
            return
        rows = [index.row() for index in self.table.selectionModel().selectedRows()]
        if not rows or any(self.items[row].status not in ("Pendiente", "Error", "Cancelado")
                           for row in rows):
            return
        try:
            options = self.selected_options()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Revisa las opciones", str(exc))
            return
        for row in rows:
            self.items[row].options = options
            self.refresh_options(row)
        self.notice.setText(f"Opciones aplicadas a {len(rows)} enlace(s).")

    def add_links(self, links):
        try:
            options = self.selected_options()
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Revisa las opciones", str(exc))
            return 0
        known = {item.url for item in self.items}
        added = 0
        rejected = []
        duplicates = 0
        for text in links:
            if not text.strip():
                continue
            try:
                url = normalize_url(text)
            except ValueError as exc:
                rejected.append(f"{text[:100]}: {exc}")
                continue
            if url in known:
                duplicates += 1
                continue
            item = DownloadItem(url, options=options)
            self.items.append(item)
            known.add(url)
            self.add_row(item)
            added += 1
        self.notice.setText(
            f"{added} enlace(s) añadido(s) · {duplicates} duplicado(s) · {len(rejected)} no válido(s)"
        )
        if rejected:
            QMessageBox.warning(self, "Revisa los enlaces", "\n\n".join(rejected[:6]))
        self.update_controls()
        return added

    def paste_many(self):
        dialog = PasteDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.add_links(dialog.editor.toPlainText().splitlines())

    def add_row(self, item):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for column, text in enumerate((item.url, self.options_label(item.options), item.status)):
            cell = QTableWidgetItem(text)
            cell.setToolTip(text)
            self.table.setItem(row, column, cell)
        self.refresh_options(row)
        progress = QProgressBar()
        progress.setValue(0)
        self.table.setCellWidget(row, 3, progress)

    def remove_selected(self):
        rows = sorted((i.row() for i in self.table.selectionModel().selectedRows()), reverse=True)
        for row in rows:
            self.items.pop(row)
            self.table.removeRow(row)
        self.update_controls()

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Carpeta de descarga", self.destination.text()
        )
        if folder:
            self.destination.setText(folder)

    def open_folder(self):
        path = Path(self.destination.text()).expanduser()
        if path.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
        else:
            self.notice.setText("La carpeta de destino todavía no existe.")

    def open_item(self, row, column):
        if self.items[row].path and Path(self.items[row].path).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.items[row].path))
        elif self.items[row].detail:
            QMessageBox.information(self, "Detalle de la descarga", self.items[row].detail)

    def start_downloads(self):
        if self.worker is not None or self.probe is not None or self.updater is not None:
            return
        pending = [item for item in self.items if item.status == "Pendiente"]
        if not pending:
            return
        try:
            tools = resolve_tools(needs_ffmpeg=any(item.options.mode != "original" for item in pending))
        except ValueError as exc:
            if sys.platform == "win32":
                self.start_after_update = True
                self.request_update()
            else:
                QMessageBox.warning(self, "Preparación local", str(exc))
            return
        try:
            for destination in {item.options.destination for item in pending}:
                destination.mkdir(parents=True, exist_ok=True)
                with TemporaryFile(dir=destination):
                    pass
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "No se puede iniciar", str(exc))
            return
        self.save_settings()
        self.worker = DownloadWorker(pending, tools, self)
        self.worker.event.connect(self.on_event)
        self.worker.finished.connect(self.downloads_finished)
        self.worker.start()
        self.notice.setText("Descargando la cola. Puedes añadir enlaces para la siguiente tanda.")
        self.update_controls()

    def retry_failed(self):
        for row, item in enumerate(self.items):
            if item.status in ("Error", "Cancelado"):
                item.status = "Pendiente"
                item.detail = ""
                item.progress = 0
                self.refresh_row(row)
        self.start_downloads()

    def on_event(self, event):
        row = next((n for n, item in enumerate(self.items) if item.id == event.item_id), None)
        if row is None:
            return
        item = self.items[row]
        if event.kind == "title":
            item.title = event.value
        elif event.kind == "path":
            item.path = event.value
        elif event.kind == "status":
            item.status = event.value
            if item.status == "Completado":
                item.progress = 100
                item.detail = item.path or "Descarga completada"
            elif item.status == "Cancelado":
                item.detail = (
                    "Descarga cancelada. Puedes reintentar para aprovechar los archivos parciales."
                )
        elif event.kind == "progress":
            item.progress, item.detail = progress_detail(event.value)
            item.status = "Descargando"
        elif event.kind == "postprocess":
            item.status = "Procesando"
        elif event.kind == "error":
            item.status = "Error"
            item.detail = event.value
            self.append_log(f"{item.title or item.url}: {event.value}")
        elif event.kind == "log":
            self.append_log(event.value)
            return
        self.refresh_row(row)
        self.notice.setText(f"{item.status} · {item.title or item.url}\n{item.detail[:250]}")

    def refresh_row(self, row):
        item = self.items[row]
        self.table.item(row, 0).setText(item.title or item.url)
        self.table.item(row, 0).setToolTip(item.url + (f"\n{item.path}" if item.path else ""))
        cell = self.table.item(row, 2)
        cell.setText(item.status)
        cell.setToolTip(item.detail)
        color = {"Error": "#ff9299", "Completado": "#7bdbb2", "Cancelado": "#e8c47c"}.get(
            item.status, "#dce5f1"
        )
        cell.setForeground(QColor(color))
        bar = self.table.cellWidget(row, 3)
        if item.status in ("Consultando", "Procesando"):
            bar.setRange(0, 0)
        else:
            bar.setRange(0, 100)
            bar.setValue(item.progress)
        bar.setToolTip(item.detail)

    def append_log(self, text):
        self.log.appendPlainText(text)
        logger.info(text)

    def downloads_finished(self):
        self.worker.deleteLater()
        self.worker = None
        completed = sum(i.status == "Completado" for i in self.items)
        failed = sum(i.status == "Error" for i in self.items)
        cancelled = sum(i.status == "Cancelado" for i in self.items)
        pending = sum(i.status == "Pendiente" for i in self.items)
        self.notice.setText(
            f"Cola detenida · {completed} completado(s) · {failed} error(es) · "
            f"{cancelled} cancelado(s) · {pending} pendiente(s)"
        )
        self.update_controls()
        if self.closing:
            QTimer.singleShot(0, self.close)
        else:
            self.run_pending_update()

    def inspect_selected(self):
        if self.worker is not None or self.probe is not None or self.updater is not None:
            return
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        try:
            tools = resolve_tools(needs_ffmpeg=False)
        except ValueError as exc:
            if sys.platform in ("win32", "darwin"):
                self.request_update()
            else:
                QMessageBox.warning(self, "Preparación local", str(exc))
            return
        self.probe = InspectWorker(self.items[selected[0].row()].url, tools, self)
        self.probe.result.connect(self.inspection_result)
        self.probe.error.connect(self.inspection_error)
        self.probe.finished.connect(self.inspection_finished)
        self.probe.start()
        self.notice.setText("Consultando las resoluciones disponibles…")
        self.update_controls()

    def inspection_result(self, metadata):
        if not self.closing:
            show_formats(metadata, self)

    def inspection_error(self, message):
        if not self.closing:
            QMessageBox.warning(self, "No se pudieron consultar los formatos", message)

    def inspection_finished(self):
        self.probe.deleteLater()
        self.probe = None
        self.notice.setText("Consulta finalizada.")
        self.update_controls()
        if self.closing:
            QTimer.singleShot(0, self.close)
        else:
            self.run_pending_update()

    def cancel(self):
        if self.worker is not None:
            self.worker.cancel()
        if self.probe is not None:
            self.probe.cancel()
        if self.updater is not None:
            self.updater.cancel()
        self.cancel_button.setEnabled(False)
        self.notice.setText(
            "Cancelando actualización…"
            if self.updater is not None
            else "Cancelando… Se conservarán los archivos parciales para reintentar."
        )

    def closeEvent(self, event):
        if self.app_updater is not None:
            self.closing = True
            self.app_updater.cancel()
            event.ignore()
            return
        if self.updater is not None:
            self.closing = True
            self.cancel()
            self.update_controls()
            event.ignore()
            return
        if self.worker is not None or self.probe is not None:
            if not self.closing:
                answer = QMessageBox.question(
                    self,
                    "Cerrar aplicación",
                    "Hay una tarea en curso. ¿Cancelarla y cerrar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                self.closing = True
                self.cancel()
                self.update_controls()
            event.ignore()
            return
        self.save_settings()
        event.accept()
