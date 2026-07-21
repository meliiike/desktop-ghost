import os
import json
from PyQt6.QtCore import QTimer, Qt, QTime, QDateTime
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QListWidget,
    QMessageBox,
    QComboBox,
    QStackedWidget,
    QTimeEdit,
    QWidget,
    QApplication,
)


class ReminderDialog(QDialog):
    def __init__(self, reminder_manager, parent=None):
        super().__init__(parent)

        self.reminder_manager = reminder_manager

        self.setWindowTitle("Add Reminder")
        self.setFixedSize(440, 500)

        if parent is not None and hasattr(parent, "get_dialog_stylesheet"):
            self.setStyleSheet(parent.get_dialog_stylesheet())

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title = QLabel("ADD REMINDER")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Reminder text")
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Example: Drink water")

        mode_label = QLabel("Reminder type")
        self.mode_box = QComboBox()
        self.mode_box.addItem("After duration")
        self.mode_box.addItem("At clock time")

        self.time_stack = QStackedWidget()
        self.time_stack.setMinimumHeight(75)

        # AFTER DURATION PAGE
        duration_page = QWidget()
        duration_layout = QHBoxLayout()
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(8)

        self.hours_input = QSpinBox()
        self.hours_input.setRange(0, 23)
        self.hours_input.setValue(0)
        self.hours_input.setSuffix(" hour")

        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(0, 59)
        self.minutes_input.setValue(0)
        self.minutes_input.setSuffix(" min")

        self.seconds_input = QSpinBox()
        self.seconds_input.setRange(0, 59)
        self.seconds_input.setValue(10)
        self.seconds_input.setSuffix(" sec")

        duration_layout.addWidget(self.hours_input)
        duration_layout.addWidget(self.minutes_input)
        duration_layout.addWidget(self.seconds_input)
        duration_page.setLayout(duration_layout)

        # CLOCK TIME PAGE
        clock_page = QWidget()
        clock_layout = QVBoxLayout()
        clock_layout.setContentsMargins(0, 0, 0, 0)
        clock_layout.setSpacing(6)

        self.clock_input = QTimeEdit()
        self.clock_input.setDisplayFormat("HH:mm")
        self.clock_input.setTime(QTime.currentTime().addSecs(60))

        clock_hint = QLabel("If the time already passed today, it will remind tomorrow.")
        clock_hint.setStyleSheet("font-size: 10px; font-weight: normal;")

        clock_layout.addWidget(self.clock_input)
        clock_layout.addWidget(clock_hint)
        clock_page.setLayout(clock_layout)

        self.time_stack.addWidget(duration_page)
        self.time_stack.addWidget(clock_page)

        self.mode_box.currentIndexChanged.connect(self.time_stack.setCurrentIndex)

        active_label = QLabel("Active reminders")
        self.reminder_list = QListWidget()
        self.refresh_list()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        add_button = QPushButton("＋ SAVE")
        close_button = QPushButton("CLOSE")
        close_button.setObjectName("dangerButton")

        add_button.clicked.connect(self.add_reminder)
        close_button.clicked.connect(self.close)

        button_layout.addWidget(add_button)
        button_layout.addWidget(close_button)

        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(text_label)
        layout.addWidget(self.text_input)
        layout.addWidget(mode_label)
        layout.addWidget(self.mode_box)
        layout.addWidget(self.time_stack)
        layout.addWidget(active_label)
        layout.addWidget(self.reminder_list)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_reminder(self):
        text = self.text_input.text().strip()

        if not text:
            QMessageBox.warning(self, "Missing Text", "Please write a reminder text.")
            return

        selected_mode = self.mode_box.currentIndex()

        # Mode 0: after duration
        if selected_mode == 0:
            hours = self.hours_input.value()
            minutes = self.minutes_input.value()
            seconds = self.seconds_input.value()

            total_seconds = hours * 3600 + minutes * 60 + seconds

            if total_seconds <= 0:
                QMessageBox.warning(
                    self,
                    "Invalid Time",
                    "Please choose a time longer than 0 seconds."
                )
                return

            time_label = self.format_duration(hours, minutes, seconds)

        # Mode 1: exact clock time
        else:
            now = QDateTime.currentDateTime()
            selected_time = self.clock_input.time()

            target = QDateTime(
                now.date(),
                selected_time
            )

            if target <= now:
                target = target.addDays(1)

            total_seconds = now.secsTo(target)
            time_label = f"at {selected_time.toString('HH:mm')}"

        self.reminder_manager.add_reminder(text, total_seconds, time_label)

        self.text_input.clear()
        self.refresh_list()

    def format_duration(self, hours, minutes, seconds):
        parts = []

        if hours > 0:
            parts.append(f"{hours}h")

        if minutes > 0:
            parts.append(f"{minutes}m")

        if seconds > 0:
            parts.append(f"{seconds}s")

        return "after " + " ".join(parts)

    def refresh_list(self):
        self.reminder_list.clear()

        reminders = self.reminder_manager.get_active_reminders()

        if not reminders:
            self.reminder_list.addItem("No active reminders.")
            return

        for reminder in reminders:
            self.reminder_list.addItem(reminder)


