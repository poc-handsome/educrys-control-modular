# exp-democz-rpi

Control and GUI for the EduCrys setup with Raspberry Pi

# Missing features
Two more interfaces were planned but could not be implemented. The first one was a
serial connection to a software used at the IKZ Modellexperimente Group [23]. The other
is the control of some software functions with a game controller. The ability to use recipes
(growing crystals automatically based on input tables) is included in the Non-OOP-V0
software but is not implemented in the new software. The GUI lacks important features
that includes the direct control of the PID output and the inability to display the images
of the cameras.

# Bugs

The author is aware of two bugs. The vertical position resets in the software after the
minimum or maximum value is hit. This is a safety thread. The second bug is that the
value of the PID output is displayed wrong.
