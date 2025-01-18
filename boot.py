import usb_midi
import usb_hid

import stompi_config

config = stompi_config.load()

# Reconfigure USB on boot
# We want a MIDI endpoint

if config["device"] == "midi":
  print("MIDI mode")
  usb_hid.disable()
  usb_midi.enable()
else:
  print("HID mode")
  usb_midi.disable()

print(usb_midi.ports)




