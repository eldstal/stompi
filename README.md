## Stompi

A MIDI pedalbox using Raspi pico (or just about any circuitpy board, probably)

Four buttons are connected to GP10, GP11, GP12, GP13, connecting each to GND.

![A very simple little stomp box](stompi.jpg)

## Installing
Install CircuitPython 8.x on a raspi pico (with or without W)

Copy `code.py` and `boot.py` and `lib/` to your board and reset it

## Usage


If you press any button while plugging the device in, the buttons will act as MIDI notes.

If you press no button while plugging the device in, the buttons will act as MIDI control changes.


## What the buttons do

In the default configuration, Buttons 0, 1 and 3 are multi-function, and will send different events if you perform a long or a short press. Button 2 is single-use, and will immediately send its event (good for timing-sensitive operations like loop triggers).

Buttons will send events 50, 51, 52 and 53 (short press) or events 60, 61, 63 (long press)
