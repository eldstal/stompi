import usb_midi
import usb_hid

# Reconfigure USB on boot
# We want a MIDI endpoint
usb_hid.disable()
usb_midi.enable()

print(usb_midi.ports)




