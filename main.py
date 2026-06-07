import sys
import os
import json
import uuid
import ctypes
import winreg
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QSystemTrayIcon, QMenu, 
                             QGraphicsDropShadowEffect, QFrame,
                             QLabel, QLineEdit, QPushButton, QFileDialog,
                             QScrollArea, QSizeGrip, QMessageBox, QDialog, QSlider)
from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QDesktopServices

APP_NAME = "MongleSticker"
if sys.platform == 'win32':
    appdata_path = os.path.join(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', os.path.expanduser('~'))), APP_NAME)
else:
    appdata_path = os.path.join(os.path.expanduser('~'), f'.{APP_NAME.lower()}')

os.makedirs(appdata_path, exist_ok=True)
BASE_DIR = appdata_path
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def get_default_config():
    default_txt = os.path.join(BASE_DIR, "memo.txt")
    if not os.path.exists(default_txt):
        with open(default_txt, "w", encoding="utf-8") as f:
            f.write("환영합니다! 몽글몽글 메모 스티커입니다.\n\n이 창의 텍스트는 드래그해서 복사할 수 있지만, 수정은 직접 할 수 없습니다.\n내용을 수정하려면 작업 표시줄 우측 하단의 \n트레이 아이콘을 우클릭하여 '기본 메모 파일 열기'를 누르거나,\n설정 창에서 '📝 열기' 버튼을 클릭하세요!\n\n파일을 저장하면 이 화면에 즉시 반영됩니다. 🌸")
            
    return {
        "memos": [
            {
                "id": str(uuid.uuid4()),
                "memo_file": default_txt,
                "x": 100,
                "y": 100,
                "w": 320,
                "h": 400,
                "color": "#FFF0F5",
                "opacity": 95,
                "line_range": "all"
            }
        ]
    }

def check_autostart():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "MongleMemoSticker"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def set_autostart(enable=True):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "MongleMemoSticker"
    
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print("Autostart error:", e)
        return False

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "memos" not in config:
                    return get_default_config()
                
                # 마이그레이션: 이전 버전 설정 파일에 누락된 필드 채우기
                for m in config["memos"]:
                    if "color" not in m: m["color"] = "#FFF0F5"
                    if "opacity" not in m: m["opacity"] = 95
                    if "line_range" not in m: m["line_range"] = "all"
                    
                return config
        except:
            pass
    return get_default_config()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def filter_lines(content, line_range):
    if not line_range or line_range.strip().lower() == "all":
        return content
    
    lines = content.split('\n')
    try:
        line_range = line_range.strip()
        if '-' in line_range:
            parts = line_range.split('-')
            start = int(parts[0]) if parts[0] else 1
            end = int(parts[1]) if parts[1] else len(lines)
            
            # 1-based index to 0-based index
            start_idx = max(0, start - 1)
            end_idx = min(len(lines), end)
            return '\n'.join(lines[start_idx:end_idx])
        else:
            idx = int(line_range)
            if 0 < idx <= len(lines):
                return lines[idx - 1]
            else:
                return ""
    except Exception:
        # 문법 오류 등이 발생하면 전체 반환
        return content


class CustomConfirmDialog(QDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: #FFF0F5;
                border-radius: 15px;
                border: 2px solid #FFE4E1;
            }
            QLabel {
                color: #5d4037;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                font-size: 14px;
                border: none;
            }
            QPushButton {
                background-color: white;
                color: #5d4037;
                border: 1px solid #FFE4E1;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFE4E1;
            }
            QPushButton#YesBtn {
                background-color: #ff8a80;
                color: white;
                border: none;
            }
            QPushButton#YesBtn:hover {
                background-color: #ff5252;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        self.frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        frame_layout.addWidget(title_label)
        
        msg_label = QLabel(message)
        frame_layout.addWidget(msg_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        no_btn = QPushButton("취소")
        no_btn.clicked.connect(self.reject)
        btn_layout.addWidget(no_btn)
        
        yes_btn = QPushButton("삭제")
        yes_btn.setObjectName("YesBtn")
        yes_btn.clicked.connect(self.accept)
        btn_layout.addWidget(yes_btn)
        
        frame_layout.addLayout(btn_layout)
        layout.addWidget(self.frame)

class StickerDetailDialog(QDialog):
    def __init__(self, memo_data, controller, parent=None):
        super().__init__(parent)
        self.memo_data = memo_data
        self.controller = controller
        
        self.memo_file = self.memo_data.get("memo_file", "")
        self.file_lines = []
        if self.memo_file and os.path.exists(self.memo_file):
            try:
                with open(self.memo_file, "r", encoding="utf-8") as f:
                    self.file_lines = f.read().split('\n')
            except Exception:
                pass
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(450, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #FFF0F5;
                border-radius: 15px;
                border: 2px solid #FFE4E1;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                color: #5d4037;
            }
            QLabel {
                border: none;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #FFE4E1;
                border-radius: 5px;
                background-color: white;
            }
            QPushButton {
                background-color: white;
                color: #5d4037;
                border: 1px solid #FFE4E1;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFE4E1;
            }
            QPushButton#PrimaryBtn {
                background-color: #FFB6C1;
                color: white;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #FF9AA2;
            }
        """)
        self.frame.setObjectName("MainFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 3)
        self.frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("⚙️ 스티커 상세 설정")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        frame_layout.addWidget(title_label)
        
        # Color Palette
        frame_layout.addWidget(QLabel("🎨 배경 색상"))
        colors = [
            ("#FFF0F5", "핑크"), ("#FFFACD", "옐로우"), 
            ("#F0F8FF", "블루"), ("#F0FFF0", "그린"), 
            ("#E6E6FA", "퍼플"), ("#F5F5F5", "그레이")
        ]
        color_layout = QHBoxLayout()
        for hex_code, name in colors:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(f"background-color: {hex_code}; border-radius: 15px; border: 1px solid #ccc;")
            btn.setToolTip(name)
            # lambda 캡처 우회
            btn.clicked.connect(lambda checked, h=hex_code: self.change_color(h))
            color_layout.addWidget(btn)
        color_layout.addStretch()
        frame_layout.addLayout(color_layout)
        
        # Opacity
        frame_layout.addWidget(QLabel("💧 투명도 (10% ~ 100%)"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(self.memo_data.get("opacity", 95))
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        frame_layout.addWidget(self.opacity_slider)
        
        # Line Range
        frame_layout.addWidget(QLabel("📄 표시할 줄 (Lines)"))
        desc = QLabel("예) 'all' (전체), '3' (3번째 줄만), '1-5' (1~5번째 줄)")
        desc.setStyleSheet("font-weight: normal; color: #888; font-size: 11px;")
        frame_layout.addWidget(desc)
        
        self.line_input = QLineEdit()
        self.line_input.setText(str(self.memo_data.get("line_range", "all")))
        self.line_input.textChanged.connect(self.change_lines)
        frame_layout.addWidget(self.line_input)
        
        preview_label = QLabel("원본 파일 내용 확인 및 미리보기 (Preview)")
        preview_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #5d4037; margin-top: 10px;")
        frame_layout.addWidget(preview_label)
        
        self.preview_box = QTextEdit()
        self.preview_box.setReadOnly(True)
        self.preview_box.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.preview_box.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview_box.setFixedHeight(180)
        self.preview_box.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #FFE4E1;
                border-radius: 8px;
                color: #555;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 6px 4px 6px 4px;
            }
            QScrollBar:horizontal, QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
                background: #ffb6c1;
                min-width: 20px;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                width: 0px;
                height: 0px;
            }
        """)
        frame_layout.addWidget(self.preview_box)
        
        frame_layout.addStretch()
        
        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("닫기")
        close_btn.setObjectName("PrimaryBtn")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        frame_layout.addLayout(btn_layout)
        layout.addWidget(self.frame)
        
        self.update_preview(self.line_input.text())
        
    def change_color(self, hex_code):
        self.memo_data["color"] = hex_code
        self.controller.refresh_sticker_style(self.memo_data["id"])
        
    def change_opacity(self, value):
        self.memo_data["opacity"] = value
        self.controller.refresh_sticker_style(self.memo_data["id"])
        
    def change_lines(self, text):
        self.memo_data["line_range"] = text
        self.update_preview(text)
        self.controller.refresh_sticker_content(self.memo_data["id"])

    def update_preview(self, line_range):
        if not self.file_lines:
            self.preview_box.setHtml("<span style='color:#888;'>파일 내용이 없거나 선택되지 않았습니다.</span>")
            return
            
        total = len(self.file_lines)
        line_range_str = line_range.strip().lower()
        selected = set()
        
        if not line_range_str or line_range_str == "all":
            selected = set(range(total))
        else:
            try:
                if '-' in line_range_str:
                    parts = line_range_str.split('-')
                    start = int(parts[0]) if parts[0] else 1
                    end = int(parts[1]) if parts[1] else total
                    start_idx = max(0, start - 1)
                    end_idx = min(total, end)
                    selected.update(range(start_idx, end_idx))
                else:
                    idx = int(line_range_str)
                    if 0 < idx <= total:
                        selected.add(idx - 1)
            except Exception:
                pass
                
        html = "<div style='white-space: pre; font-family: Consolas, monospace; line-height: 1.4;'>"
        fm = self.preview_box.fontMetrics()
        max_text_width = 290  # Safe margin subtracting padding, scrollbar, and line number area
        total_digits = len(str(total))
        
        for i, line in enumerate(self.file_lines):
            display_line = fm.elidedText(line, Qt.TextElideMode.ElideRight, max_text_width)
                
            safe_line = display_line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not safe_line:
                safe_line = " " # Ensure empty lines render correctly
            
            line_num = str(i + 1).rjust(total_digits, ' ')
            
            if i in selected:
                # Highlighted selected line
                html += f"<span style='background-color: #FFF0F5; color: #ff5252; font-weight: bold;'>{line_num} | </span>"
                html += f"<span style='background-color: #FFF0F5; color: #333; font-weight: bold;'>{safe_line}</span><br>"
            else:
                # Unselected line
                html += f"<span style='color: #ccc;'>{line_num} | </span>"
                html += f"<span style='color: #888;'>{safe_line}</span><br>"
                
        html += "</div>"
        self.preview_box.setHtml(html)


