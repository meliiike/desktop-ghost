import os
from pathlib import Path
import json
import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QWidget,
)


class QuickLinksSideList(QDialog):
    def __init__(self, quick_links, parent=None):
        super().__init__(parent)

        self.drag_position = None

        self.quick_links = quick_links
        self.ghost = parent

        self.setWindowTitle("Quick Links")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Popup |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(245)

        theme = self.ghost.get_current_theme() if self.ghost and hasattr(self.ghost, "get_current_theme") else {
            "border": "#1D8CB3",
            "text": "#123B52",
            "soft": "rgba(210, 244, 255, 190)",
            "title_bg": "rgba(210, 244, 255, 230)"
        }

        self.setStyleSheet(f"""
            QDialog {{
                background-color: transparent;
            }}

            QWidget#quickCard {{
                background-color: rgba(255, 253, 235, 245);
                border: 3px solid {theme["border"]};
                border-radius: 18px;
            }}

            QLabel#quickTitle {{
                background-color: {theme["title_bg"]};
                color: {theme["text"]};
                border: 2px solid {theme["border"]};
                border-radius: 11px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}

            QPushButton {{
                background-color: rgba(255, 255, 245, 220);
                color: {theme["text"]};
                border: 1px solid rgba(60, 60, 60, 35);
                border-left: 2px solid {theme["border"]};
                border-right: 2px solid {theme["border"]};
                border-radius: 8px;
                padding: 9px 10px;
                text-align: left;
                font-size: 12px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {theme["soft"]};
                border: 2px solid {theme["border"]};
            }}

            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 180);
                padding-left: 12px;
            }}

            QPushButton#manageButton {{
                text-align: center;
                color: {theme["text"]};
                border: 2px solid {theme["border"]};
            }}

            QPushButton#closeButton {{
                text-align: center;
                color: #B84A35;
                border: 2px solid #D45A45;
            }}

            QPushButton#closeButton:hover {{
                background-color: rgba(255, 220, 205, 220);
            }}

            QLabel#emptyLabel {{
                color: {theme["text"]};
                font-size: 11px;
                font-weight: bold;
                padding: 8px;
            }}
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("quickCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(7)

        title = QLabel("QUICK LINKS")
        title.setObjectName("quickTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        links = self.quick_links.get_links()

        if not links:
            empty = QLabel("No quick links yet.")
            empty.setObjectName("emptyLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
        else:
            for link in links[:8]:
                button = QPushButton(f"🔗  {link['name']}")
                button.setToolTip(link["url"])
                button.clicked.connect(lambda checked=False, url=link["url"]: self.open_and_close(url))
                layout.addWidget(button)

        manage_button = QPushButton("＋ ADD / MANAGE")
        manage_button.setObjectName("manageButton")
        manage_button.clicked.connect(self.open_manage_dialog)

        close_button = QPushButton("CLOSE")
        close_button.setObjectName("closeButton")
        close_button.clicked.connect(self.close)

        layout.addWidget(manage_button)
        layout.addWidget(close_button)

        outer_layout.addWidget(card)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = None
            event.accept()

    def open_and_close(self, url):
        self.quick_links.open_link(url)
        self.close()

    def open_manage_dialog(self):
        self.close()
        self.quick_links.open_manage_dialog()

    def open_and_close(self, url):
        self.quick_links.open_link(url)
        self.close()

    def open_manage_dialog(self):
        self.close()
        self.quick_links.open_manage_dialog()


class QuickLinksManageDialog(QDialog):
    def __init__(self, quick_links, parent=None):
        super().__init__(parent)

        self.quick_links = quick_links
        self.setWindowTitle("Manage Quick Links")
        self.setFixedSize(430, 420)

        if parent is not None and hasattr(parent, "get_dialog_stylesheet"):
            self.setStyleSheet(parent.get_dialog_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("MANAGE QUICK LINKS")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel("Link name")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Example: GitHub")

        url_label = QLabel("Website URL")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Example: https://github.com")

        self.link_list = QListWidget()
        self.refresh_list()

        top_buttons = QHBoxLayout()
        top_buttons.setSpacing(8)

        add_button = QPushButton("＋ ADD")
        open_button = QPushButton("OPEN")
        remove_button = QPushButton("REMOVE")

        add_button.clicked.connect(self.add_link)
        open_button.clicked.connect(self.open_selected_link)
        remove_button.clicked.connect(self.remove_selected_link)

        top_buttons.addWidget(add_button)
        top_buttons.addWidget(open_button)
        top_buttons.addWidget(remove_button)

        close_button = QPushButton("CLOSE")
        close_button.setObjectName("dangerButton")
        close_button.clicked.connect(self.close)

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(QLabel("Saved links"))
        layout.addWidget(self.link_list)
        layout.addLayout(top_buttons)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def show_warning(self, title, message):
        warning = QMessageBox(self)
        warning.setWindowTitle(title)
        warning.setText(message)
        warning.setIcon(QMessageBox.Icon.Warning)
        warning.setStyleSheet("""
            QMessageBox {
                background-color: #F8F7F2;
            }

            QLabel {
                color: #2F3A3D;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #FFFFFF;
                color: #2F3A3D;
                border: 1px solid #DAD7CC;
                border-radius: 9px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: bold;
                min-width: 70px;
            }

            QPushButton:hover {
                background-color: #EAF6F8;
                border: 1px solid #9ACAD6;
            }
        """)
        warning.exec()

    def normalize_url(self, url):
        url = url.strip()

        if not url:
            return ""

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        return url

    def add_link(self):
        name = self.name_input.text().strip()
        url = self.normalize_url(self.url_input.text())

        if not name:
            self.show_warning("Missing Name", "Please write a link name.")
            return

        if not url:
            self.show_warning("Missing URL", "Please write a website URL.")
            return

        self.quick_links.add_link(name, url)
        self.name_input.clear()
        self.url_input.clear()
        self.refresh_list()

    def open_selected_link(self):
        selected_item = self.link_list.currentItem()

        if selected_item is None:
            self.show_warning("No Selection", "Please select a link.")
            return

        link = selected_item.data(Qt.ItemDataRole.UserRole)

        if not link:
            self.show_warning("Invalid Link", "This link could not be opened.")
            return

        self.quick_links.open_link(link["url"])

    def remove_selected_link(self):
        selected_item = self.link_list.currentItem()

        if selected_item is None:
            self.show_warning("No Selection", "Please select a link.")
            return

        link = selected_item.data(Qt.ItemDataRole.UserRole)

        if not link:
            return

        self.quick_links.remove_link(link["name"], link["url"])
        self.refresh_list()

    def refresh_list(self):
        self.link_list.clear()

        links = self.quick_links.get_links()

        if not links:
            empty_item = QListWidgetItem("No quick links yet.")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.link_list.addItem(empty_item)
            return

        for link in links:
            item = QListWidgetItem(f"🔗  {link['name']}  —  {link['url']}")
            item.setData(Qt.ItemDataRole.UserRole, link)
            self.link_list.addItem(item)


class QuickLinks:
    def __init__(self, ghost):
        self.ghost = ghost

        self.data_dir = "user_data"
        os.makedirs(self.data_dir, exist_ok=True)

        self.storage_path = Path(self.data_dir) / "quick_links.json"

        self.default_links = [

            {"name": "ChatGPT",
                "url": "https://chatgpt.com"
            },
            {"name": "Gmail",
                "url": "https://mail.google.com"
            },
            {"name": "GitHub",
                "url": "https://github.com"
            },
            {"name": "YouTube",
                "url": "https://youtube.com"
            }
        ]

        self.links = self.load_links()

    def open_dialog(self):
        side_list = QuickLinksSideList(self, self.ghost)
        side_list.adjustSize()

        screen = QApplication.primaryScreen().availableGeometry()
        gap = 14

        x = self.ghost.x() + self.ghost.width() + gap
        y = self.ghost.y() + 8

        if x + side_list.width() > screen.right() - 10:
            x = self.ghost.x() - side_list.width() - gap

        if x < screen.left() + 10:
            x = screen.left() + 10

        if y < screen.top() + 10:
            y = screen.top() + 10

        if y + side_list.height() > screen.bottom() - 10:
            y = screen.bottom() - side_list.height() - 10

        side_list.move(x, y)
        side_list.exec()

    def open_manage_dialog(self):
        dialog = QuickLinksManageDialog(self, self.ghost)
        dialog.exec()

    def load_links(self):
        if not self.storage_path.exists():
            return self.default_links.copy()

        try:
            with open(self.storage_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                cleaned_links = []

                for item in data:
                    if isinstance(item, dict) and "name" in item and "url" in item:
                        cleaned_links.append({
                            "name": str(item["name"]),
                            "url": str(item["url"])
                        })

                if cleaned_links:
                    return cleaned_links

        except Exception as error:
            print("Quick links could not be loaded:", error)

        return self.default_links.copy()

    def save_links(self):
        try:
            with open(self.storage_path, "w", encoding="utf-8") as file:
                json.dump(self.links, file, indent=4, ensure_ascii=False)

        except Exception as error:
            print("Quick links could not be saved:", error)
            self.ghost.speech_bubble.show_message("Could not save quick links.", 3000)

    def get_links(self):
        return self.links

    def add_link(self, name, url):
        for link in self.links:
            if link["url"] == url:
                self.ghost.speech_bubble.show_message("This link already exists.", 3000)
                return

        self.links.append({
            "name": name,
            "url": url
        })

        self.save_links()

        self.ghost.speech_bubble.show_message(
            f"Quick link added: {name}",
            3000
        )

    def remove_link(self, name, url):
        self.links = [
            link for link in self.links
            if not (link["name"] == name and link["url"] == url)
        ]

        self.save_links()

        self.ghost.speech_bubble.show_message(
            f"Removed: {name}",
            3000
        )

    def open_link(self, url):
        try:
            webbrowser.open(url)

            self.ghost.speech_bubble.show_message(
                "Opening quick link...",
                2500
            )

        except Exception as error:
            print("Quick link open error:", error)
            self.ghost.speech_bubble.show_message(
                "Could not open link.",
                3000
            )
