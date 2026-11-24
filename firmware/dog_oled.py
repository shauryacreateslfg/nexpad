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
        messages = {
            "spotify": "Opening Spotify", "youtube": "Opening YouTube",
            "claude": "Opening Claude", "github": "Opening GitHub",
            "vscode": "Opening VS Code", "copy": "Copy sent",
            "paste": "Paste sent", "snip": "Snipping tool",
            "command": "Command sent", "accept": "Enter sent",
            "caps": "Caps Lock is on",
        }
        self.status = messages.get(name, name)
        self.status_until = time.monotonic() + seconds
        self.dirty = True

    def mode_message(self, number):
        self.message("MODE " + str(number), 1.6)

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
            if self.status is not None:
                self.display.fill(0)
                self.display.text(self.status, 4, 12, 1,
                                  font_name="/font5x8.bin")
            else:
                frame_name = "sleep" + str(self.sleep_phase) if self.pose == "sleep" else self.pose
                self.display.buffer[1:] = self.frames[frame_name]
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
