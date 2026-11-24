
from kmk.keys import KC, make_key
from kmk.modules.macros import Tap, Delay
from command_cycle import CommandCycle
from settings import COMMAND, LAUNCHERS, RUN_DIALOG_DELAY_MS, TERMINAL_DELAY_MS


class NexpadActions:
    def __init__(self, dog, locks):
        self.dog = dog
        self.locks = locks
        self.busy = False
        self.cycle = CommandCycle()
        self.keys = {}
        self.names = {1: "spotify", 5: "vscode", 2: "youtube", 3: "claude", 4: "github"}
        for label in range(1, 10):
            self.keys[label] = make_key(
                names=("NEXPAD_" + str(label),),
                on_press=self._press_handler(label),
                on_release=self._release_handler(label),
            )

    def _press_handler(self, label):
        def pressed(key, keyboard, *args):
            if self.busy:
                return
            if label in LAUNCHERS:
                if not self._typing_allowed():
                    return
                self.dog.message(self.names[label])
                self._send(keyboard, (Tap(KC.LGUI(KC.R)), Delay(RUN_DIALOG_DELAY_MS),
                                      Tap(KC.LCTL(KC.A)), LAUNCHERS[label], Tap(KC.ENTER)))
            elif label == 6:
                if not self._typing_allowed():
                    return
                action = self.cycle.press()
                if action == "type_command_and_enter":
                    self._send(keyboard, (Tap(KC.LCTL(KC.LSFT(KC.GRAVE))),
                                            Delay(TERMINAL_DELAY_MS),
                                            COMMAND, Tap(KC.ENTER)),
                               lambda: self._command_finished("command"))
                elif action == "send_enter_only":
                    self._send(keyboard, (Tap(KC.ENTER),),
                               lambda: self._command_finished("accept"))
            else:
                keycode, status = {
                    7: (KC.LCTL(KC.C), "copy"),
                    9: (KC.LCTL(KC.V), "paste"),
                    8: (KC.LGUI(KC.LSFT(KC.S)), "snip"),
                }[label]
                keyboard.tap_key(keycode)
                self.dog.message(status)
        return pressed

    def _release_handler(self, label):
        def released(key, keyboard, *args):
            if label == 6:
                self.cycle.release()
        return released

    def _typing_allowed(self):
        if self.locks.get_caps_lock():
            self.dog.message("caps", 2.0)
            return False
        return True

    def _command_finished(self, status):
        self.cycle.sent(True)
        self.dog.message(status, 3.0 if status == "command" else 1.4)

    def _send(self, keyboard, sequence, finished=None):
        self.busy = True
        def done(kbd):
            if finished is not None:
                finished()
            self.busy = False
        macro = KC.MACRO(*sequence, done, blocking=False)
        keyboard.tap_key(macro)
