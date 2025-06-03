# educrys-control-modular
[![DOI](https://zenodo.org/badge/978255829.svg)](https://doi.org/10.5281/zenodo.15496230)

Control and GUI for the EduCrys setup with Raspberry Pi

## Raspberry Pi OS and requirements
### Raspberry Pi OS
Before the software can be installed, the OS has to be installed correctly. This is important because a wrong installation could lead to deprecation errors.

#### Raspberry Pi OS Versions 
The Software was tested with Raspberry Pi OS (32-bit) Release 5.2: March 2024. (TODO: Provide link). Newer Raspberry Pi OS versions are likely to work as well but are not tested. The newest Raspberry Pi OS version is downladable from [here](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-32-bit).

#### Installing Raspberry Pi OS
Use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to install Raspberry Pi OS on the provided micro SD card. No special settings are requiered.

Insert the micro SD card into the Raspberry Pi after the process is finshed. Follow the instructions on the screen to finish the instalation of the Raspberry Pi OS.

**It is critical to choose “skip” if asked to update the software. This prevents
the OS from updating to a newer release that could potentially deprecate the
software.**

### Installation of requiered packages

Create and use a virtual environment where the external packages are installed.
```bash
python -m venv --system-site-packages venvDemocz
source venvDemocz/bin/activate
```

Now the external packages can be installed. This can be done one by one as
shown below, gathered as one ”pip install” command or with the help of a
requirements.txt file:

```bash
pip install pyyaml==6.0.2
pip install numpy==1.26.1
pip install matplotlib==3.10.0
pip install RPi.GPIO==0.7.1
pip install rpi_hardware_pwm==0.2.2
pip install Adafruit-Blinka==8.56.0
pip install adafruit-circuitpython-max31865==2.2.23
pip install adafruit-circuitpython-max31856==0.12.2
pip install adafruit-circuitpython-ina219==3.4.25
pip install adafruit-circuitpython-mlx90640==1.3.3
pip install adafruit-circuitpython-sht31d==2.3.25
```

### Starting the software
Navigate to the folder where the .sh scripts are located. The venv should be one hierarchy above the current folder. The scripts need additional permissions before they can be used:
```bash
sudo chmod +x startWithGui.sh
sudo chmod +x startWithoutGui.sh
```
Start demoCZ by starting the script:
```bash
./startWithGui.sh
```

## Software design 

*MVC concept incl. picture...*

*Description of class structure incl. table*

## Current status

Two more interfaces were planned but could not be implemented:
1. serial connection to VIFCON.
2. Control of software functions with a game controller.

Two featueres are missing in comparission to the basic software:
1. The ability to use recipes (growing crystals automatically based on input tables) is included in the Non-OOP-V0.
2. Direct control of the PID output.

## Known bugs

1. The vertical position resets in the software after the minimum or maximum value is hit.
2. images of camera can not be displayed.
3. Value of the PID output is displayed wrong.

## Acknowledgements

[This project](https://poc-handsome.github.io/) has received funding from the European Research Council (ERC) under the 
European Union’s Horizon Europe framework programme for research and innovation (grant agreement No. 101122970).

<img src="https://raw.githubusercontent.com/poc-handsome/poc-handsome.github.io/master/EN_FundedbytheEU_RGB_POS.png" width="400">
