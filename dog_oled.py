import time
from kmk.extensions import Extension


class DogOLED(Extension):
    WIDTH = 128
    HEIGHT = 32

    def __init__(self, pose_seconds=0.65):
        self.pose_seconds = pose_seconds
        self.display = None
        self.frames = {}
        self.pose = "sleep"
        self.until = 0
        self.dirty = True
        self.last_draw = -1
        self.sleep_phase = -1
        self.i2c = None
        self.status = None
        self.status_until = 0

    def during_bootup(self, keyboard):
        try:
            import board
            import busio
            import adafruit_ssd1306
            from artwork import load_frames
            self.frames = load_frames()
            self.i2c = busio.I2C(board.D5, board.D4, frequency=400000)
            if not self.i2c.try_lock():
                raise RuntimeError("OLED I2C bus unavailable")
            try:
                found = [a for a in self.i2c.scan() if a in (0x3C, 0x3D)]
            finally:
                self.i2c.unlock()
            if len(found) != 1:
                raise RuntimeError("Expected one OLED at 0x3C or 0x3D")
            self.display = adafruit_ssd1306.SSD1306_I2C(
                self.WIDTH, self.HEIGHT, self.i2c, addr=found[0]
            )
        except Exception as error:
            self.display = None
            if self.i2c is not None:
                self.i2c.deinit()
                self.i2c = None
            print("OLED disabled; keys still work:", error)

    def tip(self, direction):
        self.status = None
        self.pose = "left" if direction < 0 else "right"
        self.until = time.monotonic() + self.pose_seconds
        self.dirty = True

    def message(self, name, seconds=1.4):
        self.status = "status_" + name
        self.status_until = time.monotonic() + seconds
        self.dirty = True

    def mode_message(self, number):
        glyphs = {
            "M": (17, 27, 21, 17, 17), "O": (7, 5, 5, 5, 7),
            "D": (6, 5, 5, 5, 6), "E": (7, 4, 6, 4, 7),
            "1": (2, 6, 2, 2, 7), "2": (7, 1, 7, 4, 7),
            "3": (7, 1, 7, 1, 7), "4": (5, 5, 7, 1, 1),
            "5": (7, 4, 7, 1, 7), "6": (7, 4, 7, 5, 7),
            "7": (7, 1, 1, 1, 1), "8": (7, 5, 7, 5, 7),
            "9": (7, 5, 7, 1, 7),
        }
        frame = bytearray(512)
        x_start = 38
        for char in "MODE" + str(number):
            width = 5 if char == "M" else 3
            for y, bits in enumerate(glyphs[char]):
                for x in range(width):
                    if bits & (1 << (width - x - 1)):
                        for dy in range(2):
                            for dx in range(2):
                                px = x_start + 2 * x + dx
                                py = 11 + 2 * y + dy
                                frame[(py // 8) * 128 + px] |= 1 << (py % 8)
            x_start += 2 * width + (10 if char == "E" else 2)
        self.frames["status_mode"] = frame
        self.message("mode", 1.6)

    def after_hid_send(self, keyboard):
        if self.display is None:
            return
        now = time.monotonic()
        if self.status is not None and now >= self.status_until:
            self.status = None
            self.dirty = True
        if self.pose != "sleep" and now >= self.until:
            self.pose = "sleep"
            self.dirty = True
        phase = int(now / 0.5) % 4
        if self.status is None and self.pose == "sleep" and phase != self.sleep_phase:
            self.sleep_phase = phase
            self.dirty = True
        if not self.dirty or now - self.last_draw < 0.08:
            return
        try:
            frame_name = "sleep" + str(self.sleep_phase) if self.pose == "sleep" else self.pose
            if self.status is not None:
                frame_name = self.status
            frame = self.frames[frame_name]
            self.display.buffer[1:] = frame
            self.display.show()
            self.last_draw = now
            self.dirty = False
        except Exception as error:
            self.display = None
            print("OLED stopped; keys still work:", error)

    def on_runtime_enable(self, keyboard):
        pass

    def on_runtime_disable(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        pass

    def after_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def deinit(self, keyboard):
        if self.i2c is not None:
            self.i2c.deinit()
            self.i2c = None
