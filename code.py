import usb_midi
import usb_hid
import digitalio
import board
import supervisor
import adafruit_midi

import time

from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_debouncer import Debouncer

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.mouse import Mouse

import stompi_config

# Change this for boards other than rpi pico
# The "gpio" field of each button config in config.json
# refers to the key of this dict
GPIO_BY_INDEX = {
 0:   board.GP0,
 1:   board.GP1,
 2:   board.GP2,
 3:   board.GP3,
 4:   board.GP4,
 5:   board.GP5,
 6:   board.GP6,
 7:   board.GP7,
 8:   board.GP8,
 9:   board.GP9,
 10:  board.GP10,
 11:  board.GP11,
 12:  board.GP12,
 13:  board.GP13,
 14:  board.GP14,
 15:  board.GP15,
 16:  board.GP16,
 17:  board.GP17,
 18:  board.GP18,
 19:  board.GP19,
 20:  board.GP20,
 21:  board.GP21,
}

MOUSE_BUTTONS = {
 0: Mouse.LEFT_BUTTON,
 1: Mouse.MIDDLE_BUTTON,
 2: Mouse.RIGHT_BUTTON,
 3: Mouse.BACK_BUTTON,
 4: Mouse.FORWARD_BUTTON
}

# Fast-responding button, only has one purpose
class BUTTON_SINGLE:
  def __init__(self, pin, down, up):
    self.pin = pin
    self.debouncer = Debouncer(pin)
    self.down_func = down
    self.up_func = up

  def value(self):
    return self.pin.value

  def update(self):
    self.debouncer.update()

    if self.debouncer.fell:
      self.down_func()

    if self.debouncer.rose:
      self.up_func()


# Slower, but multi-functional button
# Short press or long press do different things.
class BUTTON_DOUBLE:

  def __init__(self, pin, short_down, short_up, long_down, long_up):
    # Hold for more than 400ms and it counts as a long press
    self.long_duration = 400
    self.pin = pin
    self.debouncer = Debouncer(pin)
    self.short_down = short_down
    self.short_up = short_up
    self.long_down = long_down
    self.long_up = long_up

    self.during_long = False

  def value(self):
    return self.pin.value

  def update(self):
    timestamp = supervisor.ticks_ms()

    self.debouncer.update()


    if self.debouncer.fell:
      self.downtime = timestamp

    if self.debouncer.value == 0:
      if not self.during_long:
        if timestamp - self.downtime >= self.long_duration:
          self.during_long = True
          self.long_down()

    if self.debouncer.rose:

      if not self.during_long:
        self.short_down()
        time.sleep(0.02)
        self.short_up()
      else:
        self.long_up()

      self.during_long = False


def setup_gpio(gpio_num):
  if gpio_num not in GPIO_BY_INDEX:
    fallback = GPIO_BY_INDEX.keys()[0]
    print("Unknown gpio number {gpio_num}. Falling back to {fallback}")
    gpio_num = fallback

  return setup_pin(GPIO_BY_INDEX[gpio_num])

def setup_pin(gp):
  pin = digitalio.DigitalInOut(gp)
  pin.direction = digitalio.Direction.INPUT
  pin.pull = digitalio.Pull.UP

  return pin


def midi_action_functions(number, is_cc):
  if is_cc:
    def down_func():
      MIDI_TRANSPORT.send(ControlChange(number, 127))

    def up_func():
      MIDI_TRANSPORT.send(ControlChange(number, 0))

  else:

    def down_func():
      MIDI_TRANSPORT.send(NoteOn(number, 127))

    def up_func():
      MIDI_TRANSPORT.send(NoteOn(number, 0))

  return down_func, up_func



def midi_action(action_conf):
  if "cc" in action_conf:
    return midi_action_functions(action_conf["cc"], True)
  else:
    note = action_conf.get("note", 0)
    return midi_action_functions(note, False)


def hid_action(action_conf):
  nop_func = lambda: 1

  if "key" in action_conf:
    key = action_conf["key"]
    keycodes = KEYBOARD_LAYOUT.keycodes(key)

    def down_func():
      for kc in keycodes:
        KEYBOARD.press(kc)

    def up_func():
      KEYBOARD.release_all()

    return down_func, up_func

  if "text" in action_conf:
    text = action_conf["text"]

    def down_func():
      KEYBOARD_LAYOUT.write(text)

    return down_func, nop_func

  elif "keycode" in action_conf:
    keycode = action_conf["keycode"]

    def down_func():
      KEYBOARD.press(keycode)

    def up_func():
      KEYBOARD.release_all()

    return down_func, up_func

  elif "click" in action_conf:
    btn_index = action_conf.get("click")

    mouse_btn = MOUSE_BUTTONS.get(btn_index, None)
    if not mouse_btn:
      print(f"Unable to click mouse button {btn_index}. skipping.")
      return nop_func, nop_func

    def down_func():
      MOUSE.press(mouse_btn)

    def up_func():
      MOUSE.release(mouse_btn)

    return down_func, up_func


  return nop_func, nop_func


BTNS = [
]

# Startup

# Parse configuration and generate the BTNS array
# This will differ depending on if the device is "midi" or "hid"
# The boot.py script will have enabled the appropriate hardware support.
config = stompi_config.load()

if config["device"] == "midi":
  MIDI_TRANSPORT = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])
  action_generator = midi_action
  default_action = { "cc": 100 }
else:
  MOUSE = Mouse(usb_hid.devices)
  KEYBOARD = Keyboard(usb_hid.devices)
  KEYBOARD_LAYOUT = KeyboardLayoutUS(KEYBOARD)
  action_generator = hid_action
  default_action = { "key": "X" }

#
# Parse the configuration
#

for button_conf in config["buttons"]:
  pin_number = button_conf.get("gpio", 0)
  try:
    pin = setup_gpio(pin_number)
  except Exception as e:
    print(e)
    print(f"Failed to configure pin {pin_number}. Skipping button.")
    continue

  action = button_conf.get("action", "single")

  if action == "double":
    short_conf = button_conf.get("short", default_action)
    long_conf  = button_conf.get("long",  default_action)
    btn = BUTTON_DOUBLE(
      pin,

      # Short press action
      *action_generator(short_conf),

      # Long press action
      *action_generator(long_conf),
    )

    BTNS.append(btn)

  else:
    short_conf = button_conf.get("short", default_action)
    btn = BUTTON_SINGLE(
      pin,

      # Press/release action
      *action_generator(short_conf),
    )

    BTNS.append(btn)


while True:

  for btn in BTNS:
    btn.update()

