from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


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
