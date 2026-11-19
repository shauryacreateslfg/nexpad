class CommandCycle:
    def __init__(self):
        self.state = "idle"
        self.down = False
 
    def press(self):
        if self.down:
            return None
        self.down = True
        if self.state == "idle":
            self.state = "sending_command"
            return "type_command_and_enter"
        if self.state == "awaiting_user_prompt":
            self.state = "sending_accept"
            return "send_enter_only"
        return None

    def release(self):
        self.down = False
 
    def sent(self, success):
        if self.state not in ("sending_command", "sending_accept"):
            return False
        if not success:
            self.state = "delivery_unknown"
        elif self.state == "sending_command":
            self.state = "awaiting_user_prompt"
        else:
            self.state = "idle"
        return True
 
    def reset_local_state(self):
        self.state = "idle"
        self.down = False