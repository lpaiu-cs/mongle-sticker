import sys
from PyQt6.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class StickyNote(QWidget):
    def __init__(self):
        super().__init__()
        # Set flags: frameless, stays on bottom, and tool (hides from taskbar usually, or we can use subwindow)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnBottomHint | 
                            Qt.WindowType.Tool)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("This is a test memo.\nYou can select this text.\nBut it stays on bottom.")
        self.text_edit.setReadOnly(True)
        
        # Styling to make it look soft and fluffy
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 240, 245, 200); /* Lavender blush with some transparency */
                border-radius: 15px;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #333333;
                border: 2px solid rgba(255, 220, 230, 255);
            }
        """)

        layout.addWidget(self.text_edit)
        
        self.setGeometry(100, 100, 300, 300)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StickyNote()
    window.show()
    sys.exit(app.exec())