class MemoWidget(QWidget):
    def __init__(self, memo_data):
        super().__init__()
        self.memo_data = memo_data
        self.memo_file = memo_data["memo_file"]
        self.memo_dir = os.path.dirname(self.memo_file) if self.memo_file else ""
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnBottomHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setGeometry(memo_data.get("x", 100), memo_data.get("y", 100), 
                         memo_data.get("w", 320), memo_data.get("h", 400))
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)
        
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFrameStyle(QFrame.Shape.NoFrame)
        
        self.size_grip = QSizeGrip(self.frame)
        self.size_grip.setFixedSize(16, 16)
        
        frame_layout.addWidget(self.text_edit)
        
        main_layout.addWidget(self.frame)
        
        self.edit_mode = False
        self.update_style()
        self.load_memo()
        
        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.on_file_changed)
        self.watcher.directoryChanged.connect(self.on_dir_changed)
        self.setup_watcher()

    def update_style(self):
        # 파싱 컬러/투명도
        hex_col = self.memo_data.get("color", "#FFF0F5").lstrip('#')
        if len(hex_col) != 6: hex_col = "FFF0F5"
        
        r, g, b = int(hex_col[0:2], 16), int(hex_col[2:4], 16), int(hex_col[4:6], 16)
        opacity = self.memo_data.get("opacity", 95)
        alpha = int(255 * (opacity / 100.0))
        
        bg_rgba = f"rgba({r}, {g}, {b}, {alpha})"
        border_rgba = f"rgba({max(0, r-30)}, {max(0, g-30)}, {max(0, b-30)}, 200)"
        dash_rgba = f"rgba({max(0, r-60)}, {max(0, g-60)}, {max(0, b-60)}, 255)"
        
        if self.edit_mode:
            self.frame.setStyleSheet(f"""
                QFrame#MainFrame {{
                    background-color: {bg_rgba};
                    border-radius: 20px;
                    border: 2px dashed {dash_rgba};
                }}
            """)
            self.size_grip.show()
        else:
            self.frame.setStyleSheet(f"""
                QFrame#MainFrame {{
                    background-color: {bg_rgba};
                    border-radius: 20px;
                    border: 2px solid {border_rgba};
                }}
            """)
            self.size_grip.hide()
            
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                color: #5d4037;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                font-size: 15px;
                line-height: 1.6;
                selection-background-color: #ffb6c1;
                selection-color: white;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {dash_rgba};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        self.update_style()

    def update_file(self, new_file):
        self.memo_data["memo_file"] = new_file
        self.memo_file = new_file
        self.memo_dir = os.path.dirname(new_file) if new_file else ""
        self.setup_watcher()
        self.load_memo()

    def setup_watcher(self):
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())
        if self.watcher.directories():
            self.watcher.removePaths(self.watcher.directories())
            
        if self.memo_dir and os.path.exists(self.memo_dir):
            self.watcher.addPath(self.memo_dir)
        if self.memo_file and os.path.exists(self.memo_file):
            self.watcher.addPath(self.memo_file)

    def load_memo(self):
        if not self.memo_file:
            self.text_edit.setPlainText("메모 파일이 설정되지 않았습니다.")
            return
            
        try:
            if not os.path.exists(self.memo_file):
                os.makedirs(self.memo_dir, exist_ok=True)
                with open(self.memo_file, "w", encoding="utf-8") as f:
                    f.write("새로운 스티커입니다!\n\n여기에 메모를 작성하세요.")
                    
            with open(self.memo_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Filter by lines
            line_range = self.memo_data.get("line_range", "all")
            filtered_content = filter_lines(content, line_range)
            
            self.text_edit.setPlainText(filtered_content)
        except Exception as e:
            pass

    def on_file_changed(self, path):
        QTimer.singleShot(100, self.load_memo)
        
    def on_dir_changed(self, path):
        if self.memo_file and os.path.exists(self.memo_file):
            if self.memo_file not in self.watcher.files():
                self.watcher.addPath(self.memo_file)
            QTimer.singleShot(100, self.load_memo)

    def mousePressEvent(self, event):
        if self.edit_mode and event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.edit_mode and event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.size_grip.move(self.frame.width() - 18, self.frame.height() - 18)

class StickerRow(QFrame):
    def __init__(self, memo_data, parent_window):
        super().__init__()
        self.memo_data = memo_data
        self.parent_window = parent_window
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #FFE4E1;
                border-radius: 8px;
            }
            QLabel { border: none; font-size: 13px; font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 8px;
                color: #333;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton#RemoveBtn {
                background-color: #ffebee;
                color: #c62828;
                border-color: #ffcdd2;
            }
            QPushButton#RemoveBtn:hover {
                background-color: #ffcdd2;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        self.name_label = QLabel(os.path.basename(memo_data["memo_file"]) if memo_data["memo_file"] else "선택 없음")
        self.name_label.setStyleSheet("font-weight: bold; color: #5d4037;")
        layout.addWidget(self.name_label, 1)
        
        detail_btn = QPushButton("⚙️ 상세")
        detail_btn.setToolTip("색상, 투명도, 줄 설정")
        detail_btn.clicked.connect(self.open_detail)
        layout.addWidget(detail_btn)
        
        open_btn = QPushButton("📝 열기")
        open_btn.setToolTip("연결된 텍스트 파일 열기")
        open_btn.clicked.connect(self.open_file)
        layout.addWidget(open_btn)
        
        change_btn = QPushButton("📂 변경")
        change_btn.setToolTip("연결할 텍스트 파일 변경")
        change_btn.clicked.connect(self.change_file)
        layout.addWidget(change_btn)
        
        remove_btn = QPushButton("❌")
        remove_btn.setObjectName("RemoveBtn")
        remove_btn.setToolTip("바탕화면에서 스티커 제거")
        remove_btn.clicked.connect(self.remove_sticker)
        layout.addWidget(remove_btn)

    def open_detail(self):
        dialog = StickerDetailDialog(self.memo_data, self.parent_window.controller, self.parent_window)
        dialog.exec()

    def open_file(self):
        file_path = self.memo_data.get("memo_file", "")
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def change_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "메모 파일 선택", BASE_DIR, "Text Files (*.txt);;All Files (*)")
        if file_path:
            file_path = os.path.normpath(file_path)
            self.name_label.setText(os.path.basename(file_path))
            self.parent_window.controller.update_sticker_file(self.memo_data["id"], file_path)

    def remove_sticker(self):
        dialog = CustomConfirmDialog("스티커 삭제", "이 스티커를 화면에서 완전히 지우시겠습니까?", self.parent_window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.parent_window.remove_row(self)

class SettingsWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(480, 500)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        
        self.frame = QFrame()
        self.frame.setObjectName("MainFrame")
        self.frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #FFF0F5;
                border-radius: 20px;
                border: 2px solid #FFE4E1;
                font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
                color: #5d4037;
            }
            QLabel { border: none; }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QPushButton#PrimaryBtn {
                background-color: #FFB6C1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #FF9AA2;
            }
            QPushButton#AddBtn {
                background-color: white;
                color: #FFB6C1;
                border: 2px dashed #FFB6C1;
                border-radius: 8px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#AddBtn:hover {
                background-color: #FFF6F7;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self.frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.title_bar = QFrame()
        self.title_bar.setStyleSheet("background-color: transparent; border: none; border-bottom: 2px solid #FFE4E1;")
        self.title_bar.setFixedHeight(45)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("🌸 몽글몽글 스티커 설정창")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #5d4037;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ff8a80;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffebee;
                border-radius: 15px;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        self.title_bar.mousePressEvent = self.title_press
        self.title_bar.mouseMoveEvent = self.title_move
        
        main_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)
        content_layout.setSpacing(10)
        
        header = QLabel("📌 활성화된 스티커 목록")
        header.setStyleSheet("font-size: 15px; font-weight: bold;")
        content_layout.addWidget(header)
        
        desc = QLabel("💡 팁: '상세' 버튼을 눌러 스티커 색상과 투명도, 특정 줄을 설정해보세요.")
        desc.setStyleSheet("font-size: 12px; color: #8d6e63; margin-bottom: 5px;")
        content_layout.addWidget(desc)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        self.list_layout = QVBoxLayout(self.scroll_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(8)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.scroll_widget)
        content_layout.addWidget(self.scroll_area)
        
        add_btn = QPushButton("➕ 새 스티커 바탕화면에 추가")
        add_btn.setObjectName("AddBtn")
        add_btn.clicked.connect(self.add_new_sticker)
        content_layout.addWidget(add_btn)
        
        self.startup_btn = QPushButton()
        self.startup_btn.setFixedHeight(45)
        self.update_startup_btn_text()
        self.startup_btn.clicked.connect(self.toggle_startup)
        content_layout.addWidget(self.startup_btn)
        
        done_btn = QPushButton("✅ 설정 완료 및 모두 저장")
        done_btn.setObjectName("PrimaryBtn")
        done_btn.clicked.connect(self.close)
        content_layout.addWidget(done_btn)
        
        main_layout.addLayout(content_layout)
        outer_layout.addWidget(self.frame)
        
        self.rows = []

    def title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def load_list(self):
        for i in reversed(range(self.list_layout.count())): 
            widget_to_remove = self.list_layout.itemAt(i).widget()
            self.list_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        self.rows.clear()
        
        config = self.controller.config
        for memo_data in config.get("memos", []):
            row = StickerRow(memo_data, self)
            self.list_layout.addWidget(row)
            self.rows.append(row)

    def add_new_sticker(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "메모 파일 선택", BASE_DIR, "Text Files (*.txt);;All Files (*)")
        if not file_path:
            return
            
        file_path = os.path.normpath(file_path)
        new_id = str(uuid.uuid4())
        screen = QApplication.primaryScreen().geometry()
        memo_data = {
            "id": new_id,
            "memo_file": file_path,
            "x": screen.width() // 2 - 160,
            "y": screen.height() // 2 - 200,
            "w": 320,
            "h": 400,
            "color": "#FFF0F5",
            "opacity": 95,
            "line_range": "all"
        }
        self.controller.config["memos"].append(memo_data)
        self.controller.spawn_sticker(memo_data, edit_mode=True)
        self.load_list()

    def remove_row(self, row_widget):
        memo_id = row_widget.memo_data["id"]
        self.controller.config["memos"] = [m for m in self.controller.config["memos"] if m["id"] != memo_id]
        self.controller.destroy_sticker(memo_id)
        self.load_list()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_list()
        self.controller.set_all_edit_mode(True)

    def update_startup_btn_text(self):
        if check_autostart():
            self.startup_btn.setText("🚀 윈도우 시작 시 자동 실행: ON")
            self.startup_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e6f7ff;
                    border: 1px solid #91d5ff;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #096dd9;
                }
                QPushButton:hover {
                    background-color: #bae7ff;
                }
            """)
        else:
            self.startup_btn.setText("🚀 윈도우 시작 시 자동 실행: OFF")
            self.startup_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #d9d9d9;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #8c8c8c;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
            """)

    def toggle_startup(self):
        current = check_autostart()
        set_autostart(not current)
        self.update_startup_btn_text()

    def closeEvent(self, event):
        self.controller.save_all_geometries()
        self.controller.set_all_edit_mode(False)
        event.accept()

