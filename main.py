import sys
from PyQt6.QtWidgets import QApplication
from ghost_window import GhostWindow


def main():
    app = QApplication(sys.argv)

    ghost = GhostWindow()
    ghost.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()