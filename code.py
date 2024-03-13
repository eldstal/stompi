import usb_midi
import digitalio
import board
import supervisor

import adafruit_midi
import adafruit_debouncer

import time

from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_on import NoteOn
from adafruit_debouncer import Debouncer


print(usb_midi.ports)
ports_in, ports_out = usb_midi.ports

transport = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1])

PINS = [
  # button, code short press
  ( digitalio.DigitalInOut(board.GP10), 50 ),
  ( digitalio.DigitalInOut(board.GP11), 51 ),
  ( digitalio.DigitalInOut(board.GP12), 52 ),
  ( digitalio.DigitalInOut(board.GP13), 53 ),
]

PRESSED = [ False for b in PINS ]
PRESSED = [ False for b in PINS ]
DOWNTIME = [ 0 for b in PINS ]

for btn, _ in PINS:
  btn.direction = digitalio.Direction.INPUT
  btn.pull = digitalio.Pull.UP

BTNS = [ (Debouncer(pin), code) for pin,code in PINS ]

# Startup:
# If any of the buttons is pressed on boot, we send notes
# If not, we send control events
MODE_CC = True
for btn,_ in BTNS:
  btn.update()
  if btn.value == 0:
    MODE_CC = False



while True:

  for b in range(len(BTNS)):
    btn,shortcode = BTNS[b]
    btn.update()

    #timestamp = supervisor.tick_ms()
    if btn.fell:
      if MODE_CC:
        transport.send(ControlChange(shortcode, 127))
      else:
        transport.send(NoteOn(shortcode, 127))

    if btn.rose:
      if MODE_CC:
        transport.send(ControlChange(shortcode, 0))
      else:
        transport.send(NoteOn(shortcode, 0))

