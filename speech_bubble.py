from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel


class SpeechBubble(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                border: 2px solid black;
                border-radius: 13px;
                padding: 5px;
                font-size: 12px;
            }
        """)

        self.hide()

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def show_message(self, text, duration=3000):
        if len(text) > 55:
            text = text[:55] + "..."

        self.setText(text)
        self.adjustSize()

        bubble_width = min(max(self.width(), 120), 190)
        bubble_height = self.height()

        self.resize(bubble_width, bubble_height)

        if self.parent() is not None:
            bubble_x = int((self.parent().width() - bubble_width) / 2) + 11
        else:
            bubble_x = 0

        bubble_y = -1

        self.move(bubble_x, bubble_y)
        self.show()
        self.raise_()

        self.timer.start(duration)