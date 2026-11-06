import sys
import os
import zipfile
import shutil
import ctypes
from PyQt6.QtCore import (Qt, QPoint, QPropertyAnimation, QEasingCurve,
                          QSequentialAnimationGroup, QParallelAnimationGroup,
                          pyqtProperty, QTimer, QRectF, pyqtSignal, QObject, QEvent, QUrl)
from PyQt6.QtGui import (QFont, QColor, QMouseEvent, QPainter, QPainterPath, 
                         QRegion, QPen, QBrush, QFontMetrics, QPixmap, QTransform, QIcon)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QGraphicsOpacityEffect, QSizePolicy,
                             QHBoxLayout, QFrame, QScrollArea, QPushButton, QHBoxLayout,
                             QSlider)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

COLORS = {
    "dark_bg": "#0d0d0d",
    "medium_bg": "#1a1a1a",
    "light_bg": "#262626",
    "border": "#404040",
    "text_light": "#d8d8d8",
    "text_muted": "#888888",
    "accent_red": "#c62828",
    "accent_blue": "#1565c0",
    "accent_green": "#2e7d32",
    "white": "#c0c0c0",
    "artemis_gray": "#707070",
    "yellow": "#FFD700",
}

LIGHT_COLORS = {
    "dark_bg": "#e8e8e8",
    "medium_bg": "#d0d0d0",
    "light_bg": "#f8f8f8",
    "border": "#b0b0b0",
    "text_light": "#2a2a2a",
    "text_muted": "#555555",
    "white": "#1a1a1a",
    "artemis_gray": "#555555",
    "yellow": "#B8860B",
}

PROJECTS_FOLDER = "Projects"
PROJECT_DATA = {
    "Computer assembly": "Computer-Assembly.zip",
    "Artificial intelligence": "Artificial-intelligence.zip",
    "Artificial intelligence vk bot": "Artificial-intelligence-VK-bot.zip",
    "Notes": "Notes.zip",
    "Python compiler": "Python-Compiler.zip",
    "Youtube unblocking": "Youtube-unblocking.zip",
    "Snake": "Snake.zip",
    "Game for remodeling": "Game-for-remodeling.zip",
    "Connection": "Connection.zip",
    "System": "System.zip",
    "TG clothing bot": "TG-clothing-bot.zip",
}

PROJECT_DOWNLOAD_STATUS = {}

def set_taskbar_icon():
    if sys.platform == "win32":
        try:
            myappid = 'ARTEMIS.PROJECT.1.00'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Не удалось установить AppUserModelID: {e}")

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class SoundManager(QObject):
    """Проигрывание звуков (MP3) без блокировок."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = {}
        self._volume = 1.0
        self._muted = False

    def _get_player(self, key: str, file_path: str) -> QMediaPlayer:
        if key in self._players:
            return self._players[key]["player"]

        audio = QAudioOutput()
        audio.setVolume(0.0 if self._muted else float(self._volume))
        player = QMediaPlayer()
        player.setAudioOutput(audio)
        self._players[key] = {"player": player, "audio": audio, "path": file_path}
        return player

    
    def set_volume(self, volume: float):
        """volume: 0.0..1.0"""
        try:
            v = max(0.0, min(1.0, float(volume)))
        except Exception:
            v = 1.0
        self._volume = v
        if self._muted:
            return
        for item in self._players.values():
            try:
                item["audio"].setVolume(v)
            except Exception:
                pass

    def set_muted(self, muted: bool):
        self._muted = bool(muted)
        for item in self._players.values():
            try:
                item["audio"].setVolume(0.0 if self._muted else float(self._volume))
            except Exception:
                pass

    def is_muted(self) -> bool:
        return bool(self._muted)

    def play(self, key: str, file_path: str):
        try:
            if not file_path:
                return
            if not os.path.exists(file_path):
                return
            player = self._get_player(key, file_path)
            player.setSource(QUrl.fromLocalFile(file_path))
            player.setPosition(0)
            player.play()
        except Exception as e:
            print(f"Не удалось проиграть звук {file_path}: {e}")


def get_app_dir():
    """Папка приложения (рядом с exe, либо рядом со скриптом)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def projects_dir_path():
    return os.path.join(get_app_dir(), PROJECTS_FOLDER)

def ensure_projects_folder(create: bool = False):
    """
    Возвращает путь к Projects.
    ВАЖНО: папка НЕ создаётся при запуске, только если create=True (когда реально скачали проект).
    """
    projects_path = projects_dir_path()
    if create and (not os.path.exists(projects_path)):
        os.makedirs(projects_path, exist_ok=True)
        print(f"Создана папка Projects: {projects_path}")
    return projects_path

