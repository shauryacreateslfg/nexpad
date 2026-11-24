import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules.macros import Macros
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.lock_status import LockStatus

from dog_oled import DogOLED
from dog_encoder import DogEncoder
from actions import NexpadActions
from lighting import Lighting
from settings import ENCODER_REVERSED, ENCODER_DIVISOR
from settings import RGB_BRIGHTNESS, RGB_CYCLE_SECONDS

keyboard = KMKKeyboard()
keyboard.col_pins = (board.D0, board.D1, board.D2)
keyboard.row_pins = (board.D3, board.D9, board.D8)
keyboard.diode_orientation = DiodeOrientation.COL2ROW

macros = Macros()
media = MediaKeys()
locks = LockStatus()
dog = DogOLED()
lighting = Lighting(dog, RGB_BRIGHTNESS, RGB_CYCLE_SECONDS)
encoder = DogEncoder(dog, lighting)
encoder.pins = ((board.D6, board.D7, None, ENCODER_REVERSED, ENCODER_DIVISOR),)
encoder.map = [((KC.VOLD, KC.VOLU, KC.NO),)]
keyboard.modules = [macros, lighting, encoder]
keyboard.extensions = [media, locks, dog]

actions = NexpadActions(dog, locks)
lighting.bind(actions.keys, hold_label=8)
keyboard.keymap = [[actions.keys[i] for i in range(1, 10)]]

if __name__ == "__main__":
    keyboard.go()
