import board
import digitalio
import usb_hid
from adafruit_debouncer import Debouncer, ticks_diff, ticks_ms
from adafruit_hid.keyboard import Keyboard as adaKB
from adafruit_hid.keycode import Keycode

LIGHT_PINS = [board.GP11, board.GP15, board.GP16, board.GP20]
# Set Light Pins to On


def initialize_lights(pins):
    for pin in pins:
        p = digitalio.DigitalInOut(pin)
        p.switch_to_output()
        p.value = True


class Button(Debouncer):
    def __init__(self, pin, short_duration_ms=50, active_down=False, **kwargs):
        self.short_duration_ms = short_duration_ms
        self.active_down = active_down
        self.last_change_ms = ticks_ms()
        self.short_registered = False
        self.short_showed = False
        self.key_pressed = False
        super().__init__(pin, **kwargs)

    def _pushed(self):
        return (self.active_down and super().fell) or (
            not self.active_down and super().rose
        )

    def _released(self):
        return (self.active_down and super().rose) or (
            not self.active_down and super().fell
        )

    def update(self):
        super().update()
        if self._pushed():
            self.last_change_ms = ticks_ms()
        elif self._released():
            self.last_change_ms = ticks_ms()
            if self.short_registered:
                self.short_registered = False
                self.short_showed = False
        else:
            duration = ticks_diff(ticks_ms(), self.last_change_ms)
            if (
                not self.short_registered
                and self.value != self.active_down
                and duration > self.short_duration_ms
            ):
                self.short_registered = True

    def press(self, kb, key):
        if self.short_registered and not self.short_showed:
            self.short_showed = True

            # Press Here
            self.key_pressed = True
            kb.press(key)
            print(f"pressing {key}")

        if self.key_pressed:
            # Release Here
            kb.release(key)
            print(f"releasing {key}")
            self.key_pressed = False


class Controller:
    def __init__(self):
        self.left = Button(digitalio.DigitalInOut(board.GP10))
        self.right = Button(digitalio.DigitalInOut(board.GP21))
        self.start = Button(digitalio.DigitalInOut(board.GP17))
        self.enter = Button(digitalio.DigitalInOut(board.GP14))

        self.ada_kbd = adaKB(usb_hid.devices)

    def update(self):
        self.left.update()
        self.right.update()
        self.start.update()
        self.enter.update()

        self.left.press(self.ada_kbd, Keycode.FOUR)
        self.right.press(self.ada_kbd, Keycode.FIVE)
        self.start.press(self.ada_kbd, Keycode.SIX)
        self.enter.press(self.ada_kbd, Keycode.SEVEN)


try:
    initialize_lights(LIGHT_PINS)
    c = Controller()
    while True:
        c.update()
except KeyboardInterrupt:
    pass
