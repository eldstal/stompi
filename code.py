import usb_midi
import digitalio
import board
import supervisor
import adafruit_midi

import time

from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_debouncer import Debouncer

# Fast-responding button, only has one purpose
class Clicker:
  def __init__(self, pin, down, up):
    self.debouncer = Debouncer(pin)
    self.down_func = down
    self.up_func = up

  def value(self):
    return self.debouncer.value

  def update(self):
    self.debouncer.update()

    if self.debouncer.fell:
      self.down_func()

    if self.debouncer.rose:
      self.up_func()


# Slower, but multi-functional button
# Short press or long press do different things.
class Holder:

  def __init__(self, pin, short_down, short_up, long_down, long_up):
    # Hold for more than 400ms and it counts as a long press
    self.long_duration = 400
    self.debouncer = Debouncer(pin)
    self.short_down = short_down
    self.short_up = short_up
    self.long_down = long_down
    self.long_up = long_up

    self.during_long = False
    pass

  def value(self):
    return self.debouncer.value

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


# Global setting
# If enabled, buttons will act as control changes
# If disabled, buttons will act as note on/off events
MODE_CC = True

ports_in, ports_out = usb_midi.ports

transport = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])


def setup_pin(gp):
  pin = digitalio.DigitalInOut(gp)
  pin.direction = digitalio.Direction.INPUT
  pin.pull = digitalio.Pull.UP

  return pin


def midi_down(number):
  if MODE_CC:
    return lambda: transport.send(ControlChange(number, 127))
  else:
    return lambda: transport.send(NoteOn(number, 127))

def midi_up(number):
  if MODE_CC:
    return lambda: transport.send(ControlChange(number, 0))
  else:
    return lambda: transport.send(NoteOn(number, 0))


BTNS = [
  # button, press event, release event
  Holder( setup_pin(board.GP10),
              midi_down(50), midi_up(50),
              midi_down(60), midi_up(60)
        ),
  Holder( setup_pin(board.GP11),
              midi_down(51), midi_up(51),
              midi_down(61), midi_up(61)
        ),
  Clicker( setup_pin(board.GP12),
              midi_down(52), midi_up(52)
         ),
  Holder( setup_pin(board.GP13),
              midi_down(53), midi_up(53),
              midi_down(63), midi_up(63)
        ),
]

# Startup:
# If any of the buttons is pressed on boot, we send notes
# If not, we send control events
for btn in BTNS:
  btn.update()
  if btn.value() == 0:
    MODE_CC = False


while True:

  for btn in BTNS:
    btn.update()