def extract_project(item_name, projects_path):
    if item_name not in PROJECT_DATA:
        print(f"Проект {item_name} не найден")
        return None
    
    zip_filename = PROJECT_DATA[item_name]
    zip_path = get_resource_path(zip_filename)
    
    if not os.path.exists(zip_path):
        print(f"Архив {zip_filename} не найден")
        return None
    
    if not validate_zip_integrity(zip_path):
        print(f"Архив {zip_filename} поврежден")
        return None
    
    project_folder_name = zip_filename.replace('.zip', '')
    extract_path = os.path.join(projects_path, project_folder_name)
    
    if os.path.exists(extract_path):
        print(f"Проект {item_name} уже распакован в {extract_path}")
        return extract_path
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if zip_filename == "TG-clothing-bot.zip":
                file_list = zip_ref.namelist()
                print(f"Содержимое архива TG-clothing-bot: {file_list}")
                
                os.makedirs(extract_path, exist_ok=True)
                
                for file in file_list:
                    zip_ref.extract(file, extract_path)
                    print(f"Извлечен файл: {file}")
                
                extracted_files = os.listdir(extract_path)
                print(f"Извлеченные файлы: {extracted_files}")
                
                required_files = ["main.py", "requirements.txt", "config.py"]
                for req_file in required_files:
                    req_path = os.path.join(extract_path, req_file)
                    if os.path.exists(req_path):
                        print(f"Найден обязательный файл: {req_file}")
                    else:
                        for root, dirs, files in os.walk(extract_path):
                            if req_file in files:
                                print(f"Найден файл {req_file} в подпапке: {root}")
                                break
                        else:
                            print(f"Предупреждение: файл {req_file} не найден")
            else:
                zip_ref.extractall(extract_path)
            
            print(f"Проект {item_name} распакован в {extract_path}")
            
            PROJECT_DOWNLOAD_STATUS[item_name] = True
            
            return extract_path
    except Exception as e:
        print(f"Ошибка при распаковке {item_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_project_folder(item_name):
    projects_path = ensure_projects_folder(create=False)

    if item_name not in PROJECT_DATA:
        return projects_path

    zip_filename = PROJECT_DATA[item_name]
    project_folder_name = zip_filename.replace('.zip', '')
    project_path = os.path.join(projects_path, project_folder_name)

    if os.path.exists(project_path) and os.path.isdir(project_path):
        PROJECT_DOWNLOAD_STATUS[item_name] = True
        return project_path

    PROJECT_DOWNLOAD_STATUS[item_name] = False
    return project_path

    
    zip_filename = PROJECT_DATA[item_name]
    project_folder_name = zip_filename.replace('.zip', '')
    project_path = os.path.join(projects_path, project_folder_name)
    
    if os.path.exists(project_path):
        PROJECT_DOWNLOAD_STATUS[item_name] = True
        return project_path
    
    if item_name in PROJECT_DOWNLOAD_STATUS and PROJECT_DOWNLOAD_STATUS[item_name]:
        return project_path
    
    return projects_path

def is_project_downloaded(item_name):
    projects_path = ensure_projects_folder(create=False)

    if item_name not in PROJECT_DATA:
        PROJECT_DOWNLOAD_STATUS[item_name] = False
        return False

    zip_filename = PROJECT_DATA[item_name]
    project_folder_name = zip_filename.replace('.zip', '')
    project_path = os.path.join(projects_path, project_folder_name)

    ok = False
    if os.path.exists(project_path) and os.path.isdir(project_path):
        try:
            ok = len(os.listdir(project_path)) > 0
        except Exception:
            ok = False

    PROJECT_DOWNLOAD_STATUS[item_name] = ok
    return ok

    
    zip_filename = PROJECT_DATA[item_name]
    project_folder_name = zip_filename.replace('.zip', '')
    project_path = os.path.join(projects_path, project_folder_name)
    
    if os.path.exists(project_path):
        if os.path.isdir(project_path) and os.listdir(project_path):
            PROJECT_DOWNLOAD_STATUS[item_name] = True
            return True
    
    PROJECT_DOWNLOAD_STATUS[item_name] = False
    return False

def open_project_folder(item_name):
    project_path = get_project_folder(item_name)
    
    if os.path.exists(project_path):
        try:
            if sys.platform == "win32":
                os.startfile(project_path)
            elif sys.platform == "darwin":
                os.system(f'open "{project_path}"')
            else:
                os.system(f'xdg-open "{project_path}"')
            print(f"Открыта папка: {project_path}")
            return True
        except Exception as e:
            print(f"Ошибка при открытии папки: {e}")
            return False
    else:
        print(f"Папка проекта не найдена: {project_path}")
        return False

def validate_zip_integrity(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            bad_file = zip_ref.testzip()
            if bad_file:
                print(f"Поврежденный файл в архиве: {bad_file}")
                return False
            return True
    except Exception as e:
        print(f"Ошибка проверки архива: {e}")
        return False

class ColorAnimationWidget(QWidget):
    bg_color_changed = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_color = QColor(COLORS["dark_bg"])
        self._animation = QPropertyAnimation(self, b"bg_color", self)
        self._animation.setDuration(500)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    @pyqtProperty(QColor)
    def bg_color(self):
        return self._bg_color
    
    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value
        self.bg_color_changed.emit(value)
        self.update()
    
    def animate_to_color(self, target_color_hex):
        target_color = QColor(target_color_hex)
        if self._bg_color != target_color:
            self._animation.stop()
            self._animation.setStartValue(self._bg_color)
            self._animation.setEndValue(target_color)
            self._animation.start()
    
    def set_color_immediately(self, color_hex):
        self._animation.stop()
        self.bg_color = QColor(color_hex)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())

class DragBarWithTriangles(ColorAnimationWidget):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_color_immediately(COLORS["accent_red"])
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        triangle_color = QColor("#ffffff")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(triangle_color))
        
        height = self.height()
        triangle_size = 4
        triangle_y = height // 2 - triangle_size // 2
        
        left_x = 10
        self.draw_triangle(painter, left_x, triangle_y, triangle_size)
        
        center_x = self.width() // 2 - triangle_size // 2
        self.draw_triangle(painter, center_x, triangle_y, triangle_size)
        
        right_x = self.width() - 10 - triangle_size
        self.draw_triangle(painter, right_x, triangle_y, triangle_size)
    
    def draw_triangle(self, painter, x, y, size):
        points = [
            QPoint(x, y),
            QPoint(x + size, y),
            QPoint(x + size // 2, y + size)
        ]
        painter.drawPolygon(points)
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class SlideDownPanel(QWidget):
    closed = pyqtSignal()
    
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.drag_start = None
        self.is_dragging = False
        self.is_installed = False
        self.current_item_name = ""
        self.dark_mode = dark_mode
        self.color_animations = {}
        self.setup_ui()
        self.update_all_styles(self.dark_mode, animate=False)

        self._state_timer = QTimer(self)
        self._state_timer.setInterval(900)
        self._state_timer.timeout.connect(self.refresh_download_state)
        
    def setup_ui(self):
        self.setFixedHeight(int(self.parent().height() * 0.65))
        self.setMinimumWidth(self.parent().width())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.drag_bar = DragBarWithTriangles()
        self.drag_bar.clicked.connect(self.close_panel)
        main_layout.addWidget(self.drag_bar)
        
        self.content_widget = QWidget()
        self.content_widget.setObjectName("content_widget")
        self.update_content_widget_style(animate=False)
        
        main_layout.addWidget(self.content_widget)
        
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(25, 20, 25, 20)
        content_layout.setSpacing(15)
        
        self.title_label = QLabel()
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.update_title_label_style(animate=False)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setStyleSheet("""
            QLabel {
                margin-bottom: 5px;
            }
        """)
        content_layout.addWidget(self.title_label)
        
        self.info_label = QLabel()
        self.info_label.setFont(QFont("Segoe UI", 10))
        self.info_label.setWordWrap(True)
        self.update_info_label_style(animate=False)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.info_label.setMinimumHeight(85)
        self.info_label.setMaximumHeight(100)
        
        description_container = QWidget()
        description_layout = QVBoxLayout(description_container)
        description_layout.setContentsMargins(0, 0, 0, 0)
        description_layout.addWidget(self.info_label)
        
        content_layout.addWidget(description_container, 1)
        
        details_widget = QWidget()
        details_layout = QHBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 10, 0, 0)
        details_layout.setSpacing(12)
        
        self.download_button = ActionButton("⬇️ Загрузить", COLORS["accent_red"])
        self.download_button.clicked.connect(self.on_download_clicked)
        self.download_button.setFixedHeight(36)
        details_layout.addWidget(self.download_button)
        
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        
        self.project_label = QLabel()
        self.project_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.update_project_label_style(animate=False)
        self.project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.project_label)
        
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.update_status_label_style(animate=False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.status_label)
        
        details_layout.addWidget(center_panel)
        details_layout.setStretch(1, 1)
        
        self.folder_button = ActionButton("📁 Файл", COLORS["border"])
        self.folder_button.clicked.connect(self.on_folder_clicked)
        self.folder_button.setFixedHeight(36)
        details_layout.addWidget(self.folder_button)
        
        content_layout.addWidget(details_widget)
        
        content_layout.addStretch(1)
        
        self.hide()
    
    def update_drag_bar_style(self, animate=True):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        if animate:
            self.drag_bar.animate_to_color(colors["accent_red"])
        else:
            self.drag_bar.set_color_immediately(colors["accent_red"])
    
    def update_content_widget_style(self, animate=False):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if animate:
            current_color = self.content_widget.palette().color(self.content_widget.backgroundRole())
            target_color = QColor(colors["dark_bg"])
            
            steps = 20
            step_duration = 40
            
            for step in range(steps + 1):
                progress = step / steps
                r = int(current_color.red() + (target_color.red() - current_color.red()) * progress)
                g = int(current_color.green() + (target_color.green() - current_color.green()) * progress)
                b = int(current_color.blue() + (target_color.blue() - current_color.blue()) * progress)
                bg_color = f"#{r:02x}{g:02x}{b:02x}"
                
                border_r = int(64 + (200 - 64) * progress) if not self.dark_mode else int(200 + (64 - 200) * progress)
                border_g = int(64 + (0 - 64) * progress) if not self.dark_mode else int(0 + (64 - 0) * progress)
                border_b = int(64 + (0 - 64) * progress) if not self.dark_mode else int(0 + (64 - 0) * progress)
                border_color = f"#{border_r:02x}{border_g:02x}{border_b:02x}"
                
                QTimer.singleShot(step * step_duration, 
                    lambda bg=bg_color, bc=border_color: self._apply_content_style(bg, bc))
        else:
            self._apply_content_style(colors["dark_bg"], colors["accent_red"])
    
    def _apply_content_style(self, bg_color, border_color):
        self.content_widget.setStyleSheet(f"""
            QWidget#content_widget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-top: none;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                margin: 0;
                padding: 0;
            }}
        """)
    
    def update_title_label_style(self, animate=True):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if animate:
            self.animate_text_color_smooth(self.title_label, colors["white"], 500)
        else:
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["white"]};
                    background: transparent;
                    border: none;
                    padding: 0;
                    margin: 0;
                    margin-bottom: 5px;
                }}
            """)
    
    def update_info_label_style(self, animate=True):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if animate:
            self.animate_text_color_smooth(self.info_label, colors["text_light"], 500)
        else:
            self.info_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["text_light"]};
                    background: transparent;
                    border: none;
                    padding: 5px 0;
                    line-height: 1.5;
                    min-height: 85px;
                    max-height: 100px;
                }}
            """)
    
    def update_project_label_style(self, animate=True):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if animate:
            self.animate_text_color_smooth(self.project_label, colors["white"], 500)
        else:
            self.project_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["white"]};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                }}
            """)
    
    def update_status_label_style(self, animate=True):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if "TG clothing bot" in self.current_item_name:
            status_color = colors["yellow"]
        elif "Youtube unblocking" in self.current_item_name:
            status_color = colors["accent_red"]
        else:
            status_color = colors["accent_green"]
        
        if animate:
            self.animate_text_color_smooth(self.status_label, status_color, 500)
        else:
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {status_color};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                    font-style: italic;
                }}
            """)
    
    def animate_text_color_smooth(self, label, target_color_hex, duration):
        current_color = label.palette().color(label.foregroundRole())
        target_color = QColor(target_color_hex)
        
        if current_color == target_color:
            return
        
        steps = 30
        step_duration = duration // steps
        
        for step in range(steps + 1):
            progress = step / steps
            r = int(current_color.red() + (target_color.red() - current_color.red()) * progress)
            g = int(current_color.green() + (target_color.green() - current_color.green()) * progress)
            b = int(current_color.blue() + (target_color.blue() - current_color.blue()) * progress)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            QTimer.singleShot(step * step_duration, 
                lambda c=color, l=label: l.setStyleSheet(f"""
                    QLabel {{
                        color: {c};
                        background: transparent;
                        border: none;
                        padding: {l.styleSheet().split('padding:')[1].split(';')[0] if 'padding:' in l.styleSheet() else '0'};
                    }}
                """))
    
    def update_all_styles(self, dark_mode, animate=True):
        self.dark_mode = dark_mode
        
        self.update_drag_bar_style(animate)
        self.update_content_widget_style(animate)
        self.update_title_label_style(animate)
        self.update_info_label_style(animate)
        self.update_project_label_style(animate)
        self.update_status_label_style(animate)
        
        colors = COLORS if dark_mode else {**COLORS, **LIGHT_COLORS}
        if hasattr(self, 'download_button'):
            self.download_button.update_theme(dark_mode)
        if hasattr(self, 'folder_button'):
            self.folder_button.update_theme(dark_mode)
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_bar.geometry().contains(event.pos()):
                self.is_dragging = True
                self.drag_start = event.globalPosition().y()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.is_dragging and self.drag_start is not None:
            current_y = event.globalPosition().y()
            delta = current_y - self.drag_start
            
            if delta > 30:
                self.close_panel()
                self.is_dragging = False
                event.accept()
                return
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            self.drag_start = None
        super().mouseReleaseEvent(event)
        
    def close_panel(self):
        self.animation = QPropertyAnimation(self, b"geometry", self)
        self.animation.setDuration(300)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRectF(
            self.x(),
            self.parent().height(),
            self.width(),
            self.height()
        ))
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.on_close_animation_finished)
        if not self._state_timer.isActive():
            self._state_timer.start()

        self.animation.start()
        
    def on_close_animation_finished(self):
        if self._state_timer.isActive():
            self._state_timer.stop()
        self.hide()
        self.closed.emit()
        
    def show_panel(self, version_info):
        self.current_item_name = version_info.get('item_name', '')
        
        version_text = version_info['version']
        
        version_date_map = {
            "Computer assembly": "1 мая 2025 г.",
            "Notes": "26 янв. 2025 г.",
            "Python compiler": "8 янв. 2025 г.",
            "Artificial intelligence": "14 дек. 2024 г.",
            "Snake": "2 дек. 2024 г.",
            "Artificial intelligence vk bot": "28 нояб. 2024 г.",
            "Connection": "17 нояб. 2024 г.",
            "System": "14 окт. 2024 г.",
            "Game for remodeling": "12 окт. 2024 г.",
            "Youtube unblocking": "12 окт. 2024 г.",
            "TG clothing bot": "25 янв. 2026 г.",
        }
        
        descriptions = {
            "Computer assembly": "Приложение для сборки, проверки компьютера, покупки компонентов.",
            "Notes": "Заметки.",
            "Python compiler": "Код создан для упрощения процесса компиляции программ. Компилятор с удобным графическим интерфейсом, который позволит вам компилировать ваши программы быстро и легко.",
            "Artificial intelligence": "Искусственный Интеллект с Голосовым Интерфейсом.",
            "Snake": "Змейка.",
            "Artificial intelligence vk bot": "Искусственный интеллект Вк бот бесплатно.",
            "Connection": "Соединение 2 файлов Python между собой.",
            "System": "Система.",
            "Game for remodeling": "Это игра исходник для масштабирования в пвп.",
            "Youtube unblocking": "Разблокировка Ютуба.",
            "TG clothing bot": "Бот для Telegram с искусственным интеллектом для подбора одежды.",
        }
        
        if self.current_item_name in version_date_map:
            date_text = version_date_map[self.current_item_name]
            self.title_label.setText(f"{date_text} - Версия {version_text}")
        else:
            self.title_label.setText(f"Версия {version_text}")
        
        if self.current_item_name in descriptions:
            description = descriptions[self.current_item_name]
            formatted_info = f"{description}"
            self.info_label.setText(formatted_info)
        else:
            main_info = version_info.get('description', 'Информация о выбранной версии...')
            formatted_info = main_info.replace('\n', '\n\n')
            self.info_label.setText(formatted_info)
        
        project_name = version_info.get('item_name', 'Неизвестный проект')
        self.project_label.setText(f"Проект: {project_name}")
        
        if project_name in ("TG clothing bot", "Computer assembly"):
            self.status_label.setText("Статус: В разработке")
            status_color = COLORS["yellow"] if self.dark_mode else LIGHT_COLORS["yellow"]
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {status_color};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                    font-style: italic;
                    font-weight: bold;
                }}
            """)
        elif project_name == "Youtube unblocking":
            self.status_label.setText("Статус: Нерабочий")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS["accent_red"]};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                    font-style: italic;
                    font-weight: bold;
                }}
            """)
        elif version_text == "1.00":
            self.status_label.setText("Статус: Актуальная версия")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS["accent_green"]};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                    font-style: italic;
                }}
            """)
        else:
            self.status_label.setText("Статус: Архивная версия")
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["artemis_gray"]};
                    background: transparent;
                    border: none;
                    padding: 2px 0;
                    margin: 0;
                    font-style: italic;
                }}
            """)
        
        is_downloaded = is_project_downloaded(self.current_item_name)
        self.is_installed = is_downloaded
        self._apply_download_button_state(is_downloaded)

        
        self.setGeometry(
            0,
            self.parent().height(),
            self.parent().width(),
            int(self.parent().height() * 0.65)
        )
        
        self.show()
        self.raise_()
        
        self.animation = QPropertyAnimation(self, b"geometry", self)
        self.animation.setDuration(400)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(QRectF(
            self.x(),
            self.parent().height() - self.height(),
            self.width(),
            self.height()
        ))
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.animation.start()
    
    def on_download_clicked(self):
        if not self.is_installed:
            print(f"Загрузка {self.current_item_name} версия 1.00...")
            
            projects_path = ensure_projects_folder(create=True)
            extracted_path = extract_project(self.current_item_name, projects_path)
            
            if extracted_path:
                self.is_installed = True
                self._apply_download_button_state(True)
                if hasattr(self.parent(), 'play_sound'):
                    self.parent().play_sound('finish')
                print(f"Проект успешно распакован в: {extracted_path}")
            else:
                print(f"Ошибка при распаковке проекта {self.current_item_name}")
    
    def on_folder_clicked(self):
        if hasattr(self.parent(), 'play_sound'):
            self.parent().play_sound('file')
        print(f"Переход к файлам {self.current_item_name} версия 1.00...")
        open_project_folder(self.current_item_name)

class BorderedThemePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.border_color = QColor(COLORS["accent_red"])
        self.border_width = 2
        self.dark_mode = True
        self._theme_progress = 0.0
        self._theme_from = None
        self._theme_to = None
        self._theme_anim = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        bg_color = QColor(colors["dark_bg"])
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        pen = QPen(self.border_color, self.border_width)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            self.border_width // 2,
            self.border_width // 2,
            self.width() - self.border_width,
            self.height() - self.border_width,
            10, 10
        )
        
    def update_style(self, dark_mode):
        self.dark_mode = dark_mode
        self.border_color = QColor(COLORS["accent_red"])
        self.repaint()

class AnimatedLetterLabel(QLabel):
    _original_y_changed = pyqtSignal(float)
    _original_x_changed = pyqtSignal(float)
    _rotation_changed = pyqtSignal(float)
    _scale_changed = pyqtSignal(float)
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._original_y = 0.0
        self._original_x = 0.0
        self._rotation = 0.0
        self._scale = 1.0
        self.current_animations = []
        self.is_hovered = False
        self.base_font_size = 20
        self.dark_mode = True
    
    @pyqtProperty(float, notify=_original_y_changed)
    def original_y(self):
        return self._original_y
    
    @original_y.setter
    def original_y(self, value):
        if self._original_y != value:
            self._original_y = value
            self._original_y_changed.emit(value)
            self.update()
    
    @pyqtProperty(float, notify=_original_x_changed)
    def original_x(self):
        return self._original_x
    
    @original_x.setter
    def original_x(self, value):
        if self._original_x != value:
            self._original_x = value
            self._original_x_changed.emit(value)
            self.update()
    
    @pyqtProperty(float, notify=_rotation_changed)
    def rotation(self):
        return self._rotation
    
    @rotation.setter
    def rotation(self, value):
        if self._rotation != value:
            self._rotation = value
            self._rotation_changed.emit(value)
            self.update()
    
    @pyqtProperty(float, notify=_scale_changed)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        if self._scale != value:
            self._scale = value
            self._scale_changed.emit(value)
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        current_font = QFont("Segoe UI", self.base_font_size, QFont.Weight.Bold)
        painter.setFont(current_font)
        
        font_metrics = QFontMetrics(current_font)
        text_rect = font_metrics.boundingRect(self.text())
        
        x = (self.width() - text_rect.width()) / 2 + self._original_x
        y = (self.height() + text_rect.height()) / 2 - font_metrics.descent() + self._original_y
        
        transform = QTransform()
        transform.translate(self.width()/2, self.height()/2)
        transform.rotate(self._rotation)
        transform.scale(self._scale, self._scale)
        transform.translate(-self.width()/2, -self.height()/2)
        painter.setTransform(transform)
        
        shadow_layers = [
            (2, QColor(200, 200, 200, 60)),
            (3, QColor(200, 200, 200, 30)),
        ]
        
        for radius, color in shadow_layers:
            painter.setPen(QPen(color, radius))
            offset = radius / 15
            painter.drawText(int(x + offset), int(y + offset), self.text())
        
        painter.setPen(QPen(QColor(colors["artemis_gray"])))
        painter.drawText(int(x), int(y), self.text())
    
    
    
    def update_theme_intermediate(self, text_muted):
        try:
            self.setStyleSheet(f"""
                QLabel {{
                    color: {text_muted};
                    padding: 2px 5px;
                    background: transparent;
                    font-style: italic;
                    border: none;
                }}
            """)
        except Exception:
            pass


    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self.update()

class AnimatedFooterLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.is_bold_strikethrough = False
        self.force_strike = False
        self.force_strike = False
        self.dark_mode = True
        
        self.bold_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        self.setFont(self.bold_font)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
    
    def update_style(self, colors=None):
        if colors is None:
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if self.is_bold_strikethrough or self.force_strike:
            self.setText('<s>Version 1.00</s>')
        else:
            self.setText("Version 1.00")
        
        text_color = colors["text_muted"]
        
        self.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                padding: 2px 5px;
                background: transparent;
                font-style: italic;
                border: none;
            }}
        """)
    
    
    def update_theme_intermediate(self, text_muted):
        try:
            self.setStyleSheet(f"""
                QLabel {{
                    color: {text_muted};
                    padding: 2px 5px;
                    background: transparent;
                    font-style: italic;
                    border: none;
                }}
            """)
        except Exception:
            pass

    def set_strikethrough(self, enabled: bool):
        self.force_strike = bool(enabled)
        self.update_style()

    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        colors = COLORS if dark_mode else {**COLORS, **LIGHT_COLORS}
        self.update_style(colors)
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        self.is_bold_strikethrough = True
        self.setText('<s>Version 1.00</s>')
        self.repaint()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.is_bold_strikethrough = False
        self.setText("Version 1.00")
        self.repaint()
        super().leaveEvent(event)

class CircularImageLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setScaledContents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, self.width(), self.height())
        painter.setClipPath(path)
        
        if self.pixmap():
            painter.drawPixmap(0, 0, self.width(), self.height(), self.pixmap())
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class AnimatedCategoryButton(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, text="", item_type="", parent=None, dark_mode=True):
        super().__init__(parent)
        self.text = text
        self.item_type = item_type
        self.dark_mode = dark_mode
        self.is_active = False
        self.is_hovered = False
        
        self.normal_bg_color = QColor()
        self.hover_bg_color = QColor()
        self.active_bg_color = QColor()
        self.normal_text_color = QColor()
        self.hover_text_color = QColor()
        self.active_text_color = QColor()
        
        self._bg_color = QColor()
        self._text_color = QColor()
        
        self.bg_animation = QPropertyAnimation(self, b"bg_color", self)
        self.bg_animation.setDuration(300)
        self.bg_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.text_animation = QPropertyAnimation(self, b"text_color", self)
        self.text_animation.setDuration(300)
        self.text_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(self.bg_animation)
        self.animation_group.addAnimation(self.text_animation)
        
        self.setup_ui()
        self.update_colors()
        self.setFixedHeight(36)
        self.setMinimumWidth(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @pyqtProperty(QColor)
    def bg_color(self):
        return self._bg_color
    
    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value
        self.update()
    
    @pyqtProperty(QColor)
    def text_color(self):
        return self._text_color
    
    @text_color.setter
    def text_color(self, value):
        self._text_color = value
        self.update()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.text_label = QLabel(self.text)
        self.text_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)
    
    def update_colors(self):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        if self.is_active:
            self.normal_bg_color = QColor(COLORS["accent_red"])
            self.normal_bg_color.setAlpha(37)
            self.normal_text_color = QColor(colors["white"])
        else:
            self.normal_bg_color = QColor(colors["medium_bg"])
            self.normal_text_color = QColor(colors["white"])
        
        self.hover_bg_color = QColor(COLORS["accent_red"])
        self.hover_bg_color.setAlpha(64)
        self.hover_text_color = QColor("#c0c0c0")
        
        if not self.animation_group.state() == QPropertyAnimation.State.Running:
            if self.is_active:
                self._bg_color = self.normal_bg_color
                self._text_color = self.normal_text_color
            elif self.is_hovered:
                self._bg_color = self.hover_bg_color
                self._text_color = self.hover_text_color
            else:
                self._bg_color = self.normal_bg_color
                self._text_color = self.normal_text_color
            self.update()
    
    def enterEvent(self, event):
        self.is_hovered = True
        if not self.is_active:
            self.animate_to_state("hover")
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.is_hovered = False
        if not self.is_active:
            self.animate_to_state("normal")
        super().leaveEvent(event)
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_type)
        super().mousePressEvent(event)
    
    def set_active(self, active):
        if self.is_active == active:
            return
        
        self.is_active = active
        self.update_colors()
        
        if active:
            self.animate_to_state("active")
        elif self.is_hovered:
            self.animate_to_state("hover")
        else:
            self.animate_to_state("normal")
    
    def animate_to_state(self, state):
        target_bg_color = None
        target_text_color = None
        
        if state == "active":
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
            target_bg_color = QColor(COLORS["accent_red"])
            target_bg_color.setAlpha(37)
            target_text_color = QColor(colors["white"])
        elif state == "hover":
            target_bg_color = QColor(COLORS["accent_red"])
            target_bg_color.setAlpha(64)
            target_text_color = QColor("#c0c0c0")
        elif state == "normal":
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
            target_bg_color = QColor(colors["medium_bg"])
            target_text_color = QColor(colors["white"])
        
        if target_bg_color and target_text_color:
            if self.animation_group.state() == QPropertyAnimation.State.Running:
                self.animation_group.stop()
            
            self.bg_animation.setStartValue(self._bg_color)
            self.bg_animation.setEndValue(target_bg_color)
            
            self.text_animation.setStartValue(self._text_color)
            self.text_animation.setEndValue(target_text_color)
            
            self.animation_group.start()
    
    
    def update_theme_intermediate(self, dark_bg, medium_bg, light_bg, border, text_light, white):
        try:
            self.normal_bg_color = QColor(medium_bg)
            self.normal_text_color = QColor(white)
            self.hover_bg_color = QColor(COLORS["accent_red"])
            self.hover_bg_color.setAlpha(64)
            self.hover_text_color = QColor("#c0c0c0")

            if self.is_active:
                self._bg_color = QColor(COLORS["accent_red"])
                self._bg_color.setAlpha(37)
                self._text_color = QColor(white)
            elif self.is_hovered:
                self._bg_color = self.hover_bg_color
                self._text_color = self.hover_text_color
            else:
                self._bg_color = self.normal_bg_color
                self._text_color = self.normal_text_color
            self.update()
        except Exception:
            pass

    def update_theme(self, dark_mode):
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self.update_colors()
            
            if self.animation_group.state() == QPropertyAnimation.State.Running:
                self.animation_group.stop()
            
            colors = COLORS if dark_mode else {**COLORS, **LIGHT_COLORS}
            
            if self.is_active:
                self._bg_color = QColor(COLORS["accent_red"])
                self._bg_color.setAlpha(37)
                self._text_color = QColor(colors["white"])
            elif self.is_hovered:
                self._bg_color = QColor(COLORS["accent_red"])
                self._bg_color.setAlpha(64)
                self._text_color = QColor("#c0c0c0")
            else:
                self._bg_color = QColor(colors["medium_bg"])
                self._text_color = QColor(colors["white"])
            
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QBrush(self._bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)
        
        self.text_label.setStyleSheet(f"""
            QLabel {{
                color: {self._text_color.name()};
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
                font-weight: {'bold' if self.is_active else 'medium'};
            }}
        """)

class CloseButton(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("✕")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rotation_angle = 0
        self.is_animating = False
        self.animation = None
        self.update_style()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        transform = QTransform()
        transform.translate(self.width()/2, self.height()/2)
        transform.rotate(self.rotation_angle)
        transform.translate(-self.width()/2, -self.height()/2)
        painter.setTransform(transform)
        
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(QColor(COLORS["accent_red"])))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "✕")
        
    def update_style(self):
        self.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: none;
            }}
            QLabel:hover {{
                background-color: transparent;
            }}
        """)
    
    def enterEvent(self, event):
        if not self.is_animating:
            self.start_rotation_animation()
        super().enterEvent(event)
    
    def start_rotation_animation(self):
        self.is_animating = True
        
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self, b"rotation_angle", self)
        self.animation.setDuration(500)
        self.animation.setStartValue(self.rotation_angle)
        self.animation.setEndValue(self.rotation_angle + 360)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.animation.finished.connect(self.on_animation_finished)
        self.animation.start()
    
    def on_animation_finished(self):
        self.is_animating = False
        self.rotation_angle = self.rotation_angle % 360
        
    @pyqtProperty(float)
    def rotation_angle(self):
        return self._rotation_angle if hasattr(self, '_rotation_angle') else 0
    
    @rotation_angle.setter
    def rotation_angle(self, value):
        self._rotation_angle = value
        self.update()
        

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ThemeSlider(QWidget):
    theme_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.dark_mode = True
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.slider_bg = QLabel()
        self.slider_bg.setFixedSize(60, 30)
        self.update_slider_bg_style()
        
        self.moon_label = QLabel("🌙")
        self.moon_label.setFont(QFont("Segoe UI", 12))
        self.moon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.moon_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: white;
                padding: 0;
                margin: 0;
            }
        """)
        
        self.sun_label = QLabel("☀️")
        self.sun_label.setFont(QFont("Segoe UI", 12))
        self.sun_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sun_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: black;
                padding: 0;
                margin: 0;
            }
        """)
        
        self.slider_knob = QWidget()
        self.slider_knob.setFixedSize(26, 26)
        self.slider_knob_layout = QHBoxLayout(self.slider_knob)
        self.slider_knob_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_knob_layout.setSpacing(0)
        
        self.slider_knob_layout.addWidget(self.moon_label)
        self.sun_label.hide()
        
        self.update_slider_knob_style()
        
        layout.addWidget(self.slider_bg)
        self.slider_knob.setParent(self)
        self.update_slider_position()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def update_slider_bg_style(self):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        self.slider_bg.setStyleSheet(f"""
            QLabel {{
                background-color: {colors["medium_bg"]};
                border-radius: 15px;
                border: 2px solid {colors["border"]};
            }}
        """)
    
    def update_slider_knob_style(self):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        self.slider_knob.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["accent_red"]};
                border-radius: 13px;
                border: none;
            }}
        """)
    
    def update_slider_position(self):
        if self.dark_mode:
            self.slider_knob.move(2, 2)
            self.moon_label.show()
            self.sun_label.hide()
        else:
            self.slider_knob.move(32, 2)
            self.moon_label.hide()
            self.sun_label.show()
            
            if self.slider_knob_layout.indexOf(self.sun_label) == -1:
                self.slider_knob_layout.addWidget(self.sun_label)
    
    def update_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self.update_slider_bg_style()
        self.update_slider_knob_style()
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_theme()
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_changed.emit(self.dark_mode)
        
        self.animate_slider_position()
        self.animate_icon_change()
        
        QTimer.singleShot(300, lambda: self.update_slider_bg_style())
        QTimer.singleShot(300, lambda: self.update_slider_knob_style())
    
    def animate_slider_position(self):
        anim = QPropertyAnimation(self.slider_knob, b"pos", self)
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if self.dark_mode:
            anim.setStartValue(QPoint(32, 2))
            anim.setEndValue(QPoint(2, 2))
        else:
            anim.setStartValue(QPoint(2, 2))
            anim.setEndValue(QPoint(32, 2))
        
        anim.start()
    
    def animate_icon_change(self):
        if self.dark_mode:
            self.moon_label.show()
            self.sun_label.hide()
        else:
            self.moon_label.hide()
            self.sun_label.show()
            
            if self.slider_knob_layout.indexOf(self.sun_label) == -1:
                self.slider_knob_layout.addWidget(self.sun_label)


class SoundSlider(QWidget):
    """Тумблер звука как у темы (🔊 / 🔇)."""
    sound_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self.muted = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.slider_bg = QLabel()
        self.slider_bg.setFixedSize(60, 30)

        self.icon_on = QLabel("🔊")
        self.icon_on.setFont(QFont("Segoe UI", 12))
        self.icon_on.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_on.setStyleSheet("QLabel { background: transparent; padding: 0; margin: 0; }")

        self.icon_off = QLabel("🔇")
        self.icon_off.setFont(QFont("Segoe UI", 12))
        self.icon_off.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_off.setStyleSheet("QLabel { background: transparent; padding: 0; margin: 0; }")

        self.slider_knob = QWidget()
        self.slider_knob.setFixedSize(26, 26)
        self.slider_knob_layout = QHBoxLayout(self.slider_knob)
        self.slider_knob_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_knob_layout.setSpacing(0)

        self.slider_knob_layout.addWidget(self.icon_on)
        self.icon_off.hide()

        layout.addWidget(self.slider_bg)
        self.slider_knob.setParent(self)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.dark_mode = True
        self.update_theme(self.dark_mode)
        self.update_slider_position(immediate=True)

    def update_theme(self, dark_mode: bool):
        self.dark_mode = dark_mode
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}

        self.slider_bg.setStyleSheet(f"""
            QLabel {{
                background-color: {colors["medium_bg"]};
                border-radius: 15px;
                border: 2px solid {colors["border"]};
            }}
        """)
        self.slider_knob.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["accent_red"]};
                border-radius: 13px;
                border: none;
            }}
        """)

    def set_muted(self, muted: bool):
        if self.muted == muted:
            return
        self.muted = muted
        self.update_slider_position(immediate=True)

    def update_slider_position(self, immediate=False):
        if self.muted:
            target = QPoint(32, 2)
            self.icon_on.hide()
            self.icon_off.show()
            if self.slider_knob_layout.indexOf(self.icon_off) == -1:
                self.slider_knob_layout.addWidget(self.icon_off)
        else:
            target = QPoint(2, 2)
            self.icon_on.show()
            self.icon_off.hide()

        if immediate:
            self.slider_knob.move(target)
        else:
            anim = QPropertyAnimation(self.slider_knob, b"pos", self)
            anim.setDuration(260)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setEndValue(target)
            anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def toggle(self):
        self.muted = not self.muted
        self.sound_changed.emit(self.muted)
        self.update_slider_position(immediate=False)
