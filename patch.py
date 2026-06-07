import os
import re

with open("E:/vv/mongle-sticker/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
content = content.replace(
    "from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer, QUrl",
    "from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer, QUrl, QAbstractNativeEventFilter"
)
content = content.replace(
    "QSlider)",
    "QSlider, QCheckBox, QFontDialog)"
)
content = content.replace(
    "from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QDesktopServices",
    "from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QDesktopServices, QFont"
)

# 2. Global Hotkey Filter & APP_VERSION
filter_code = """
import ctypes
import ctypes.wintypes
import threading
import urllib.request
import json

APP_VERSION = "v1.1"
WM_HOTKEY = 0x0312

class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG" or eventType == b"windows_dispatcher_MSG":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self.controller.toggle_boss_key()
                return True, 0
        return False, 0
"""
content = content.replace("CONFIG_FILE = os.path.join(BASE_DIR, \"config.json\")", "CONFIG_FILE = os.path.join(BASE_DIR, \"config.json\")\n" + filter_code)

# 3. get_default_config
content = content.replace(
    '"opacity": 90,',
    '"opacity": 90,\n                "use_markdown": False,\n                "font_family": "Malgun Gothic",\n                "font_size": 15,\n                "on_top": False,'
)

# 4. StickerDetailDialog UI
markdown_and_font_ui = """
        # Font Settings
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("폰트 설정:"))
        self.font_btn = QPushButton("글꼴 변경")
        self.font_btn.clicked.connect(self.change_font)
        font_layout.addWidget(self.font_btn)
        font_layout.addStretch()
        frame_layout.addLayout(font_layout)
        
        # Markdown Settings
        self.md_cb = QCheckBox("마크다운(Markdown) 렌더링 사용")
        self.md_cb.setChecked(self.memo_data.get("use_markdown", False))
        self.md_cb.stateChanged.connect(self.change_markdown)
        frame_layout.addWidget(self.md_cb)
"""
content = content.replace(
    "        preview_label = QLabel(\"원본 파일 내용 확인 및 미리보기 (Preview)\")",
    markdown_and_font_ui + "\n        preview_label = QLabel(\"원본 파일 내용 확인 및 미리보기 (Preview)\")"
)

markdown_methods = """
    def change_markdown(self, state):
        self.memo_data["use_markdown"] = bool(state)
        self.controller.refresh_sticker_content(self.memo_data["id"])

    def change_font(self):
        current_font = QFont(self.memo_data.get("font_family", "Malgun Gothic"), self.memo_data.get("font_size", 15))
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.memo_data["font_family"] = font.family()
            self.memo_data["font_size"] = font.pointSize()
            self.controller.refresh_sticker_style(self.memo_data["id"])

    def change_lines(self, text):"""
content = content.replace("    def change_lines(self, text):", markdown_methods)

# 5. MemoWidget UI (Pin) and apply_pin_state
pin_ui = """
        self.on_top = self.memo_data.get("on_top", False)
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0,0,0,0)
        top_layout.addStretch()
        self.pin_btn = QPushButton("📌" if self.on_top else "📎")
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setToolTip("항상 위로 고정 (Pin)")
        self.pin_btn.setStyleSheet("QPushButton { background: transparent; border: none; font-size: 14px; } QPushButton:hover { background: rgba(255,182,193, 100); border-radius: 12px; }")
        self.pin_btn.clicked.connect(self.toggle_pin)
        top_layout.addWidget(self.pin_btn)
        
        frame_layout.addLayout(top_layout)
        frame_layout.addWidget(self.text_edit)
"""
content = content.replace("        frame_layout.addWidget(self.text_edit)", pin_ui)

pin_methods = """
    def toggle_pin(self):
        self.on_top = not self.on_top
        self.memo_data["on_top"] = self.on_top
        self.pin_btn.setText("📌" if self.on_top else "📎")
        self.apply_pin_state()
        self.show()

    def apply_pin_state(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags |= Qt.WindowType.WindowStaysOnBottomHint
        self.setWindowFlags(flags)

    def set_edit_mode(self, enabled):"""
content = content.replace("    def set_edit_mode(self, enabled):", pin_methods)

content = content.replace(
    "        self.setWindowFlags(\n            Qt.WindowType.FramelessWindowHint | \n            Qt.WindowType.WindowStaysOnBottomHint | \n            Qt.WindowType.Tool\n        )",
    "        self.on_top = memo_data.get(\"on_top\", False)\n        self.apply_pin_state()"
)

# 6. MemoWidget Font updates
content = content.replace(
    "font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;",
    "font-family: '{self.memo_data.get('font_family', 'Malgun Gothic')}';"
)
content = content.replace(
    "font-size: 15px;",
    "font-size: {self.memo_data.get('font_size', 15)}px;"
)

# 7. MemoWidget Markdown updates
load_memo_replacement = """
            if self.memo_data.get("use_markdown", False):
                self.text_edit.setMarkdown(filtered_content)
            else:
                self.text_edit.setPlainText(filtered_content)
"""
content = content.replace("            self.text_edit.setPlainText(filtered_content)", load_memo_replacement)

# 8. AppController updates
app_controller_additions = """    def __init__(self, app):
        self.app = app
        self.config = load_config()
        self.widgets = {}  # id -> MemoWidget
        self.boss_key_active = False
        
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), app)
        self.tray_icon.setToolTip("몽글몽글 스티커")
        self.setup_tray_menu()
        
        self.settings_window = SettingsWindow(self)
        
        for memo_data in self.config.get("memos", []):
            self.spawn_sticker(memo_data, edit_mode=False)
            
        self.check_updates()

    def toggle_boss_key(self):
        self.boss_key_active = not self.boss_key_active
        for w in self.widgets.values():
            if self.boss_key_active:
                w.hide()
            else:
                w.show()

    def check_updates(self):
        def worker():
            try:
                req = urllib.request.Request("https://api.github.com/repos/lpaiu-cs/mongle-sticker/releases/latest")
                req.add_header("User-Agent", "MongleSticker")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read())
                    latest_tag = data.get("tag_name", "")
                    if latest_tag and latest_tag != APP_VERSION:
                        self.release_url = data.get("html_url", "")
                        QTimer.singleShot(2000, lambda: self.tray_icon.showMessage(
                            "업데이트 알림",
                            f"새로운 몽글몽글 스티커 {latest_tag} 버전이 출시되었습니다! 클릭해서 다운로드하세요.",
                            QSystemTrayIcon.MessageIcon.Information,
                            5000
                        ))
                        try: self.tray_icon.messageClicked.disconnect()
                        except Exception: pass
                        self.tray_icon.messageClicked.connect(self.open_update_url)
            except Exception as e:
                print("Update check failed:", e)
        threading.Thread(target=worker, daemon=True).start()

    def open_update_url(self):
        if hasattr(self, "release_url"):
            QDesktopServices.openUrl(QUrl(self.release_url))"""
content = re.sub(r"    def __init__\(self, app\):.*?(?=\n    def spawn_sticker)", app_controller_additions, content, flags=re.DOTALL)

# 9. Main hotkey registration
main_additions = """    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    controller = AppController(app)
    
    # Register Global Hotkey Filter
    hotkey_filter = GlobalHotkeyFilter(controller)
    app.installNativeEventFilter(hotkey_filter)
    
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    VK_M = 0x4D
    try:
        ctypes.windll.user32.RegisterHotKey(None, 1, MOD_ALT | MOD_CONTROL, VK_M)
    except Exception as e:
        print("Hotkey registration failed:", e)
    
    app_icon = create_tray_icon()
    app.setWindowIcon(app_icon)
    
    controller.show_settings()
    
    ret = app.exec()
    try:
        ctypes.windll.user32.UnregisterHotKey(None, 1)
    except: pass
    sys.exit(ret)"""
content = re.sub(r"    app = QApplication\(sys.argv\).*?sys.exit\(app.exec\(\)\)", main_additions, content, flags=re.DOTALL)

with open("E:/vv/mongle-sticker/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Patch applied successfully.")
