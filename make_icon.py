import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from main import create_tray_icon

app = QApplication(sys.argv)
icon = create_tray_icon()
# Windows Explorer prefers 256x256 for the main executable icon
pixmap = icon.pixmap(256, 256)
pixmap.save("icon.ico", "ICO")
print("High-res icon.ico created!")