class ReminderManager:
    def __init__(self, ghost):
        self.ghost = ghost

        # Klasörü oluştur
        self.data_dir = "user_data"
        os.makedirs(self.data_dir, exist_ok=True)

        # Dosya yolu
        self.data_file = os.path.join(self.data_dir, "reminders.json")

        self.active_reminders = []
        self.timers = {}

        self.load_data()

    def load_data(self):
        """JSON dosyasından hatırlatıcıları yükler ve zamanı gelmeyenleri tekrar kurar."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    saved_reminders = json.load(f)

                current_time = QDateTime.currentSecsSinceEpoch()

                for rem in saved_reminders:
                    target_time = rem.get("target_time", 0)
                    text = rem.get("text", "")
                    reminder_text = rem.get("reminder_text", "")

                    if target_time > current_time:

                        remaining_secs = target_time - current_time
                        self.active_reminders.append(reminder_text)
                        self._start_timer(text, reminder_text, remaining_secs)
            except Exception as error:
                print("Hatırlatıcılar yüklenemedi:", error)

    def save_data(self, all_reminders_data):
        """Tüm aktif hatırlatıcıların datalarını kaydeder."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(all_reminders_data, f, indent=4)
        except Exception as error:
            print("Hatırlatıcılar kaydedilemedi:", error)

    def open_dialog(self):
        dialog = ReminderDialog(self, self.ghost)
        dialog.exec()

    def add_reminder(self, text, seconds, time_label=None):
        if time_label is None:
            time_label = f"in {seconds} seconds"

        reminder_text = f"{text} - {time_label}"
        self.active_reminders.append(reminder_text)

        self.ghost.speech_bubble.show_message(
            f"Okay, I will remind you: {text}",
            3000
        )

        current_time = QDateTime.currentSecsSinceEpoch()
        target_time = current_time + seconds

        all_reminders = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    all_reminders = json.load(f)
            except:
                pass

        all_reminders.append({
            "text": text,
            "reminder_text": reminder_text,
            "target_time": target_time
        })
        self.save_data(all_reminders)

        self._start_timer(text, reminder_text, seconds)

    def _start_timer(self, text, reminder_text, seconds):
        """Timer oluşturma işlemini ayrı bir fonksiyona aldık."""
        timer = QTimer(self.ghost)
        timer.setSingleShot(True)
        self.timers[reminder_text] = timer

        timer.timeout.connect(lambda: self.trigger_reminder(text, reminder_text, timer))
        timer.start(seconds * 1000)

    def trigger_reminder(self, text, reminder_text, timer):
        if reminder_text in self.active_reminders:
            self.active_reminders.remove(reminder_text)

        # JSON'dan silme işlemi
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    all_reminders = json.load(f)
                # Süresi biteni listeden çıkar ve tekrar kaydet
                all_reminders = [r for r in all_reminders if r.get("reminder_text") != reminder_text]
                self.save_data(all_reminders)
            except:
                pass

        if reminder_text in self.timers:
            del self.timers[reminder_text]

        self.ghost.speech_bubble.show_message(f"Reminder: {text}", 6000)
        QApplication.beep()

        self.ghost.movement.start_jump(35)

        if hasattr(self.ghost, "shake"):
            self.ghost.shake(intensity=10, repeat=8)

        QTimer.singleShot(450, lambda: self.ghost.movement.start_jump(28))
        QTimer.singleShot(900, lambda: self.ghost.speech_bubble.show_message(f"Hey! {text}", 3500))

        timer.deleteLater()

    def get_active_reminders(self):
        return self.active_reminders