from kmk.modules.encoder import EncoderHandler


class DogEncoder(EncoderHandler):
    def __init__(self, dog, lighting):
        super().__init__()
        self.dog = dog
        self.lighting = lighting

    def on_move_do(self, keyboard, encoder_id, state):
        if self.lighting.turn(state["direction"]):
            return
        super().on_move_do(keyboard, encoder_id, state)
        self.dog.tip(state["direction"])

    def before_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        super().before_matrix_scan(keyboard)