class AppController:
    def __init__(self, app):
        self.app = app
        self.config = load_config()
        self.widgets = {}  # id -> MemoWidget
        
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), app)
        self.tray_icon.setToolTip("몽글몽글 스티커")
        self.setup_tray_menu()
        
        self.settings_window = SettingsWindow(self)
        
        for memo_data in self.config.get("memos", []):
            self.spawn_sticker(memo_data, edit_mode=False)

    def spawn_sticker(self, memo_data, edit_mode=False):
        w = MemoWidget(memo_data)
        w.set_edit_mode(edit_mode)
        w.show()
        self.widgets[memo_data["id"]] = w

    def destroy_sticker(self, memo_id):
        if memo_id in self.widgets:
            self.widgets[memo_id].close()
            del self.widgets[memo_id]

    def update_sticker_file(self, memo_id, new_file):
        if memo_id in self.widgets:
            self.widgets[memo_id].update_file(new_file)
            
    def refresh_sticker_style(self, memo_id):
        if memo_id in self.widgets:
            self.widgets[memo_id].update_style()
            
    def refresh_sticker_content(self, memo_id):
        if memo_id in self.widgets:
            self.widgets[memo_id].load_memo()

    def set_all_edit_mode(self, enabled):
        for w in self.widgets.values():
            w.set_edit_mode(enabled)

    def save_all_geometries(self):
        for memo_id, w in self.widgets.items():
            geo = w.geometry()
            for memo_data in self.config["memos"]:
                if memo_data["id"] == memo_id:
                    memo_data["x"] = geo.x()
                    memo_data["y"] = geo.y()
                    memo_data["w"] = geo.width()
                    memo_data["h"] = geo.height()
        save_config(self.config)

    def show_settings(self):
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def setup_tray_menu(self):
        menu = QMenu()
        open_action = menu.addAction("📝 기본 메모 파일 열기")
        open_action.triggered.connect(self.open_default_memo)
        menu.addSeparator()
        settings_action = menu.addAction("⚙️ 스티커 관리 / 크기 조절")
        settings_action.triggered.connect(self.show_settings)
        menu.addSeparator()
        exit_action = menu.addAction("❌ 프로그램 종료")
        exit_action.triggered.connect(self.app.quit)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def open_default_memo(self):
        if self.config.get("memos"):
            first_memo = self.config["memos"][0].get("memo_file")
            if first_memo and os.path.exists(first_memo):
                QDesktopServices.openUrl(QUrl.fromLocalFile(first_memo))

def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    painter.setBrush(QColor("#FFB6C1"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 16, 16)
    
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(16, 20, 32, 6, 3, 3)
    painter.drawRoundedRect(16, 32, 24, 6, 3, 3)
    painter.drawRoundedRect(16, 44, 32, 6, 3, 3)
    
    painter.end()
    return QIcon(pixmap)

def main():
    try:
        myappid = 'monglemongle.memosticker.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    app_icon = create_tray_icon()
    app.setWindowIcon(app_icon)
    
    controller = AppController(app)
    controller.show_settings()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