class ActionButton(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text="", color=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.normal_color = color or COLORS["accent_red"]
        self.hover_color = self.adjust_color_brightness(self.normal_color, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_hovered = False
        
        self.setFixedHeight(32)
        self.setMinimumWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update_style()
    
    def adjust_color_brightness(self, hex_color, percent):
        try:
            color = QColor(hex_color)
            factor = 1 + (percent / 100.0)
            r = min(255, int(color.red() * factor))
            g = min(255, int(color.green() * factor))
            b = min(255, int(color.blue() * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color
    
    def update_style(self):
        current_color = self.hover_color if self.is_hovered else self.normal_color
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {current_color};
                color: white;
                border-radius: 6px;
                border: none;
                padding: 8px 12px;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
            QLabel:hover {{
                background-color: {self.hover_color};
            }}
        """)
        self.setText(self.text)
    
    def update_theme(self, dark_mode):
        pass
    

    def refresh_download_state(self):
        """Если папку проекта удалили/появилась — кнопка обновляется без перезапуска."""
        if not self.current_item_name:
            return
        downloaded = is_project_downloaded(self.current_item_name)
        if downloaded != self.is_installed:
            self.is_installed = downloaded
            self._apply_download_button_state(downloaded)

    def _apply_download_button_state(self, downloaded: bool):
        if downloaded:
            self.download_button.set_text("✅ Загружено")
        else:
            self.download_button.set_text("⬇️ Загрузить")
            self.download_button.set_color(COLORS["accent_red"])
            self.download_button.setEnabled(True)
            self.download_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.download_button.update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        self.is_hovered = True
        self.update_style()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update_style()
        super().leaveEvent(event)
    
    def set_color(self, color):
        self.normal_color = color
        self.hover_color = self.adjust_color_brightness(color, 20)
        self.update_style()
    
    def set_text(self, text):
        self.text = text
        self.update_style()

class SubMenuItem(QWidget):
    closed = pyqtSignal(str)
    version_selected = pyqtSignal(dict)
    
    def __init__(self, item_name, parent=None):
        super().__init__(parent)
        self.item_name = item_name
        self.versions = self.get_versions_for_item(item_name)
        self.dark_mode = True
        self.setup_ui()
    
    def get_versions_for_item(self, item_name):
        version_mapping = {
            "Computer assembly": ["1.00"],
            "Artificial intelligence": ["1.00"],
            "Artificial intelligence vk bot": ["1.00"],
            "Notes": ["1.00"],
            "Python compiler": ["1.00"],
            "Youtube unblocking": ["1.00"],
            "Snake": ["1.00"],
            "Game for remodeling": ["1.00"],
            "Connection": ["1.00"],
            "System": ["1.00"],
            "TG clothing bot": ["1.00"]
        }
        return version_mapping.get(item_name, ["1.00"])
    
    def get_version_info(self, item_name, version):
        info = {
            "item_name": item_name,
            "version": version,
            "description": ""
        }
        
        version_info = {
            "Computer assembly": {
                "1.00": "Приложение для сборки, проверки компьютера, покупки компонентов."
            },
            "Artificial intelligence": {
                "1.00": "Искусственный Интеллект с Голосовым Интерфейсом."
            },
            "Artificial intelligence vk bot": {
                "1.00": "Искусственный интеллект Вк бот бесплатно."
            },
            "Notes": {
                "1.00": "Заметки."
            },
            "Python compiler": {
                "1.00": "Код создан для упрощения процесса компиляции программ. Компилятор с удобным графическим интерфейсом, который позволит вам компилировать ваши программы быстро и легко."
            },
            "Youtube unblocking": {
                "1.00": "Разблокировка Ютуба."
            },
            "Snake": {
                "1.00": "Змейка."
            },
            "Game for remodeling": {
                "1.00": "Это игра исходник для масштабирования в пвп."
            },
            "Connection": {
                "1.00": "Соединение 2 файлов Python между собой."
            },
            "System": {
                "1.00": "Система."
            },
            "TG clothing bot": {
                "1.00": "Бот для Telegram с искусственным интеллектом для подбора одежды."
            }
        }
        
        if item_name in version_info and version in version_info[item_name]:
            info["description"] = version_info[item_name][version]
        else:
            info["description"] = f"Версия {version} проекта {item_name}.\nОсновные функции и возможности."
            
        return info
    
    def setup_ui(self):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["medium_bg"]};
                border-radius: 10px;
                border: 1px solid {colors["border"]};
                margin: 0;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        title_label = QLabel(f"{self.item_name}")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["white"]};
                padding: 6px 0;
                background: transparent;
                border: none;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setMinimumHeight(40)
        layout.addWidget(title_label)
        
        versions_label = QLabel("Доступные версии:")
        versions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        versions_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_muted"]};
                padding: 2px 0;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(versions_label)
        
        for version in self.versions:
            version_btn = QPushButton(f"Версия {version}")
            version_btn.setProperty("version", version)
            version_btn.setFont(QFont("Segoe UI", 10))
            version_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            version_btn.setFixedHeight(35)
            version_btn.setMinimumWidth(140)
            
            btn_style = f"""
                QPushButton {{
                    background-color: {COLORS["accent_green"]};
                    color: {colors["white"]};
                    border-radius: 6px;
                    border: none;
                    padding: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["accent_green"]}80;
                }}
            """
            
            version_btn.setStyleSheet(btn_style)
            version_btn.clicked.connect(lambda checked, v=version: self.on_version_selected(v))
            layout.addWidget(version_btn)
        
        close_btn = QPushButton("✕ Закрыть")
        close_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedHeight(40)
        close_btn.setMinimumWidth(140)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["accent_red"]};
                color: {colors["white"]};
                border-radius: 6px;
                border: none;
                padding: 10px 15px;
                margin-top: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff5252;
                color: {colors["white"]};
            }}
        """)
        close_btn.clicked.connect(self.close_self)
        layout.addWidget(close_btn)
        
        layout.addStretch()
    
    def on_version_selected(self, version):
        print(f"Выбрана версия {version} для {self.item_name}")
        version_info = self.get_version_info(self.item_name, version)
        self.version_selected.emit(version_info)
    
    def close_self(self):
        try:
            w = self.window()
            if hasattr(w, "play_sound"):
                w.play_sound("exit")
        except Exception:
            pass
        self.closed.emit(self.item_name)
    
    def update_style(self, colors):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["medium_bg"]};
                border-radius: 10px;
                border: 1px solid {colors["border"]};
                margin: 0;
                padding: 15px;
            }}
        """)

class RoundedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARTEMIS")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(300, 300, 500, 220)

        set_taskbar_icon()
        self.load_app_icon()

        self.sound_manager = SoundManager(self)
        self.sound_volume = 1.0
        self.sound_muted = False
        self.sound_manager.set_volume(self.sound_volume)
        self._sound_paths = {
            'file': get_resource_path('File.mp3'),
            'finish': get_resource_path('Finish.mp3'),
            'exit': get_resource_path('Exit.mp3'),
        }
        self._closing_in_progress = False

        self.drag_pos = QPoint()
        self.is_dragging = False
        self.selected_category = "ai"
        self.is_initial_load = True
        self.is_theme_panel_open = False
        self.dark_mode = True
        self._theme_progress = 0.0
        self._theme_from = None
        self._theme_to = None
        self._theme_anim = None

        self.letter_animations = {}
        self.current_hovered_letter = None
        self.panel_animation_group = None
        
        self.footer_animation_active = False
        self.footer_animation_index = 0
        self.footer_sequences = []
        self.footer_reverse_animation = False
        self.footer_timer = None
        
        self.current_submenu = None
        self.submenu_animations = {}
        self.submenu_instances = {}
        self.is_submenu_open = False
        self.current_submenu_item = None
        self.content_animation_group = None
        
        self.content_item_handlers = {}
        
        self.version_panel = None
        
        self.base_font_size = 20
        self.footer_label = None
        self.version_label = None
        self.letter_labels = []
        self.category_buttons = []
        self.content_items = {}
        
        self.panel_y = 80
        self.panel_height = 200
        self.panel_width = 150
        self.original_content_width = 280
        self.small_content_width = 160
        
        self.was_minimized = False
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        self.photo_label = CircularImageLabel()
        self.photo_label.clicked.connect(self.toggle_theme_panel)
        
        self.load_photo()
        
        top_layout.addWidget(self.photo_label)
        
        self.title_container = QWidget()
        self.title_container.setCursor(Qt.CursorShape.PointingHandCursor)
        
        title_layout = QHBoxLayout(self.title_container)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(1)
        
        for letter in "ARTEMIS":
            letter_label = AnimatedLetterLabel(letter)
            letter_label.setObjectName(f"letter_{letter}")
            
            letter_label.dark_mode = self.dark_mode
            
            title_font = QFont("Segoe UI", 20, QFont.Weight.Bold)
            letter_label.setFont(title_font)
            letter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            letter_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS["artemis_gray"]};
                    padding: 0px;
                    background: transparent;
                    border: none;
                    margin: 0;
                }}
            """)
            
            letter_label.setCursor(Qt.CursorShape.PointingHandCursor)
            title_layout.addWidget(letter_label)
            self.letter_labels.append(letter_label)
        
        top_layout.addStretch()
        top_layout.addWidget(self.title_container)
        top_layout.addStretch()
        
        self.close_btn = CloseButton()
        self.close_btn.clicked.connect(self.close)
        top_layout.addWidget(self.close_btn)
        
        layout.addWidget(top_container)

        categories_container = QWidget()
        categories_layout = QHBoxLayout(categories_container)
        categories_layout.setContentsMargins(0, 8, 0, 8)
        categories_layout.setSpacing(8)
        
        categories_layout.addStretch()
        
        categories = [
            ("Ai", "ai"),
            ("Vk", "vk"),
            ("Tg", "tg"),
            ("App", "app"),
            ("Games", "games"),
            ("Script", "script"),
        ]
        
        for text, item_type in categories:
            category_btn = AnimatedCategoryButton(text, item_type, dark_mode=self.dark_mode)
            
            if item_type == "ai":
                category_btn.set_active(True)
            
            category_btn.clicked.connect(self.show_category_content)
            categories_layout.addWidget(category_btn)
            self.category_buttons.append(category_btn)
        
        categories_layout.addStretch()
        layout.addWidget(categories_container)
        
        self.main_content_container = QWidget()
        main_content_layout = QHBoxLayout(self.main_content_container)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(8)
        
        self.content_container = QWidget()
        self.content_container.setFixedWidth(self.original_content_width)
        self.content_container.setObjectName("content_container")
        self.content_container.setStyleSheet(f"""
            QWidget#content_container {{
                background: {COLORS["medium_bg"]}; 
                border-radius: 10px;
                border: 1px solid {COLORS["border"]};
                margin: 0;
                padding: 0;
            }}
        """)
        
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(6)
        
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
                min-height: 160px;
            }}
            QScrollBar:vertical {{
                background: {COLORS["dark_bg"]};
                width: 5px;
                border-radius: 2px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS["border"]};
                border-radius: 2px;
                min-height: 15px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS["accent_green"]};
            }}
        """)
        
        self.content_widget = QWidget()
        self.content_items_layout = QVBoxLayout(self.content_widget)
        self.content_items_layout.setSpacing(6)
        self.content_items_layout.setContentsMargins(2, 2, 2, 2)
        
        self.content_scroll.setWidget(self.content_widget)
        content_layout.addWidget(self.content_scroll)
        
        main_content_layout.addWidget(self.content_container)
        
        self.submenu_container = QWidget()
        self.submenu_container.setFixedWidth(0)
        self.submenu_container.hide()
        
        submenu_layout = QVBoxLayout(self.submenu_container)
        submenu_layout.setContentsMargins(0, 0, 0, 0)
        submenu_layout.setSpacing(0)
        
        main_content_layout.addWidget(self.submenu_container)
        
        layout.addWidget(self.main_content_container)

        footer_container = QWidget()
        footer_layout = QHBoxLayout(footer_container)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(0)
        
        self.footer_label = QLabel("© 2026 ARTEMIS")
        self.footer_label.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_font = QFont("Segoe UI", 8, QFont.Weight.Normal)
        self.footer_label.setFont(footer_font)
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.footer_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS["text_muted"]};
                padding: 3px;
                background: transparent;
                letter-spacing: 0.5px;
            }}
        """)
        
        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()
        
        self.version_label = AnimatedFooterLabel("Version 1.00")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_layout.addWidget(self.version_label)
        layout.addWidget(footer_container)

        central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS["dark_bg"]};
                border-radius: 0px;
                border: none;
            }}
        """)

        self.theme_panel = BorderedThemePanel(self)
        self.theme_panel.setGeometry(self.width(), self.panel_y, self.panel_width, self.panel_height)

        theme_layout = QVBoxLayout(self.theme_panel)
        theme_layout.setContentsMargins(12, 12, 12, 12)
        theme_layout.setSpacing(8)

        self.theme_header = QWidget()
        self.theme_header_layout = QHBoxLayout(self.theme_header)
        self.theme_header_layout.setContentsMargins(0, 0, 0, 0)
        self.theme_header_layout.setSpacing(10)

        self.theme_title = QLabel("Тема")
        self.theme_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.theme_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS["white"]};
                background: transparent;
                border: none;
            }}
        """)

        if hasattr(self, "sound_title"):
            self.sound_title.setStyleSheet(f"""
                QLabel {{
                    color: {colors["white"]};
                    background: transparent;
                    border: none;
                }}
            """)
        if hasattr(self, "sound_slider"):
            self.sound_slider.update_theme(self.dark_mode)
        if hasattr(self, "volume_slider"):
            self.volume_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: 6px;
                    border-radius: 3px;
                    background: {colors["border"]};
                }}
                QSlider::handle:horizontal {{
                    background: {COLORS["accent_red"]};
                    width: 14px;
                    margin: -5px 0;
                    border-radius: 7px;
                }}
            """)
        self.theme_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.theme_header_layout.addWidget(self.theme_title)

        self.theme_slider = ThemeSlider()
        self.theme_slider.theme_changed.connect(self.change_theme)
        self.theme_header_layout.addWidget(self.theme_slider, 0, Qt.AlignmentFlag.AlignRight)

        theme_layout.addWidget(self.theme_header)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["border"]};
                border: none;
                height: 1px;
                margin: 4px 0;
            }}
        """)
        theme_layout.addWidget(separator)


        self.sound_header = QWidget()
        self.sound_header_layout = QHBoxLayout(self.sound_header)
        self.sound_header_layout.setContentsMargins(0, 0, 0, 0)
        self.sound_header_layout.setSpacing(10)

        self.sound_title = QLabel("Звук")
        self.sound_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.sound_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.sound_title.setStyleSheet(f"QLabel {{ color: {COLORS['white']}; background: transparent; border: none; }}")
        self.sound_header_layout.addWidget(self.sound_title)

        self.sound_slider = SoundSlider()
        self.sound_slider.sound_changed.connect(self.set_sound_muted)
        self.sound_header_layout.addWidget(self.sound_slider, 0, Qt.AlignmentFlag.AlignRight)

        theme_layout.addWidget(self.sound_header)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_sound_volume_percent)
        self.volume_slider.setFixedHeight(18)
        self.volume_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        theme_layout.addWidget(self.volume_slider)

        theme_layout.addStretch()
        self.theme_panel.hide()

        if hasattr(self, "sound_slider"):
            self.sound_slider.set_muted(self.sound_muted)
            self.sound_slider.update_theme(self.dark_mode)
        if hasattr(self, "volume_slider"):
            self.volume_slider.setValue(int(self.sound_volume * 100))
            self.volume_slider.setEnabled(not self.sound_muted)

        self.installEventFilter(self)
        for letter_label in self.letter_labels:
            letter_label.installEventFilter(self)
        if self.footer_label:
            self.footer_label.installEventFilter(self)

        QTimer.singleShot(300, self.setup_title_animations)
        QTimer.singleShot(600, lambda: self.show_category_content("ai", is_initial=True))

    def play_sound(self, name: str):
        path = self._sound_paths.get(name)
        self.sound_manager.play(name, path)


    def set_sound_muted(self, muted: bool):
        self.sound_muted = bool(muted)
        try:
            self.sound_manager.set_muted(self.sound_muted)
        except Exception:
            pass

        if hasattr(self, "volume_slider"):
            self.volume_slider.setEnabled(not self.sound_muted)
        if hasattr(self, "sound_slider"):
            self.sound_slider.set_muted(self.sound_muted)

        if hasattr(self, "version_label") and hasattr(self.version_label, "set_strikethrough"):
            self.version_label.set_strikethrough(self.sound_muted)

    def set_sound_volume_percent(self, value: int):
        v = max(0, min(100, int(value)))
        self.sound_volume = v / 100.0
        if self.sound_muted:
            return
        try:
            self.sound_manager.set_volume(self.sound_volume)
        except Exception:
            pass

    def load_app_icon(self):
        try:
            icon_paths = [
                "ARTMIS.ico",
                "ARTEMIS.ico",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "ARTMIS.ico"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "ARTEMIS.ico"),
            ]
            
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                icon_paths.insert(0, os.path.join(base_path, "ARTMIS.ico"))
                icon_paths.insert(1, os.path.join(base_path, "ARTEMIS.ico"))
            
            icon_loaded = False
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    icon_loaded = True
                    break
            
            if not icon_loaded:
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(COLORS["dark_bg"]))
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                painter.setBrush(QBrush(QColor(COLORS["accent_red"])))
                painter.drawEllipse(4, 4, 24, 24)
                
                painter.setPen(QPen(QColor(COLORS["white"])))
                painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
                painter.end()
                
                self.setWindowIcon(QIcon(pixmap))
                
        except Exception as e:
            print(f"Ошибка загрузки иконки: {e}")
    
    def load_photo(self):
        pixmap = None

        candidates = ["Photo.jpg", "photo.jpg"]

        try:
            for name in candidates:
                if os.path.exists(name):
                    pixmap = QPixmap(name)
                    break

            if pixmap is None:
                if getattr(sys, 'frozen', False):
                    base_path = sys._MEIPASS
                else:
                    base_path = os.path.dirname(os.path.abspath(__file__))

                for name in candidates:
                    photo_path = os.path.join(base_path, name)
                    if os.path.exists(photo_path):
                        pixmap = QPixmap(photo_path)
                        break
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")

        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap(40, 40)
            pixmap.fill(QColor(COLORS["dark_bg"]))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(COLORS["medium_bg"])))
            painter.drawEllipse(0, 0, 40, 40)
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(COLORS["text_muted"])))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "ART")
            painter.end()
        else:
            pixmap = pixmap.scaled(
                40, 40,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

        self.photo_label.setPixmap(pixmap)


    def show_version_info_panel(self, version_info):
        if self.version_panel is None:
            self.version_panel = SlideDownPanel(self, dark_mode=self.dark_mode)
            self.version_panel.closed.connect(self.on_version_panel_closed)
        else:
            self.version_panel.dark_mode = self.dark_mode
            self.version_panel.update_all_styles(self.dark_mode, animate=False)
        
        self.version_panel.show_panel(version_info)
    
    def on_version_panel_closed(self):
        self.version_panel = None

    def eventFilter(self, obj, event):
        if obj in self.letter_labels:
            if event.type() == event.Type.Enter:
                self.on_letter_enter(obj)
                return True
            elif event.type() == event.Type.Leave:
                self.on_letter_leave(obj)
                return True
        
        elif hasattr(self, 'footer_label') and obj == self.footer_label:
            if event.type() == event.Type.Enter:
                self.on_footer_enter()
                return True
            elif event.type() == event.Type.Leave:
                self.on_footer_leave()
                return True
                
        return super().eventFilter(obj, event)
    
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.was_minimized = True
            elif self.was_minimized and self.windowState() == Qt.WindowState.WindowNoState:
                self.was_minimized = False
        super().changeEvent(event)
    
    def event(self, event):
        if event.type() == QEvent.Type.ApplicationActivate:
            if self.isMinimized():
                self.showNormal()
            elif not self.isVisible():
                self.show()
            self.activateWindow()
            self.raise_()
            return True
        return super().event(event)

    def on_footer_enter(self):
        if not self.footer_animation_active:
            self.start_footer_animation()

    def start_footer_animation(self):
        if self.footer_animation_active:
            return
        
        self.footer_animation_active = True
        self.footer_reverse_animation = False
        
        sequences = [
            "© 2026 ARTEMIS",
            "© 202 ARTEMIS", 
            "© 20 ARTEMIS",
            "© 2 ARTEMIS",
            "©  ARTEMIS",
            "© 2 ARTEMIS",
            "© 20 ARTEMIS",
            "© 202 ARTEMIS",
            "© 2024 ARTEMIS"
        ]
        
        self.footer_sequences = sequences
        self.footer_animation_index = 0
        self.animate_next_footer_text()

    def on_footer_leave(self):
        if self.footer_animation_active or self.footer_label.text() != "© 2026 ARTEMIS":
            self.start_footer_reverse_animation()

    def start_footer_reverse_animation(self):
        current_text = self.footer_label.text()
        
        if current_text == "© 2026 ARTEMIS":
            self.footer_animation_active = False
            self.footer_reverse_animation = False
            return
        
        self.footer_animation_active = True
        self.footer_reverse_animation = True
        
        full_sequence_backward = [
            "© 2024 ARTEMIS",
            "© 202 ARTEMIS",
            "© 20 ARTEMIS", 
            "© 2 ARTEMIS",
            "©  ARTEMIS",
            "© 2 ARTEMIS",
            "© 20 ARTEMIS",
            "© 202 ARTEMIS",
            "© 2026 ARTEMIS"
        ]
        
        try:
            current_index = full_sequence_backward.index(current_text)
            self.footer_sequences = full_sequence_backward[current_index:]
            self.footer_animation_index = 0
        except ValueError:
            self.footer_sequences = [current_text, "© 2026 ARTEMIS"]
            self.footer_animation_index = 0
        
        self.animate_next_footer_text()

    def animate_next_footer_text(self):
        if not self.footer_animation_active:
            return
        
        if self.footer_label and self.footer_sequences:
            if self.footer_animation_index < len(self.footer_sequences):
                self.footer_label.setText(self.footer_sequences[self.footer_animation_index])
                
                if (not self.footer_reverse_animation and 
                    self.footer_sequences[self.footer_animation_index] == "© 2024 ARTEMIS"):
                    self.footer_animation_active = False
                    return
                
                if (self.footer_reverse_animation and 
                    self.footer_sequences[self.footer_animation_index] == "© 2026 ARTEMIS"):
                    self.footer_animation_active = False
                    self.footer_reverse_animation = False
                    return
                
                self.footer_animation_index += 1
                delay = 200 if self.footer_reverse_animation else 300
                QTimer.singleShot(delay, self.animate_next_footer_text)
            else:
                self.footer_animation_active = False
                if self.footer_reverse_animation:
                    self.footer_reverse_animation = False

    def stop_footer_animation(self):
        self.footer_animation_active = False
        self.footer_reverse_animation = False
        if self.footer_timer:
            self.footer_timer.stop()
            self.footer_timer = None

    def on_letter_enter(self, letter_label):
        if self.current_hovered_letter == letter_label:
            return
            
        self.reset_current_hover()
        self.current_hovered_letter = letter_label
        letter_label.is_hovered = True
        self.animate_single_letter(letter_label)

    def on_letter_leave(self, letter_label):
        if letter_label.is_hovered:
            letter_label.is_hovered = False
            self.reset_single_letter(letter_label)
            
        if self.current_hovered_letter == letter_label:
            self.current_hovered_letter = None

    def animate_single_letter(self, letter_label):
        if letter_label in self.letter_animations:
            self.letter_animations[letter_label].stop()
        
        anim_group = QParallelAnimationGroup(self)
        
        if letter_label.text() == "S":
            rotate_anim = QPropertyAnimation(letter_label, b"rotation", self)
            rotate_anim.setDuration(600)
            rotate_anim.setStartValue(0)
            rotate_anim.setEndValue(15)
            rotate_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            anim_group.addAnimation(rotate_anim)
            
            scale_anim = QPropertyAnimation(letter_label, b"scale", self)
            scale_anim.setDuration(400)
            scale_anim.setStartValue(1.0)
            scale_anim.setEndValue(1.05)
            scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim_group.addAnimation(scale_anim)
            
            y_anim = QPropertyAnimation(letter_label, b"original_y", self)
            y_anim.setDuration(400)
            y_anim.setStartValue(letter_label.original_y)
            y_anim.setEndValue(-6)
            y_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim_group.addAnimation(y_anim)
        else:
            y_anim = QPropertyAnimation(letter_label, b"original_y", self)
            y_anim.setDuration(400)
            y_anim.setStartValue(letter_label.original_y)
            y_anim.setEndValue(-6)
            y_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim_group.addAnimation(y_anim)
            
            scale_anim = QPropertyAnimation(letter_label, b"scale", self)
            scale_anim.setDuration(400)
            scale_anim.setStartValue(1.0)
            scale_anim.setEndValue(1.03)
            scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            anim_group.addAnimation(scale_anim)
        
        self.letter_animations[letter_label] = anim_group
        anim_group.start()

    def reset_single_letter(self, letter_label):
        if letter_label in self.letter_animations:
            self.letter_animations[letter_label].stop()
        
        reset_group = QParallelAnimationGroup(self)
        
        animations = [
            (b"original_y", 0.0),
            (b"rotation", 0.0),
            (b"scale", 1.0)
        ]
        
        for prop_name, end_value in animations:
            anim = QPropertyAnimation(letter_label, prop_name, self)
            anim.setDuration(300)
            anim.setStartValue(getattr(letter_label, prop_name.decode()))
            anim.setEndValue(end_value)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            reset_group.addAnimation(anim)
        
        reset_group.start()
        self.letter_animations[letter_label] = reset_group
        
        def cleanup():
            if letter_label in self.letter_animations:
                self.letter_animations.pop(letter_label, None)
        
        reset_group.finished.connect(cleanup)

    def reset_current_hover(self):
        if self.current_hovered_letter:
            self.reset_single_letter(self.current_hovered_letter)
            self.current_hovered_letter.is_hovered = False
            self.current_hovered_letter = None

    def toggle_theme_panel(self):
        if not self.is_theme_panel_open:
            self.theme_panel.show()
            self.theme_panel.raise_()
            self.theme_panel.setGeometry(self.width(), self.panel_y, self.panel_width, self.panel_height)
            
            if self.panel_animation_group:
                self.panel_animation_group.stop()
            
            self.panel_animation_group = QSequentialAnimationGroup(self)
            panel_anim = QPropertyAnimation(self.theme_panel, b"geometry")
            panel_anim.setDuration(500)
            panel_anim.setStartValue(QRectF(self.width(), self.panel_y, self.panel_width, self.panel_height))
            panel_anim.setEndValue(QRectF(self.width() - self.panel_width, self.panel_y, self.panel_width, self.panel_height))
            panel_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.panel_animation_group.addAnimation(panel_anim)
            
            self.panel_animation_group.start()
            self.is_theme_panel_open = True
            
        else:
            if self.panel_animation_group:
                self.panel_animation_group.stop()
            
            self.panel_animation_group = QSequentialAnimationGroup(self)
            
            panel_hide_anim = QPropertyAnimation(self.theme_panel, b"geometry")
            panel_hide_anim.setDuration(400)
            panel_hide_anim.setStartValue(QRectF(self.width() - self.panel_width, self.panel_y, self.panel_width, self.panel_height))
            panel_hide_anim.setEndValue(QRectF(self.width(), self.panel_y, self.panel_width, self.panel_height))
            panel_hide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
            self.panel_animation_group.addAnimation(panel_hide_anim)
            
            def hide_panel():
                self.theme_panel.hide()
                self.panel_animation_group = None
            
            self.panel_animation_group.finished.connect(hide_panel)
            self.panel_animation_group.start()
            self.is_theme_panel_open = False

    
    @pyqtProperty(float)
    def theme_progress(self):
        return float(self._theme_progress)

    @theme_progress.setter
    def theme_progress(self, value):
        self._theme_progress = float(value)
        if not self._theme_from or not self._theme_to:
            return
        p = max(0.0, min(1.0, self._theme_progress))

        colors_from = self._theme_from
        colors_to = self._theme_to

        dark_bg = self.interpolate_color(colors_from["dark_bg"], colors_to["dark_bg"], p)
        medium_bg = self.interpolate_color(colors_from["medium_bg"], colors_to["medium_bg"], p)
        light_bg = self.interpolate_color(colors_from["light_bg"], colors_to["light_bg"], p)
        border = self.interpolate_color(colors_from["border"], colors_to["border"], p)
        text_light = self.interpolate_color(colors_from["text_light"], colors_to["text_light"], p)
        text_muted = self.interpolate_color(colors_from["text_muted"], colors_to["text_muted"], p)
        white = self.interpolate_color(colors_from["white"], colors_to["white"], p)
        artemis_gray = self.interpolate_color(colors_from["artemis_gray"], colors_to["artemis_gray"], p)

        self.apply_intermediate_theme(dark_bg, medium_bg, light_bg, border, text_light, text_muted, white, artemis_gray)


    def change_theme(self, is_dark_mode):
        if self.dark_mode == is_dark_mode:
            return

        from_dark = self.dark_mode
        to_dark = bool(is_dark_mode)

        self.animate_theme_transition(from_dark, to_dark)

        self.theme_slider.update_theme(to_dark)

        if hasattr(self, "sound_slider"):
            self.sound_slider.update_theme(to_dark)

        if self.version_panel:
            self.version_panel.dark_mode = to_dark
            self.version_panel.update_all_styles(to_dark, animate=True)

    def animate_theme_transition(self, from_dark_mode: bool, to_dark_mode: bool):
        colors_from = COLORS if from_dark_mode else {**COLORS, **LIGHT_COLORS}
        colors_to = COLORS if to_dark_mode else {**COLORS, **LIGHT_COLORS}

        self._theme_from = colors_from
        self._theme_to = colors_to

        if self._theme_anim:
            try:
                self._theme_anim.stop()
            except Exception:
                pass

        self._theme_anim = QPropertyAnimation(self, b"theme_progress", self)
        self._theme_anim.setDuration(380)
        self._theme_anim.setStartValue(0.0)
        self._theme_anim.setEndValue(1.0)
        self._theme_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._theme_anim.finished.connect(lambda: self.finalize_theme_transition(to_dark_mode))
        self._theme_anim.start()

    def interpolate_color(self, color1_hex, color2_hex, progress):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        rgb1 = hex_to_rgb(color1_hex)
        rgb2 = hex_to_rgb(color2_hex)
        
        r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * progress)
        g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * progress)
        b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * progress)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def apply_intermediate_theme(self, dark_bg, medium_bg, light_bg, border, text_light, text_muted, white, artemis_gray):
        self.centralWidget().setStyleSheet(f"""
            QWidget {{
                background-color: {dark_bg};
                border-radius: 0px;
                border: none;
            }}
        """)
        
        self.content_container.setStyleSheet(f"""
            QWidget#content_container {{
                background: {medium_bg}; 
                border-radius: 10px;
                border: 1px solid {border};
                margin: 0;
                padding: 0;
            }}
        """)
        
        for item_label in self.content_items.values():
            item_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_light};
                    padding: 12px 15px;
                    background-color: {light_bg};
                    border-radius: 8px;
                    border-left: 3px solid {border};
                    margin: 2px;
                    min-height: 40px;
                }}
                QLabel:hover {{
                    background-color: {light_bg};
                    border-left-color: {COLORS["accent_green"]};
                    color: {white};
                }}
            """)
        
        for letter_label in self.letter_labels:
            letter_label.setStyleSheet(f"""
                QLabel {{
                    color: {artemis_gray};
                    padding: 0px;
                    background: transparent;
                    border: none;
                    margin: 0;
                }}
            """)
        
        for btn in self.category_buttons:
            if hasattr(btn, 'update_theme_intermediate'):
                btn.update_theme_intermediate(dark_bg, medium_bg, light_bg, border, text_light, white)
        
        if self.footer_label:
            self.footer_label.setStyleSheet(f"""
                QLabel {{
                    color: {text_muted};
                    padding: 3px;
                    background: transparent;
                    letter-spacing: 0.5px;
                }}
            """)
        
        if hasattr(self.version_label, 'update_theme_intermediate'):
            self.version_label.update_theme_intermediate(text_muted)
        
        if self.current_submenu:
            self.current_submenu.setStyleSheet(f"""
                QWidget {{
                    background-color: {medium_bg};
                    border-radius: 10px;
                    border: 1px solid {border};
                    margin: 0;
                    padding: 15px;
                }}
            """)
    
    def finalize_theme_transition(self, target_dark_mode):
        self.dark_mode = target_dark_mode
        
        self.update_all_styles_immediately()
        
        for btn in self.category_buttons:
            if hasattr(btn, 'update_theme'):
                btn.update_theme(self.dark_mode)
        
        for letter_label in self.letter_labels:
            if hasattr(letter_label, 'update_theme'):
                letter_label.update_theme(self.dark_mode)
        
        self.theme_panel.update_style(self.dark_mode)
        if hasattr(self, "sound_slider"):
            self.sound_slider.update_theme(self.dark_mode)
        if hasattr(self, "sound_title"):
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
            self.sound_title.setStyleSheet(f"QLabel {{ color: {colors['white']}; background: transparent; border: none; }}")
        
        if hasattr(self.version_label, 'update_theme'):
            self.version_label.update_theme(self.dark_mode)
    
    def update_all_styles_immediately(self):
        colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
        
        self.centralWidget().setStyleSheet(f"""
            QWidget {{
                background-color: {colors["dark_bg"]};
                border-radius: 0px;
                border: none;
            }}
        """)
        
        self.content_container.setStyleSheet(f"""
            QWidget#content_container {{
                background: {colors["medium_bg"]}; 
                border-radius: 10px;
                border: 1px solid {colors["border"]};
                margin: 0;
                padding: 0;
            }}
        """)
        
        for item_label in self.content_items.values():
            item_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["text_light"]};
                    padding: 12px 15px;
                    background-color: {colors["light_bg"]};
                    border-radius: 8px;
                    border-left: 3px solid {colors["border"]};
                    margin: 2px;
                    min-height: 40px;
                }}
                QLabel:hover {{
                    background-color: {colors["light_bg"]};
                    border-left-color: {colors["accent_green"]};
                    color: {colors["white"]};
                }}
            """)
        
        if self.current_submenu:
            self.current_submenu.update_style(colors)
        
        self.theme_title.setStyleSheet(f"""
            QLabel {{
                color: {colors["white"]};
                background: transparent;
                border: none;
            }}
        """)
        
        if self.footer_label:
            self.footer_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["text_muted"]};
                    padding: 3px;
                    background: transparent;
                    letter-spacing: 0.5px;
                }}
            """)
        
        if hasattr(self.version_label, 'update_theme'):
            self.version_label.update_theme(self.dark_mode)
        
        self.update()


    def closeEvent(self, event):
        if getattr(self, "_closing_in_progress", False):
            event.accept()
            return

        self._closing_in_progress = True
        self.play_sound('exit')
        event.ignore()

        QTimer.singleShot(650, QApplication.quit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 15, 15)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        
        if self.is_theme_panel_open:
            self.theme_panel.setGeometry(self.width() - self.panel_width, self.panel_y, self.panel_width, self.panel_height)
        else:
            self.theme_panel.setGeometry(self.width(), self.panel_y, self.panel_width, self.panel_height)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_widget = self.childAt(event.pos())
            
            if self.theme_panel.isVisible() and self.theme_panel.geometry().contains(event.pos()):
                return
            
            if clicked_widget == self.close_btn:
                super().mousePressEvent(event)
                return
                
            is_clickable = False
            for btn in self.category_buttons:
                if clicked_widget == btn:
                    is_clickable = True
                    break
            
            if is_clickable:
                super().mousePressEvent(event)
                return
                
            self.is_dragging = True
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            event.accept()

    def show_category_content(self, item_type, is_initial=False):
        if self.selected_category == item_type and not is_initial:
            return
        
        if self.is_submenu_open:
            self.close_submenu()
            QTimer.singleShot(400, lambda: self._show_category_after_close(item_type, is_initial))
        else:
            self._show_category_after_close(item_type, is_initial)

    def _show_category_after_close(self, item_type, is_initial):
        for btn in self.category_buttons:
            if hasattr(btn, 'set_active'):
                btn.set_active(False)
        
        for btn in self.category_buttons:
            if hasattr(btn, 'item_type') and btn.item_type == item_type:
                btn.set_active(True)
                break
        
        self.selected_category = item_type
        
        if not is_initial:
            self.animate_content_transition()
        
        self.fill_content(item_type)

    def animate_content_transition(self):
        opacity_effect = QGraphicsOpacityEffect(self.content_container)
        self.content_container.setGraphicsEffect(opacity_effect)
        
        fade_out = QPropertyAnimation(opacity_effect, b"opacity", self)
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.3)
        
        fade_in = QPropertyAnimation(opacity_effect, b"opacity", self)
        fade_in.setDuration(200)
        fade_in.setStartValue(0.3)
        fade_in.setEndValue(1.0)
        
        seq_animation = QSequentialAnimationGroup(self)
        seq_animation.addAnimation(fade_out)
        seq_animation.addAnimation(fade_in)
        seq_animation.start()

    def fill_content(self, item_type):
        self.content_item_handlers.clear()
        
        for i in reversed(range(self.content_items_layout.count())):
            widget = self.content_items_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
            else:
                item = self.content_items_layout.itemAt(i)
                if item:
                    self.content_items_layout.removeItem(item)
        
        self.content_items.clear()
        
        content_data = {
            "ai": {
                "items": [
                    "Computer assembly",
                    "Artificial intelligence", 
                    "Artificial intelligence vk bot",
                    "TG clothing bot",
                ]
            },
            "vk": {
                "items": [
                    "Artificial intelligence vk bot"
                ]
            },
            "tg": {
                "items": [
                    "TG clothing bot",
                ]
            },
            "app": {
                "items": [
                    "Notes",
                    "Python compiler",
                    "Youtube unblocking"
                ]
            },
            "games": {
                "items": [
                    "Snake",
                    "Game for remodeling"
                ]
            },
            "script": {
                "items": [
                    "Connection",
                    "System"
                ]
            }
        }
        
        if item_type in content_data:
            data = content_data[item_type]
            colors = COLORS if self.dark_mode else {**COLORS, **LIGHT_COLORS}
            
            for item in data["items"]:
                item_label = QLabel(item)
                item_label.setFont(QFont("Segoe UI", 10))
                item_label.setCursor(Qt.CursorShape.PointingHandCursor)
                
                item_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors["text_light"]};
                        padding: 12px 15px;
                        background-color: {colors["light_bg"]};
                        border-radius: 8px;
                        border-left: 3px solid {colors["border"]};
                        margin: 2px;
                        min-height: 40px;
                    }}
                    QLabel:hover {{
                        background-color: {colors["light_bg"]};
                        border-left-color: {colors["accent_green"]};
                        color: {colors["white"]};
                    }}
                """)
                item_label.setWordWrap(True)
                item_label.setMinimumHeight(40)
                
                def create_handler(name):
                    def handler(event):
                        if event.button() == Qt.MouseButton.LeftButton:
                            self.on_content_item_clicked(event, name)
                    return handler
                
                handler = create_handler(item)
                self.content_item_handlers[item] = handler
                item_label.mousePressEvent = handler
                
                self.content_items_layout.addWidget(item_label)
                self.content_items[item] = item_label
            
            self.content_items_layout.addStretch(0)
            self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.content_widget.adjustSize()
            self.content_scroll.ensureVisible(0, 0, 0, 0)

    def on_content_item_clicked(self, event, item_name):
        if event.button() == Qt.MouseButton.LeftButton:
            self.play_sound('file')
            if self.is_submenu_open and self.current_submenu and self.current_submenu.item_name == item_name:
                self.close_submenu()
                return
            
            if self.is_submenu_open:
                self.close_submenu()
            
            self.current_submenu = SubMenuItem(item_name, self.submenu_container)
            self.current_submenu.closed.connect(self.on_submenu_closed)
            self.current_submenu.version_selected.connect(self.show_version_info_panel)
            
            self.open_submenu(item_name)

    def on_submenu_closed(self, item_name):
        self.close_submenu()

    def open_submenu(self, item_name):
        if self.current_submenu is None:
            return
        
        if self.content_animation_group:
            self.content_animation_group.stop()
            self.content_animation_group.deleteLater()
        
        layout = self.submenu_container.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        layout.addWidget(self.current_submenu)
        
        self.submenu_container.show()
        self.submenu_container.raise_()
        
        content_anim = QPropertyAnimation(self.content_container, b"minimumWidth", self)
        content_anim.setDuration(400)
        content_anim.setStartValue(self.original_content_width)
        content_anim.setEndValue(self.small_content_width)
        content_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        submenu_anim = QPropertyAnimation(self.submenu_container, b"minimumWidth", self)
        submenu_anim.setDuration(400)
        submenu_anim.setStartValue(0)
        submenu_anim.setEndValue(240)
        submenu_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.content_animation_group = QParallelAnimationGroup(self)
        self.content_animation_group.addAnimation(content_anim)
        self.content_animation_group.addAnimation(submenu_anim)
        self.content_animation_group.start()
        
        self.is_submenu_open = True
        self.current_submenu_item = item_name

    def close_submenu(self):
        if not self.is_submenu_open:
            return
        
        if self.content_animation_group:
            self.content_animation_group.stop()
            self.content_animation_group.deleteLater()
        
        content_anim = QPropertyAnimation(self.content_container, b"minimumWidth", self)
        content_anim.setDuration(400)
        current_width = self.content_container.width()
        content_anim.setStartValue(current_width)
        content_anim.setEndValue(self.original_content_width)
        content_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        submenu_anim = QPropertyAnimation(self.submenu_container, b"minimumWidth", self)
        submenu_anim.setDuration(400)
        submenu_anim.setStartValue(self.submenu_container.width())
        submenu_anim.setEndValue(0)
        submenu_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        def on_animation_finished():
            self.submenu_container.hide()
            
            layout = self.submenu_container.layout()
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            self.current_submenu = None
            self.is_submenu_open = False
            self.current_submenu_item = None
        
        submenu_anim.finished.connect(on_animation_finished)
        
        self.content_animation_group = QParallelAnimationGroup(self)
        self.content_animation_group.addAnimation(content_anim)
        self.content_animation_group.addAnimation(submenu_anim)
        self.content_animation_group.start()

    def setup_title_animations(self):
        if hasattr(self, 'title_animation_group'):
            self.title_animation_group.stop()
        
        self.title_animation_group = QSequentialAnimationGroup(self)
        
        for i, letter_label in enumerate(self.letter_labels):
            opacity_effect = QGraphicsOpacityEffect(letter_label)
            letter_label.setGraphicsEffect(opacity_effect)
            
            opacity_anim = QPropertyAnimation(opacity_effect, b"opacity", self)
            opacity_anim.setDuration(350)
            opacity_anim.setStartValue(0.0)
            opacity_anim.setEndValue(1.0)
            opacity_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            
            if i > 0:
                pause = QPropertyAnimation(self, b"windowOpacity", self)
                pause.setDuration(100)
                pause.setStartValue(1.0)
                pause.setEndValue(1.0)
                self.title_animation_group.addAnimation(pause)
            
            self.title_animation_group.addAnimation(opacity_anim)
        
        self.title_animation_group.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    app.setStyleSheet(f"""
        * {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
        }}
        QToolTip {{
            display: none !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }}
        QPushButton:focus, QLabel:focus, QWidget:focus {{
            outline: none;
        }}
        QScrollBar {{
            background: transparent;
        }}
        QScrollBar:vertical {{
            width: 8px;
        }}
        QScrollBar::handle:vertical {{
            background: #666;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #888;
        }}
    """)
    
    window = RoundedWindow()
    window.show()
    sys.exit(app.exec())
