import json

default_config = {
  # Set to either "midi" or "hid"
  "device": "midi",

  #
  # MIDI example
  # 
  "buttons": [

    # A "double" button can act on a short or long press
    { "gpio": 10, "action": "double", "short": { "cc": 50 }, "long": { "note": 60 } },

    # For "device": "midi", the action is "cc" (a control code) or "note" (a note)
    { "gpio": 11, "action": "double", "short": { "cc": 51 }, "long": { "note": 61 } },

    # A "single" button reacts faster, but can only perform one action.
    { "gpio": 12, "action": "single", "short": { "note": 52 } },


    { "gpio": 33, "action": "double", "short": { "cc": 53 }, "long": { "note": 63 } }

  ]
}

def load():
  config = default_config

  try:
    config = json.load(open("stompi.json"))
  except Exception as e:
    print(e)
    print("Failed to load configuration. Falling back to default.")

  return config

