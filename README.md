# What's this?
pyFIS allows you to control various kinds of passenger information systems.

# Supported devices
This library currently supports the following devices:

* Bus and train displays
  * IBIS devices
    * All standard telegrams as well as some manufacturer-specific variants
    * Connection via serial or TCP
  * LAWO's MONO system
    * Support for sending bitmaps to some LED displays
    * Support for XY10 flipdot pixel control
* Split-Flap displays
  * KRONE / MAN System 9000 "FBM" split-flap modules with ZiLOG microcontroller (in combination with the "FBUE" address board)
  * KRONE / MAN System 9000 "HLST" heater and light control boards
  * KRONE System 8200 (doesn't require any modifications, can send commands to the integrated display controller)
  * OMEGA split-flap units with RS-485 data protocol

Support is planned for:

* KRONE / MAN System 9000 "FBK" split-flap group controller boards
* ADtranz split-flap units with infrared absolute encoders
* AEG MIS LCD signs using the MIS1 protocol and a Geavision Control Unit (GCU)

# The `SplitFlapDisplay` class
The `SplitFlapDisplay` class is an abstraction level you can use to represent a display made up of multiple split-flap modules. It functions as a wrapper for the various display controller classes. Using this class, you can create various fields such as a `TextField`, which represents of one or more alphanumerical split-flap modules, or a `CustomMapField`, which represents split-flap modules with texts or symbols printed on the flaps. Of course, the mapping of position code to displayed value can be set according to the modules you have.

It can even render the display layout as ASCII graphics in your terminal! For more details, take a look at [the example script](/splitflap_display_example.py).

![ASCII rendering of display output](/images/ascii_render.png?raw=true)
![Another ASCII rendering of display output](/images/ascii_render2.png?raw=true)

# Hardware description
Probably most relevant is the pinout of the various devices.
Here's a short, incomplete summary.

## KRONE / MAN system with ZiLOG microcontrollers
This system has a ZiLOG microcontroller on every split-flap unit and separate address boards, where the units are usually plugged in. This enables easy swapping of units without having to change the address, since the address boards would be permanently mounted in the display's backplane.

The address is set with DIP switches and transferred to the split-flap unit using a shift register.

The split-flap units have a 10-pin connector exposing the FBM single interface:

![FBM pin numbering](/images/krone_fbm_pin_numbering.jpg?raw=true)

| Pin | Function                                        |
|-----|-------------------------------------------------|
| 1   | GND                                             |
| 2   | 42V AC (Live)                                   |
| 3   | VCC (9...12V DC)                                |
| 4   | 42V AC (Neutral)                                |
| 5   | 5V DC output for address logic                  |
| 6   | Address shift register data                     |
| 7   | Address shift register clock                    |
| 8   | Tx / Data from unit (CMOS logic levels)         |
| 9   | Rx / Data to unit (CMOS logic levels)           |
| 10  | Address shift register strobe                   |

However, this alone is rather impractical. Controlling these units in combination with the address boards is much easier. The address boards have a 20-pin connector which exposes the FBM bus interface:

| Pin      | Function                                 |
|----------|------------------------------------------|
| 1...6    | 42V AC (Live)                            |
| 7...12   | 42V AC (Neutral)                         |
| 13,14,15  | VCC (9...12V DC)                        |
| 16,18,20 | GND                                      |
| 17       | Rx / Data to units (CMOS logic levels)   |
| 19       | Tx / Data from units (CMOS logic levels) |

If you don't have the address boards, you can order the remade version I created together with [Phalos Southpaw](http://www.phalos-werkstatt.de/), which is available [here](https://github.com/Mezgrman/Krone-FBUE)!

# Reference photos
In case you're not sure what kind of display you have, here are some pictures:

![KRONE / MAN split-flap unit](/images/krone_zilog.jpg?raw=true)

KRONE / MAN split-flap unit with ZiLOG microcontroller. There is also a variant with a THT microcontroller, which is also compatible.

![FBUE address board](/images/krone_fbue.jpg?raw=true)

KRONE / MAN "FBUE" address board for "FBM" split-flap units

![KRONE / MAN FBK board](/images/krone_fbk.jpg?raw=true)

KRONE / MAN "FBK" board for controlling groups of FBM+FBUE split-flap units

![OMEGA split-flap unit](/images/omega_unit.jpg?raw=true)

OMEGA split-flap unit with RS-485 and DC input, commonly found in SBB (Swiss train operator) displays



# Installation
`pip install pyfis`