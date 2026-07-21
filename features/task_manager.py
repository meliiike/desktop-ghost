import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QMessageBox
)


class TaskDialog(QDialog):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)

        self.task_manager = task_manager

        self.setWindowTitle("Daily Tasks")
        self.setFixedSize(420, 390)

        if parent is not None and hasattr(parent, "get_dialog_stylesheet"):
            self.setStyleSheet(parent.get_dialog_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("DAILY TASKS")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        input_label = QLabel("New task")
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Example: Finish project proposal")

        self.task_list = QListWidget()
        self.refresh_list()

        top_button_layout = QHBoxLayout()
        top_button_layout.setSpacing(10)

        add_button = QPushButton("＋ ADD")
        remind_button = QPushButton("REMIND NEXT")

        add_button.clicked.connect(self.add_task)
        remind_button.clicked.connect(self.remind_next_task)

        top_button_layout.addWidget(add_button)
        top_button_layout.addWidget(remind_button)

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.setSpacing(10)

        complete_button = QPushButton("✓ COMPLETE")
        close_button = QPushButton("CLOSE")
        close_button.setObjectName("dangerButton")

        complete_button.clicked.connect(self.complete_selected_task)
        close_button.clicked.connect(self.close)

        bottom_button_layout.addWidget(complete_button)
        bottom_button_layout.addWidget(close_button)

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(input_label)
        layout.addWidget(self.task_input)
        layout.addLayout(top_button_layout)
        layout.addWidget(QLabel("Today's tasks"))
        layout.addWidget(self.task_list)
        layout.addLayout(bottom_button_layout)

        self.setLayout(layout)

    def add_task(self):
        task_text = self.task_input.text().strip()

        if not task_text:
            QMessageBox.warning(self, "Missing Task", "Please write a task.")
            return

        self.task_manager.add_task(task_text)

        self.task_input.clear()
        self.refresh_list()

    def complete_selected_task(self):
        selected_item = self.task_list.currentItem()

        if selected_item is None:
            QMessageBox.warning(self, "No Selection", "Please select a task.")
            return

        task_text = selected_item.text()

        task_text = task_text.replace("[ ] ", "").replace("[✓] ", "")

        self.task_manager.complete_task(task_text)
        self.refresh_list()

    def remind_next_task(self):
        self.task_manager.remind_next_task()

    def refresh_list(self):
        self.task_list.clear()

        tasks = self.task_manager.get_tasks()

        if not tasks:
            self.task_list.addItem("No tasks yet.")
            return

        for task in tasks:
            if task["done"]:
                self.task_list.addItem(f"[✓] {task['text']}")
            else:
                self.task_list.addItem(f"[ ] {task['text']}")


class TaskManager:
    def __init__(self, ghost):
        self.ghost = ghost

        # Klasör mimarisi oluşturuluyor
        self.data_dir = "user_data"
        os.makedirs(self.data_dir, exist_ok=True)

        # JSON dosyasının yolu ayarlanıyor
        self.data_file = os.path.join(self.data_dir, "tasks.json")

        # Başlangıçta kayıtlı görevleri yükle
        self.tasks = self.load_data()

    def load_data(self):
        """JSON dosyasından kayıtlı görevleri yükler."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as error:
                print("Görev verisi yüklenemedi:", error)
        return []

    def save_data(self):
        """Mevcut görevleri JSON dosyasına kaydeder."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=4)
        except Exception as error:
            print("Görev verisi kaydedilemedi:", error)

    def open_dialog(self):
        dialog = TaskDialog(self, self.ghost)
        dialog.exec()

    def add_task(self, task_text):
        task = {
            "text": task_text,
            "done": False
        }

        self.tasks.append(task)
        self.save_data()  # JSON'a anında kayıt

        self.ghost.speech_bubble.show_message(
            f"Task added: {task_text}",
            3000
        )

    def complete_task(self, task_text):
        for task in self.tasks:
            if task["text"] == task_text and not task["done"]:
                task["done"] = True
                self.save_data()  # Değişikliği anında kaydet

                self.ghost.speech_bubble.show_message(
                    "Good job! Task completed.",
                    3000
                )

                self.ghost.movement.start_jump(30)
                return

        self.ghost.speech_bubble.show_message(
            "This task is already completed.",
            3000
        )

    def remind_next_task(self):
        for task in self.tasks:
            if not task["done"]:
                self.ghost.speech_bubble.show_message(
                    f"Next task: {task['text']}",
                    5000
                )
                return

        self.ghost.speech_bubble.show_message(
            "All tasks are completed!",
            4000
        )

    def get_tasks(self):
        return self.tasks