import random
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


class GhostMovement:
    def __init__(self, ghost):
        self.ghost = ghost

        self.direction = random.choice([-1, 1])
        self.speed = 0

        self.is_jumping = False
        self.jump_phase = 0
        self.jump_height = 0

        self.base_y = 0

        self.move_timer = QTimer(self.ghost)
        self.move_timer.timeout.connect(self.update_movement)
        self.move_timer.start(40)

        self.behavior_timer = QTimer(self.ghost)
        self.behavior_timer.timeout.connect(self.choose_behavior)
        self.behavior_timer.start(2500)

    def get_screen_geometry(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def ground_y(self):
        screen = self.get_screen_geometry()

        if screen is None:
            return 600

        return screen.y() + screen.height() - self.ghost.height() - 30

    def place_on_ground(self):
        screen = self.get_screen_geometry()

        if screen is None:
            self.base_y = 600
            self.ghost.move(500, self.base_y)
            return

        min_x = screen.x() + 50
        max_x = screen.x() + screen.width() - self.ghost.width() - 50

        if max_x <= min_x:
            start_x = screen.x() + 50
        else:
            start_x = random.randint(min_x, max_x)

        self.base_y = self.ground_y()
        self.ghost.move(start_x, self.base_y)

    def clamp_to_screen(self, x, y):
        screen = self.get_screen_geometry()

        if screen is None:
            return x, y

        min_x = screen.x()
        max_x = screen.x() + screen.width() - self.ghost.width()

        min_y = screen.y()
        max_y = screen.y() + screen.height() - self.ghost.height()

        x = max(min_x, min(x, max_x))
        y = max(min_y, min(y, max_y))

        return x, y

    def update_movement(self):
        if self.ghost.state == "sleep" or self.ghost.drag_position is not None:
            return

        x = self.ghost.x()
        y = self.base_y

        screen = self.get_screen_geometry()

        if screen is None:
            return

        if self.ghost.state == "walk":
            x += self.speed * self.direction

            left_edge = screen.x()
            right_edge = screen.x() + screen.width() - self.ghost.width()

            if x <= left_edge:
                x = left_edge
                self.direction = 1

            elif x >= right_edge:
                x = right_edge
                self.direction = -1

        if self.is_jumping:
            self.jump_phase += 0.20

            jump_offset = int(math.sin(self.jump_phase) * self.jump_height)

            if jump_offset < 0:
                jump_offset = 0

            y = self.base_y - jump_offset

            if self.jump_phase >= math.pi:
                self.finish_jump()
                y = self.base_y

        x, y = self.clamp_to_screen(x, y)
        self.ghost.move(x, y)

    def choose_behavior(self):
        if self.ghost.state in ["sleep", "dragged", "jump"]:
            return

        if self.ghost.drag_position is not None:
            return

        behavior = random.choice([
            "idle",
            "idle",
            "idle",
            "idle",
            "idle",
            "walk",
            "walk",
            "turn",
            "small_jump"
        ])

        if behavior == "idle":
            self.set_idle()

        elif behavior == "walk":
            self.start_walking()

        elif behavior == "turn":
            self.direction *= -1
            self.set_idle()

        elif behavior == "small_jump":
            self.start_jump(random.choice([14, 18, 22]))

    def set_idle(self):
        if self.ghost.state != "sleep":
            self.ghost.state = "idle"
            self.speed = 0

    def start_walking(self):
        if self.ghost.state in ["sleep", "jump", "dragged"]:
            return

        self.ghost.state = "walk"
        self.speed = random.choice([1, 2])

        walk_time = random.randint(1000, 2200)
        QTimer.singleShot(walk_time, self.stop_walking)

    def stop_walking(self):
        if self.ghost.state == "walk":
            self.set_idle()

    def start_jump(self, height=35):
        if self.ghost.state in ["sleep", "dragged"]:
            return

        self.ghost.state = "jump"
        self.is_jumping = True
        self.jump_phase = 0
        self.jump_height = height
        self.speed = 0

    def finish_jump(self):
        self.is_jumping = False
        self.jump_phase = 0
        self.jump_height = 0

        if self.ghost.state != "sleep":
            self.set_idle()

    def go_to_ground(self):
        x = self.ghost.x()
        y = self.ground_y()

        x, y = self.clamp_to_screen(x, y)

        self.base_y = y
        self.ghost.move(x, y)
        self.set_idle()

    def stop_all_motion(self):
        self.speed = 0
        self.is_jumping = False