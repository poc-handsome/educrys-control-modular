# educrys-control-modular
[![DOI](https://zenodo.org/badge/978255829.svg)](https://doi.org/10.5281/zenodo.15496230)

Control and GUI for the EduCrys setup with Raspberry Pi

## Raspberry Pi OS and requirements

*List of ALL steps how to obtain and burn a working OS image and install all required packages...*

## Software design 

*MVC concept incl. picture...*

*Description of class structure incl. table*

## Current status

*Complete list of missing features vs. educrys-control-basic...*

Two more interfaces were planned but could not be implemented. The first one was a
serial connection to a software used at the IKZ Modellexperimente Group [23]. The other
is the control of some software functions with a game controller. The ability to use recipes
(growing crystals automatically based on input tables) is included in the Non-OOP-V0
software but is not implemented in the new software. The GUI lacks important features
that includes the direct control of the PID output and the inability to display the images
of the cameras.

## Known bugs

*Complete list of bugs...*

The author is aware of two bugs. The vertical position resets in the software after the
minimum or maximum value is hit. This is a safety thread. The second bug is that the
value of the PID output is displayed wrong.

## Acknowledgements

[This project](https://poc-handsome.github.io/) has received funding from the European Research Council (ERC) under the 
European Union’s Horizon Europe framework programme for research and innovation (grant agreement No. 101122970).

<img src="https://raw.githubusercontent.com/poc-handsome/poc-handsome.github.io/master/EN_FundedbytheEU_RGB_POS.png" width="400">
