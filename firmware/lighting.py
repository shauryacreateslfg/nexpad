import random
import time
from kmk.modules import Module
from kmk.keys import make_key


MODE_NAMES = ("Off", "White reactive", "Red-orange", "Cyan", "Green",
              "Blue", "Purple", "Rainbow", "Random reactive")
FAMILIES = ((0, 22), (118, 137), (72, 98), (155, 176), (188, 212))


def colour(hue, value):
    hue = (hue % 256) * 6
    sector = hue // 256
    rising = (hue % 256) * value // 255
    falling = value - rising
    return ((value, rising, 0), (falling, value, 0),
            (0, value, rising), (0, falling, value),
            (rising, 0, value), (value, 0, falling))[sector]


class Lighting(Module):
    def __init__(self, dog, brightness=32, cycle_seconds=12):
        self.dog = dog
        self.brightness = max(0, min(int(brightness), 32))
        self.cycle_seconds = max(2, cycle_seconds)
        self.mode = 8
        self.pixels = None
        self.last_draw = -1
        self.hues = [0] * 9
        self.pressed_at = [-100.0] * 9
        self.keys = []
        self.down_keys = set()
        self.chord_down = False
        self.chord_used = False
        self.tap_key = None
        self.chord_key = make_key(
            names=("NEXPAD_LIGHTING",),
            on_press=self._pressed,
            on_release=self._released,
        )

    def bind(self, keys, hold_label):
        self.tap_key = keys[hold_label]
        keys[hold_label] = self.chord_key
        self.keys = [keys[i] for i in range(1, 10)]

    def _pressed(self, key, keyboard, *args):
        if not self.chord_down:
            self.chord_down = True
            self.chord_used = False

    def _released(self, key, keyboard, *args):
        if not self.chord_down:
            return
        self.chord_down = False
        if not self.chord_used:
            self.tap_key.on_press(keyboard)
            self.tap_key.on_release(keyboard)

    def turn(self, direction):
        if not self.chord_down:
            return False
        self.chord_used = True
        step = 1 if direction > 0 else -1
        self.mode = ((self.mode - 1 + step) % 9) + 1
        self.pressed_at = [-100.0] * 9
        self.last_draw = -1
        self.dog.mode_message(self.mode)
        return True

    def process_key(self, keyboard, key, is_pressed, int_coord):
        if key in self.keys:
            index = self.keys.index(key)
            if is_pressed and index not in self.down_keys:
                self.down_keys.add(index)
                if self.mode in (2, 9):
                    self.hues[index] = random.randrange(256)
                    self.pressed_at[index] = time.monotonic()
            elif not is_pressed:
                self.down_keys.discard(index)
        return key

    def during_bootup(self, keyboard):
        try:
            import board
            import neopixel
            self.pixels = neopixel.NeoPixel(
                board.D10, 9, brightness=1.0,
                auto_write=False, pixel_order=neopixel.GRB,
            )
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
        except Exception as error:
            self.pixels = None
            print("LEDs disabled; keys still work:", error)

    def after_hid_send(self, keyboard):
        if self.pixels is None:
            return
        now = time.monotonic()
        if now - self.last_draw < 0.05:
            return
        try:
            phase = (now % self.cycle_seconds) / self.cycle_seconds
            if self.mode == 1:
                self.pixels.fill((0, 0, 0))
            elif self.mode == 2:
                base = min(self.brightness, 4)
                for index in range(9):
                    age = now - self.pressed_at[index]
                    fade = max(0, 1 - age / 0.9)
                    white = base + int((self.brightness - base) * fade * fade)
                    self.pixels[index] = (white, white, white)
            elif self.mode <= 7:
                low, high = FAMILIES[self.mode - 3]
                drift = 1 - abs(2 * phase - 1)
                hue = low + int((high - low) * drift)
                self.pixels.fill(colour(hue, self.brightness))
            elif self.mode == 8:
                self.pixels.fill(colour(int(phase * 256), self.brightness))
            else:
                for index in range(9):
                    age = now - self.pressed_at[index]
                    value = int(self.brightness * max(0, 1 - age / 0.7))
                    self.pixels[index] = colour(self.hues[index], value)
            self.pixels.show()
            self.last_draw = now
        except Exception as error:
            self.pixels = None
            print("LEDs stopped; keys still work:", error)

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
