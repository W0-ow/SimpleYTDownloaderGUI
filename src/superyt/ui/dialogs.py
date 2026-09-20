from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from superyt.ui.workers import ToolWorker


class PasteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir varios enlaces")
        self.resize(600, 340)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pega un enlace de YouTube por línea."))
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("https://www.youtube.com/watch?v=…\nhttps://youtu.be/…")
        layout.addWidget(self.editor)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Añadir a la cola")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SettingsDialog(QDialog):
    def __init__(self, overrides, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Herramientas y ajustes")
        self.resize(760, 580)
        self.worker = None
        self.close_when_done = False
        layout = QVBoxLayout(self)
        help_text = QLabel(
            "Deja las rutas vacías para usar bin/ junto a la aplicación y, después, PATH.\n"
            "FFprobe debe estar en la misma carpeta que FFmpeg."
        )
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        form = QFormLayout()
        self.fields = {}
        self.versions = {}
        for name in ("yt-dlp", "ffmpeg", "deno"):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            field = QLineEdit(overrides.get(name, ""))
            field.setPlaceholderText("Detección automática")
            self.fields[name] = field
            browse = QPushButton("Examinar")
            browse.clicked.connect(lambda checked=False, f=field: self.browse(f))
            row_layout.addWidget(field, 1)
            row_layout.addWidget(browse)
            form.addRow(name, row)
        layout.addLayout(form)
        self.check = QPushButton("Comprobar herramientas y versiones")
        self.check.clicked.connect(self.check_versions)
        layout.addWidget(self.check)
        for name in ("yt-dlp", "ffmpeg", "ffprobe", "deno"):
            label = QLabel(f"{name}: pendiente")
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.versions[name] = label
            layout.addWidget(label)
        layout.addStretch()
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.check_versions()

    def browse(self, field):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar ejecutable", field.text())
        if path:
            field.setText(path)

    def overrides(self):
        return {
            name: field.text().strip()
            for name, field in self.fields.items()
            if field.text().strip()
        }

    def check_versions(self):
        self.check.setEnabled(False)
        self.buttons.setEnabled(False)
        for name, label in self.versions.items():
            label.setText(f"{name}: comprobando…")
        self.worker = ToolWorker(self.overrides(), self)
        self.worker.result.connect(
            lambda name, value: self.versions[name].setText(f"{name}: {value}")
        )
        self.worker.finished.connect(self.check_finished)
        self.worker.start()

    def check_finished(self):
        self.worker.deleteLater()
        self.worker = None
        self.check.setEnabled(True)
        self.buttons.setEnabled(True)
        if self.close_when_done:
            super().reject()

    def reject(self):
        if self.worker is not None:
            self.close_when_done = True
            self.worker.requestInterruption()
            return
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            self.reject()
            event.ignore()
        else:
            event.accept()


def show_formats(metadata, parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Formatos disponibles")
    dialog.resize(740, 470)
    layout = QVBoxLayout(dialog)
    title = QLabel(str(metadata.get("title", "Vídeo")))
    title.setTextFormat(Qt.TextFormat.PlainText)
    title.setWordWrap(True)
    layout.addWidget(title)
    note = QLabel(
        "Resoluciones ofrecidas por el vídeo. La descarga elegirá la mejor dentro del límite indicado.\n"
        "El perfil MP4 compatible solo elige vídeo H.264; puede ofrecer menos resoluciones."
    )
    note.setWordWrap(True)
    layout.addWidget(note)
    formats = metadata.get("formats", [])
    rows = set()
    for fmt in formats:
        if not isinstance(fmt, dict) or fmt.get("vcodec") in (None, "none"):
            continue
        rows.add(
            (
                str(fmt.get("height") or "—"),
                str(fmt.get("ext") or "—"),
                str(fmt.get("vcodec") or "—"),
                str(fmt.get("fps") or "—"),
            )
        )
    table = QTableWidget(len(rows), 4)
    table.setHorizontalHeaderLabels(["Altura (p)", "Contenedor", "Códec de vídeo", "FPS"])
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    for row, values in enumerate(
        sorted(rows, key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=True)
    ):
        for column, value in enumerate(values):
            table.setItem(row, column, QTableWidgetItem(value))
    layout.addWidget(table)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.button(QDialogButtonBox.StandardButton.Close).setText("Cerrar")
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    dialog.exec()
