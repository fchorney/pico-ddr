import time

import board
import usb_hid
from adafruit_debouncer import Debouncer, ticks_diff, ticks_ms
from adafruit_hid.keyboard import Keyboard as adaKB
from adafruit_hid.keycode import Keycode
from digitalio import DigitalInOut, Pull

LIGHT_PINS = [board.GP11, board.GP15, board.GP16, board.GP20]
# Set Light Pins to On


def initialize_lights(pins):
    for pin in pins:
        p = DigitalInOut(pin)
        p.switch_to_output()
        p.value = True


class KeyState(object):
    IDLE = 0
    PRESS = 1
    PRESSED = 2
    HOLD = 3
    RELEASE = 4
    RELEASED = 5


class Button(object):
    def __init__(
        self,
        pin: int,
        kb,
        kcode: int,
        press_time: float = 0.05,
        release_time: float = 0.02,
    ) -> None:
        self.kcode = kcode
        self.kstate = KeyState.IDLE
        self.on = False
        self.state_changed = False

        self.press_time = press_time
        self.press_timer = 0.0
        self.release_time = release_time
        self.release_timer = 0.0

        # Set Pin to Input
        self.btn = DigitalInOut(pin)
        self.btn.switch_to_input(pull=Pull.DOWN)

        self.kb = kb
        self.pressed = False

    @property
    def off(self) -> bool:
        return not self.on

    def press(self) -> None:
        if not self.pressed:
            self.kb.press(self.kcode)
            self.pressed = True

    def release(self) -> None:
        if self.pressed:
            self.kb.release(self.kcode)
            self.pressed = False

    def update(self) -> None:
        self.on = self.btn.value
        self.state_changed = False

        if self.kstate == KeyState.IDLE:
            if self.on:
                self.transition_to(KeyState.PRESS)
                self.press_timer = time.monotonic()
            else:
                self.release()
        elif self.kstate == KeyState.PRESS:
            if (time.monotonic() - self.press_timer) > self.press_time:
                self.transition_to(KeyState.PRESSED)
            elif self.off:
                self.transition_to(KeyState.RELEASE)
                self.release_timer = time.monotonic()
        elif self.kstate == KeyState.PRESSED:
            self.transition_to(KeyState.HOLD)
        elif self.kstate == KeyState.HOLD:
            if self.off:
                self.transition_to(KeyState.RELEASE)
                self.release_timer = time.monotonic()
            else:
                self.press()
        elif self.kstate == KeyState.RELEASE:
            if (time.monotonic() - self.release_timer) > self.release_time:
                self.transition_to(KeyState.RELEASED)
            elif self.on:
                self.transition_to(KeyState.PRESS)
                self.press_timer = time.monotonic()
        elif self.kstate == KeyState.RELEASED:
            self.transition_to(KeyState.IDLE)

    def transition_to(self, next_state: int) -> None:
        self.kstate = next_state
        self.state_changed = True


class Controller:
    def __init__(self):
        ada_kbd = adaKB(usb_hid.devices)

        self.left = Button(board.GP10, ada_kbd, Keycode.FOUR)
        self.right = Button(board.GP17, ada_kbd, Keycode.FIVE)
        self.start = Button(board.GP21, ada_kbd, Keycode.SIX)
        self.enter = Button(board.GP14, ada_kbd, Keycode.SEVEN)

    def update(self):
        self.left.update()
        self.right.update()
        self.start.update()
        self.enter.update()


try:
    initialize_lights(LIGHT_PINS)
    c = Controller()
    while True:
        c.update()
except KeyboardInterrupt:
    pass
