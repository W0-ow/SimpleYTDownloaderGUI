STYLE = """
QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 13px; color: #dce5f1; }
QMainWindow, QDialog { background: #101722; }
QLabel#heading { font-size: 27px; font-weight: 700; color: #f3f7fc; }
QLabel#subheading { color: #9baec5; font-size: 13px; }
QLabel#section { color: #86a2c2; font-size: 11px; font-weight: 700; }
QLabel#notice { color: #b7c8dd; padding: 8px 0; }
QFrame#card { background: #172231; border: 1px solid #28384d; border-radius: 12px; }
QLineEdit, QPlainTextEdit, QComboBox {
    background: #101a28; border: 1px solid #354860; border-radius: 6px;
    padding: 9px; selection-background-color: #2865bd;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #5c9ffc; }
QComboBox:disabled, QLineEdit:disabled { color: #6e8096; border-color: #28384d; }
QComboBox { min-width: 115px; padding-right: 24px; }
QComboBox QAbstractItemView { background: #192638; selection-background-color: #2865bd; }
QPushButton { background: #24354a; border: 1px solid #354a63; border-radius: 6px; padding: 10px 15px; }
QPushButton:hover { background: #304762; border-color: #7091b7; }
QPushButton:pressed { background: #1c2c40; }
QPushButton#primary { background: #397ee8; border-color: #397ee8; color: white; font-weight: 600; }
QPushButton#primary:hover { background: #5092f4; }
QPushButton:disabled { color: #6e8096; background: #1a2635; border-color: #2a384a; }
QTableWidget { background: #121e2c; alternate-background-color: #172333; border: 1px solid #293c52; border-radius: 6px; gridline-color: #223448; selection-background-color: #26476c; }
QTableWidget::item { padding: 7px; }
QHeaderView::section { background: #1c2b3e; color: #a4bad3; border: none; padding: 10px; font-weight: 600; }
QProgressBar { border: none; border-radius: 5px; background: #26364a; text-align: center; min-height: 18px; }
QProgressBar::chunk { background: #3f86ec; border-radius: 5px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QToolTip { background: #22364e; color: white; border: 1px solid #56708f; padding: 6px; }
QScrollBar:vertical { background: #142030; width: 12px; }
QScrollBar::handle:vertical { background: #3a4f69; min-height: 25px; border-radius: 5px; }
"""
