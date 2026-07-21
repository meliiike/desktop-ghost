from features.ask_ai import AskAIDialog
import random
import sys
import os
import re

from PyQt6.QtWidgets import QWidget, QLabel, QApplication, QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QGraphicsOpacityEffect, QComboBox, QLineEdit
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QAction, QTransform , QPainter, QPainterPath


from ghost_movement import GhostMovement
from speech_bubble import SpeechBubble
from features.reminder_manager import ReminderManager
from features.task_manager import TaskManager
from features.file_basket import FileBasket
from features.quick_links import QuickLinks


class GhostWindow(QWidget):
    def __init__(self):

        self.data_dir = "user_data"
        os.makedirs(self.data_dir, exist_ok=True)

        self.settings_file = os.path.join(self.data_dir, "ghost_settings.json")

        self.state = "idle"
        self.ghost_size = 150
        self.drag_position = None
        self.was_dragged = False
        self.current_character = "ghost1"

        self.character_original_direction = {
            "ghost1": "left",
            "ghost2": "right",
            "ghost3": "left"
        }


        self.animation_frames = {}
        self.current_frame_index = 0
        self.last_animation_state = "idle"

        super().__init__()

        self.state = "idle"
        self.ghost_size = 150
        self.drag_position = None
        self.was_dragged = False

        self.setup_window()
        self.setup_visual()

        self.speech_bubble = SpeechBubble(self)
        self.movement = GhostMovement(self)
        self.movement.place_on_ground()
        self.setup_animation()

        self.reminder_manager = ReminderManager(self)
        self.task_manager = TaskManager(self)
        self.file_basket = FileBasket(self)
        self.quick_links = QuickLinks(self)
        self.setMouseTracking(True)

        self.speech_timer = QTimer(self)
        self.speech_timer.timeout.connect(self.random_speech)
        self.speech_timer.start(9000)
        # self.keep_on_top_timer = QTimer(self)
        # self.keep_on_top_timer.timeout.connect(self.keep_on_top)
        # self.keep_on_top_timer.start(200)
        #tried to force the ghost be on top always but it stole the focus so I am changing stuff rn but keeping the mistakes, | Melike
        #this issue only belongs to Macbook users bc gokce says theres no problem in windows such as I have | Melike

    def setup_window(self):
        flags = (
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
        )

        if sys.platform == "darwin":
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus

        self.setWindowFlags(flags)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAcceptDrops(True)

    def apply_macos_window_behavior(self):
        if sys.platform != "darwin":
            return

        try:
            import objc
            from AppKit import (
                NSStatusWindowLevel,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorStationary,
                NSWindowCollectionBehaviorIgnoresCycle,
                NSWindowCollectionBehaviorFullScreenAuxiliary
            )

            ns_view = objc.objc_object(c_void_p=int(self.winId()))
            ns_window = ns_view.window()

            if ns_window is not None:
                ns_window.setLevel_(NSStatusWindowLevel)

                # İŞTE KRİTİK NOKTA: Chrome'a, masaüstüne veya başka yere tıklasan bile
                # Ghost'un alta atılmasını ve gizlenmesini engeller.
                ns_window.setHidesOnDeactivate_(False)

                behaviors = (
                        NSWindowCollectionBehaviorCanJoinAllSpaces |
                        NSWindowCollectionBehaviorStationary |
                        NSWindowCollectionBehaviorIgnoresCycle |
                        NSWindowCollectionBehaviorFullScreenAuxiliary
                )
                ns_window.setCollectionBehavior_(behaviors)

        except Exception as error:
            print("macOS window behavior could not be applied:", error)

    def setup_visual(self):
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label.raise_() #label at top

        # Bubble için üstte küçük boşluk
        self.top_space = 25

        self.resize(self.ghost_size, self.ghost_size + self.top_space)

        self.label.resize(self.ghost_size, self.ghost_size)
        self.label.move(0, self.top_space)


        # Hover hint
        self.hover_hint = QLabel("Right click for options", self)
        self.hover_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hover_hint.setStyleSheet("""
            QLabel {
                color: #4A4A4A;
                background-color: rgba(255, 255, 255, 210);
                border: 1px solid #D8D2E8;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 10px;
            }
        """)
        self.hover_hint.adjustSize()
        self.hover_hint.move(18, self.height() - 28)
        self.hover_hint.hide()

    def setup_animation(self):
        self.load_character_frames(self.current_character)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation_frame)
        self.animation_timer.start(160)  # frame speed

        self.update_animation_frame()

    def load_character_frames(self, character_name):
        self.animation_frames = {
            "idle": [],
            "walk": [],
            "jump": [],
            "sleep": []
        }

        def frame_number(file_name):
            match = re.search(r"_(\d+)\.png$", file_name)
            if match:
                return int(match.group(1))
            return -1

        def load_state_frames(state):
            folder = f"assets/{character_name}"

            if not os.path.exists(folder):
                print("Folder not found:", folder)
                return []

            files = []

            for file_name in os.listdir(folder):
                if file_name.startswith(state + "_") and file_name.endswith(".png"):
                    files.append(file_name)

            files.sort(key=frame_number)

            loaded_frames = []

            for file_name in files:
                path = os.path.join(folder, file_name)
                pixmap = QPixmap(path)

                if pixmap.isNull():
                    print("Could not load:", path)
                    continue

                scaled_pixmap = pixmap.scaled(
                    QSize(self.ghost_size, self.ghost_size),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                # Eğer önceki hayalet izini düzeltmek için eklediğimiz canvas fonksiyonu varsa kullan
                if hasattr(self, "fit_pixmap_to_canvas"):
                    scaled_pixmap = self.fit_pixmap_to_canvas(scaled_pixmap)

                loaded_frames.append(scaled_pixmap)

            print(character_name, state, "frames:", files)
            return loaded_frames

        self.animation_frames["idle"] = load_state_frames("idle")
        self.animation_frames["walk"] = load_state_frames("walk")
        self.animation_frames["jump"] = load_state_frames("jump")

        sleep_path = f"assets/{character_name}/sleep.png"
        sleep_pixmap = QPixmap(sleep_path)

        if not sleep_pixmap.isNull():
            scaled_sleep = sleep_pixmap.scaled(
                QSize(self.ghost_size, self.ghost_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            if hasattr(self, "fit_pixmap_to_canvas"):
                scaled_sleep = self.fit_pixmap_to_canvas(scaled_sleep)

            self.animation_frames["sleep"].append(scaled_sleep)

        self.current_frame_index = 0
        self.last_animation_state = "idle"

        print("Loaded frames for", character_name)
        print("idle:", len(self.animation_frames["idle"]))
        print("walk:", len(self.animation_frames["walk"]))
        print("jump:", len(self.animation_frames["jump"]))
        print("sleep:", len(self.animation_frames["sleep"]))

    def update_animation_frame(self):
        self.label.setText("")
        self.label.setStyleSheet("")

        animation_state = self.state

        if animation_state == "dragged":
            animation_state = "idle"

        if animation_state not in self.animation_frames:
            animation_state = "idle"

        frames = self.animation_frames.get(animation_state, [])

        # If this state's frames are missing, use idle frames
        if not frames:
            frames = self.animation_frames.get("idle", [])

        # If even idle frames are missing, show emoji and stop
        if not frames:
            self.label.setText("👻")
            self.label.setStyleSheet(f"font-size: {self.ghost_size}px;")
            self.label.setPixmap(QPixmap())
            return

        if animation_state != self.last_animation_state:
            self.current_frame_index = 0
            self.last_animation_state = animation_state

        if self.current_frame_index >= len(frames):
            self.current_frame_index = 0

        pixmap = frames[self.current_frame_index]

        # Character direction control
        original_direction = self.character_original_direction.get(
            self.current_character,
            "right"
        )

        should_flip = False

        if original_direction == "right":
            # Original sprite looks right, flip only when moving left
            should_flip = self.movement.direction == -1

        elif original_direction == "left":
            # Original sprite looks left, flip only when moving right
            should_flip = self.movement.direction == 1

        if should_flip:
            pixmap = pixmap.transformed(
                QTransform().scale(-1, 1),
                Qt.TransformationMode.SmoothTransformation
            )

        self.label.setPixmap(pixmap)

        self.current_frame_index += 1

        if self.current_frame_index >= len(frames):
            self.current_frame_index = 0

    def random_speech(self):
        if self.state == "sleep" or self.drag_position is not None:
            return

        if random.random() > 0.45:
            return

        messages = [
            "Need a break?",
            "Drop files on me!",
            "I am watching the desktop.",
            "Do not forget your tasks.",
            "Right click me!",
            "I feel useful today."
        ]

        self.speech_bubble.show_message(random.choice(messages), 3500)

    def enterEvent(self, event):
        if self.state != "sleep" and self.drag_position is None:
            self.hover_hint.show()
            self.hover_hint.raise_()
            QTimer.singleShot(1200, self.hover_hint.hide)

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_hint.hide()
        super().leaveEvent(event)


    def is_quick_link_shortcut_pressed(self):
        # Windows: detects Q even if the ghost window does not take keyboard focus.
        if sys.platform == "win32":
            try:
                import ctypes
                return bool(ctypes.windll.user32.GetAsyncKeyState(ord("Q")) & 0x8000)
            except Exception as error:
                print("Shortcut check error:", error)
                return False

        # Fallback for systems where direct key state is not available.
        # On macOS/Linux this may only work while the ghost/app has focus.
        modifiers = QApplication.keyboardModifiers()
        return False


    def is_keyboard_key_pressed(self, key_letter):
        # Windows: detects normal letter keys even if the ghost does not take keyboard focus.
        if sys.platform == "win32":
            try:
                import ctypes
                return bool(ctypes.windll.user32.GetAsyncKeyState(ord(key_letter.upper())) & 0x8000)
            except Exception as error:
                print("Shortcut check error:", error)
                return False

        # macOS/Linux fallback: normal letter keys are not reliable without focus.
        # Use menu/right-click on those systems, or later switch these to Ctrl/Shift shortcuts.
        return False

    def handle_quick_action_shortcut(self):
        # Q + left click -> Quick Links
        if self.is_keyboard_key_pressed("Q"):
            self.open_quick_links()
            return True

        # F + left click -> File Basket / File Exchange
        if self.is_keyboard_key_pressed("F"):
            self.open_file_basket()
            return True

        # A + left click -> full Ask AI
        if self.is_keyboard_key_pressed("A"):
            self.open_ask_ai()
            return True

        return False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Quick Actions:
            # Q + left click -> Quick Links
            # F + left click -> File Basket
            # A + left click -> Ask AI
            if self.handle_quick_action_shortcut():
                self.drag_position = None
                self.was_dragged = False
                event.accept()
                return

            self.state = "dragged"
            self.movement.stop_all_motion()
            self.speech_bubble.hide()

            self.was_dragged = False

            self.drag_position = (
                    event.globalPosition().toPoint()
                    - self.frameGeometry().topLeft()
            )

        elif event.button() == Qt.MouseButton.RightButton:
            self.show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            self.was_dragged = True

            new_pos = event.globalPosition().toPoint() - self.drag_position
            x, y = self.movement.clamp_to_screen(new_pos.x(), new_pos.y())
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

        # Only update ground if user really dragged the ghost
        if self.was_dragged:
            self.movement.base_y = self.y()

        self.was_dragged = False

        if self.state != "sleep":
            self.movement.set_idle()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            self.was_dragged = False

            self.movement.start_jump(35)
            self.speech_bubble.show_message("Hey!", 1500)

    def get_current_theme(self):
        themes = {
            "ghost1": {
                "main": "#1D8CB3",
                "soft": "rgba(210, 244, 255, 190)",
                "border": "#1D8CB3",
                "text": "#123B52",
                "title_bg": "rgba(210, 244, 255, 230)",
                "window_bg": "rgba(255, 253, 235, 245)"
            },
            "ghost2": {
                "main": "#E9A90F",
                "soft": "rgba(255, 238, 170, 190)",
                "border": "#E9A90F",
                "text": "#5A3A00",
                "title_bg": "rgba(255, 228, 125, 230)",
                "window_bg": "rgba(255, 253, 235, 245)"
            },
            "ghost3": {
                "main": "#3D9A4B",
                "soft": "rgba(220, 250, 210, 190)",
                "border": "#3D9A4B",
                "text": "#1D4F2C",
                "title_bg": "rgba(215, 245, 205, 230)",
                "window_bg": "rgba(255, 253, 235, 245)"
            }
        }

        return themes.get(self.current_character, themes["ghost1"])

    def get_dialog_stylesheet(self):
        theme = self.get_current_theme()

        return f"""
        QDialog {{
            background-color: #fdfdf5; /* Kırmızı değil, sabit krem rengi */
            border: 3px solid {theme["border"]};
            border-radius: 18px;
        }}

        QLabel#dialogTitle {{
            background-color: {theme["title_bg"]};
            color: {theme["text"]};
            border: 2px solid {theme["border"]};
            border-radius: 12px;
            padding: 7px 18px;
            font-size: 14px;
            font-weight: bold;
        }}

        QLabel {{
            color: {theme["text"]};
            font-size: 12px;
            font-weight: bold;
        }}

        QLineEdit, QTextEdit, QListWidget, QSpinBox, QTimeEdit {{
            background-color: #ffffff; /* Saf beyaz */
            color: {theme["text"]};
            border: 2px solid #cccccc;
            border-radius: 10px;
            padding: 8px;
        }}

        QComboBox {{
            background-color: #ffffff;
            color: {theme["text"]};
            border: 2px solid #cccccc;
            border-radius: 10px;
            padding: 8px;
            font-weight: bold;
        }}

        QComboBox QAbstractItemView {{
            background-color: #ffffff;
            color: {theme["text"]};
            selection-background-color: #d1d1d1;
            selection-color: {theme["text"]};
            border: 1px solid #cccccc;
        }}

        QPushButton {{
            background-color: #f0f0e0;
            color: {theme["text"]};
            border: 2px solid #cccccc;
            border-radius: 10px;
            padding: 8px 12px;
        }}

        QPushButton:hover {{
            background-color: #e0e0d0;
        }}
        """

    def show_menu(self, position):
        menu = QDialog(self)
        menu.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Popup |
            Qt.WindowType.NoDropShadowWindowHint
        )
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        menu.setFixedWidth(268)

        themes = {
            "ghost1": {
                "main": "#1D8CB3",
                "soft": "rgba(210, 244, 255, 190)",
                "border": "#1D8CB3",
                "text": "#123B52",
                "title_bg": "rgba(210, 244, 255, 230)"
            },
            "ghost2": {
                "main": "#E9A90F",
                "soft": "rgba(255, 238, 170, 190)",
                "border": "#E9A90F",
                "text": "#5A3A00",
                "title_bg": "rgba(255, 228, 125, 230)"
            },
            "ghost3": {
                "main": "#3D9A4B",
                "soft": "rgba(220, 250, 210, 190)",
                "border": "#3D9A4B",
                "text": "#1D4F2C",
                "title_bg": "rgba(215, 245, 205, 230)"
            }
        }

        theme = themes.get(self.current_character, themes["ghost1"])

        menu.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}

            QWidget#menuCard {{
                background-color: rgba(255, 253, 235, 245);
                border: 3px solid {theme["border"]};
                border-radius: 20px;
            }}

            QLabel#menuTitle {{
                background-color: {theme["title_bg"]};
                color: {theme["text"]};
                border: 2px solid {theme["border"]};
                border-radius: 12px;
                padding: 6px 18px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }}

            QPushButton {{
                background-color: rgba(255, 255, 245, 210);
                color: {theme["text"]};
                border: 1px solid rgba(60, 60, 60, 35);
                border-left: 2px solid {theme["border"]};
                border-right: 2px solid {theme["border"]};
                border-radius: 8px;
                padding: 10px 14px;
                text-align: left;
                font-size: 13px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {theme["soft"]};
                border: 2px solid {theme["border"]};
            }}

            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 180);
                padding-left: 15px;
            }}

            QPushButton#quitButton {{
                color: #B84A35;
                border-left: 2px solid #D45A45;
                border-right: 2px solid #D45A45;
            }}

            QPushButton#quitButton:hover {{
                background-color: rgba(255, 220, 205, 220);
                border: 2px solid #D45A45;
            }}

            QLabel#divider {{
                color: {theme["border"]};
                font-size: 10px;
                padding: 0px;
            }}
        """)

        outer_layout = QHBoxLayout(menu)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("menuCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        title = QLabel("QUICK MENU")
        title.setObjectName("menuTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)

        def add_divider():
            divider = QLabel("• • • • • • • • • • • • • • •")
            divider.setObjectName("divider")
            divider.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(divider)

        def add_button(text, callback, quit_button=False):
            button = QPushButton(text)

            if quit_button:
                button.setObjectName("quitButton")

            def clicked():
                menu.close()
                callback()

            button.clicked.connect(clicked)
            layout.addWidget(button)
            return button

        add_button("💬   Talk", self.manual_talk)
        add_button("🎬   Demo Mode", self.demo_mode)
        add_button("✨   Ask AI", self.open_ask_ai)
        add_button("⏰   Add Reminder", self.add_reminder)
        add_button("📋   Daily Tasks", self.open_tasks)
        add_button("📁   File Basket", self.open_file_basket)
        add_button("🔗   Quick Links", self.open_quick_links)

        add_divider()

        add_button("⬆   Jump", lambda: self.movement.start_jump(35))
        add_button("🍃   Go to Ground", self.movement.go_to_ground)
        add_button("☾   Sleep / Wake Up", self.toggle_sleep)

        add_divider()

        add_button("↻   Change Character", self.open_character_selector)
        add_button("✕   Quit", self.quit_app, quit_button=True)

        outer_layout.addWidget(card)

        menu.adjustSize()

        screen = QApplication.primaryScreen().availableGeometry()

        # Menü ghost'un üstüne doğru açılsın
        menu_x = self.x() + (self.width() - menu.width()) // 2
        menu_y = self.y() - menu.height() - 12

        # Eğer üstte yer yoksa ghost'un yanına aç
        if menu_y < screen.top() + 10:
            menu_y = self.y() + 20

        # Ekrandan taşmasın
        if menu_x < screen.left() + 10:
            menu_x = screen.left() + 10

        if menu_x + menu.width() > screen.right() - 10:
            menu_x = screen.right() - menu.width() - 10

        if menu_y + menu.height() > screen.bottom() - 10:
            menu_y = screen.bottom() - menu.height() - 10

        menu.adjustSize()

        screen = QApplication.primaryScreen().availableGeometry()
        gap = 14

        # Menü karakterin üstüne değil, sağ yanına açılsın
        menu_x = self.x() + self.width() + gap
        menu_y = self.y() - 20

        # Sağ tarafta yer yoksa sol tarafa aç
        if menu_x + menu.width() > screen.right() - 10:
            menu_x = self.x() - menu.width() - gap

        # Soldan taşarsa ekran içine al
        if menu_x < screen.left() + 10:
            menu_x = screen.left() + 10

        # Yukarıdan taşarsa biraz aşağı al
        if menu_y < screen.top() + 10:
            menu_y = screen.top() + 10

        # Aşağıdan taşarsa yukarı çek
        if menu_y + menu.height() > screen.bottom() - 10:
            menu_y = screen.bottom() - menu.height() - 10

        menu.move(menu_x, menu_y)
        menu.exec()

    def show_file_drop_animation(self):
        opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(opacity_effect)

        self.flash_animation = QPropertyAnimation(opacity_effect, b"opacity")
        self.flash_animation.setDuration(500)
        self.flash_animation.setStartValue(1.0)
        self.flash_animation.setKeyValueAt(0.4, 0.35)
        self.flash_animation.setKeyValueAt(0.8, 1.0)
        self.flash_animation.setEndValue(1.0)

        self.flash_animation.finished.connect(
            lambda: self.label.setGraphicsEffect(None)
        )

        self.flash_animation.start()

    def make_circle_pixmap(self, image_path, size=72):
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            return QPixmap()

        pixmap = pixmap.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        circle_pixmap = QPixmap(size, size)
        circle_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circle_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, size, size)

        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        return circle_pixmap

    def open_character_selector(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Appearance")
        dialog.setFixedSize(390, 270)
        dialog.setStyleSheet(self.get_dialog_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("APPEARANCE")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)

        characters = [
            ("ghost1", "assets/ghost1/idle_0.png"),
            ("ghost2", "assets/ghost2/idle_0.png"),
            ("ghost3", "assets/ghost3/idle_0.png")
        ]

        for character_name, image_path in characters:
            button = QPushButton()
            button.setFixedSize(100, 86)

            if character_name == self.current_character:
                button.setText("✓")
            else:
                button.setText("")

            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(255, 255, 245, 220);
                    border: 2px solid {"#D45A45" if character_name == self.current_character else "#DAD7CC"};
                    border-radius: 14px;
                    font-size: 18px;
                    font-weight: bold;
                    color: #B84A35;
                    text-align: top right;
                    padding: 4px;
                }}

                QPushButton:hover {{
                    background-color: rgba(230, 248, 252, 230);
                    border: 2px solid #9ACAD6;
                }}
            """)

            icon_label = QLabel(button)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedSize(78, 68)
            icon_label.move(11, 10)

            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(QSize(72, 72), Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                icon_label.setPixmap(pixmap)

            button.clicked.connect(
                lambda checked=False, name=character_name, d=dialog: self.select_character_from_dialog(name, d))
            button_layout.addWidget(button)

        layout.addLayout(button_layout)

        # Boyut seçme
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Ghost Size:"))
        size_box = QComboBox()
        size_box.addItems(["Small (100px)", "Medium (150px)", "Large (200px)", "Extra Large (250px)", "Custom..."])

        # Seçili boyutu ayarla
        sizes = [100, 150, 200, 250]
        if self.ghost_size in sizes:
            size_box.setCurrentIndex(sizes.index(self.ghost_size))
        else:
            size_box.setCurrentIndex(4)

        size_box.activated.connect(lambda index: self.handle_size_selection(index, size_box, dialog))
        size_layout.addWidget(size_box)
        layout.addLayout(size_layout)

        close_button = QPushButton("CLOSE")
        close_button.setObjectName("dangerButton")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()

    def handle_size_selection(self, index, size_box, dialog):
        if index < 4:
            self.resize_character([100, 150, 200, 250][index])
        else:
            from PyQt6.QtWidgets import QInputDialog
            val, ok = QInputDialog.getInt(dialog, "Custom Size", "Pixels (50-500):", self.ghost_size, 50, 500)
            if ok:
                self.resize_character(val)

    def change_character_and_close(self, name, dialog):
        self.change_character(name)
        dialog.close()

    def resize_character(self, new_size):

        self.ghost_size = int(new_size)

        self.resize(self.ghost_size, self.ghost_size + self.top_space)
        self.label.resize(self.ghost_size, self.ghost_size)

        self.load_character_frames(self.current_character)
        self.current_frame_index = 0

        self.speech_bubble.show_message("I am reshaped!", 2000)
        self.movement.start_jump(25)

    def select_character_from_dialog(self, character_name, dialog):
        self.change_character(character_name)
        dialog.close()

    def change_character(self, character_name): #change char
        self.current_character = character_name
        self.load_character_frames(character_name)
        self.current_frame_index = 0
        self.speech_bubble.show_message(f"Changed to {character_name}.", 2000)

    def shake(self, intensity=8, repeat=6):
        original_x = self.x()
        original_y = self.y()

        for i in range(repeat):
            offset = intensity if i % 2 == 0 else -intensity

            QTimer.singleShot(
                i * 60,
                lambda o=offset: self.move(original_x + o, original_y)
            )

        QTimer.singleShot(
            repeat * 60,
            lambda: self.move(original_x, original_y)
        )

    def demo_mode(self):
        if self.state == "sleep":
            self.toggle_sleep()

        self.movement.stop_all_motion()

        steps = [
            ("Hi! I am your desktop ghost.", 0, False),
            ("You can drag me around.", 2500, True),
            ("Drop files on me and I will hold them.", 5000, True),
            ("I can manage your daily tasks.", 7500, False),
            ("I can remind you later.", 10000, True),
            ("You can ask me questions with AI.", 12500, False),
            ("Right click me to explore everything!", 15000, True),
        ]

        for message, delay, jump in steps:
            QTimer.singleShot(
                delay,
                lambda msg=message, should_jump=jump: self.demo_step(msg, should_jump)
            )

    def demo_step(self, message, should_jump=False):
        self.speech_bubble.show_message(message, 2200)

        if should_jump:
            self.movement.start_jump(28)

    def manual_talk(self):
        messages = [
            "Hi! I am your desktop ghost.",
            "I can help with reminders.",
            "Soon I will hold your files.",
            "I am still learning.",
            "Let's be productive."
        ]

        self.speech_bubble.show_message(random.choice(messages), 3500)

    def add_reminder(self):
        self.reminder_manager.open_dialog()

    def open_tasks(self):
        self.task_manager.open_dialog()

    def open_file_basket(self):
        self.file_basket.open_dialog()

    def open_quick_links(self):
        self.quick_links.open_dialog()

    def toggle_sleep(self):
        if self.state == "sleep":
            self.state = "idle"
            self.movement.stop_all_motion()
            self.speech_bubble.show_message("I am awake.", 2500)
            print("Ghost woke up.")

        else:
            self.state = "sleep"
            self.movement.stop_all_motion()
            self.speech_bubble.hide()
            print("Ghost is sleeping.")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()

        added_count = 0

        for url in urls:
            file_path = url.toLocalFile()

            if file_path:
                self.file_basket.add_file(file_path)
                added_count += 1

        if added_count > 0:
            self.show_file_drop_animation()
            self.movement.start_jump(25)
            self.speech_bubble.show_message(
                f"Holding {added_count} file(s).",
                3000
            )

        event.acceptProposedAction()



    def showEvent(self, event):
        super().showEvent(event)
        # PyQt6'nın pencereyi çizme işlemi bittikten 100ms sonra Mac ayarlarını zorluyoruz.
        # Aksi takdirde Qt bizim ayarlarımızı ezip pencereyi alta atabiliyor.
        QTimer.singleShot(100, self.apply_macos_window_behavior)

    def quit_app(self):
        self.speech_timer.stop()
        self.movement.move_timer.stop()
        self.movement.behavior_timer.stop()

        self.close()
        QApplication.quit()

    def open_ask_ai(self):
        dialog = AskAIDialog(self, self)
        dialog.exec()


