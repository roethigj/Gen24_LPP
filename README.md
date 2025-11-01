[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Gen24_LPP
Home assistant Custom Component for limiting Fronius Gen24 Inverter according to §9 EEG 2025.


> [!CAUTION]
> This is a work in progress project - it is still in early development stage, so there are still breaking changes possible.
>
> This is an unofficial implementation and not supported by Fronius. It might stop working at any point in time.
> You are using this module (and it's prerequisites/dependencies) at your own risk. Not me neither any of contributors to this or any prerequired/dependency project are responsible for damage in any kind caused by this project or any of its prerequsites/dependencies.


## Setup
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roethigj&repository=Gen24_LPP&category=Integration)

or 
# Installation
HACS installation
* Go to HACS
* Click on the 3 dots in the top right corner.
* Select "Custom repositories"
* Add the [URL](https://github.com/roethigj/Gen24_LPP) to the repository.
* Select the 'integration' type.
* Click the "ADD" button.

Manual installation
Copy contents of custom_components folder to your home-assistant config/custom_components folder.
After reboot of Home-Assistant, this integration can be configured through the integration setup UI.

> [!IMPORTANT]
> Update your GEN24 inverter firmware to 1.34.6-1 or higher.

# Usage

### Controls

In progress
| Entity  | Description |
| --- | --- |
| Discharge Limit | This is maxium discharging power in watts of which the battery can be discharged by.  |
| Grid Charge Power | The charging power in watts when the storage is being charged from the grid. Note that grid charging is seems to be limited to an effictive 50% by the hardware. |
| Grid Discharge Power | The discharging power in watts when the storage is being discharged to the grid. |
| Minimum Reserve | The minimum reserve for storage when discharging. Note that the storage will charge from the grid with 0.5kW if SOC falls below this level. Called 'Reserve Capacity' in Fronius Web UI. |
| PV Charge Limit  | This is maximum PV charging power in watts of which the battery can be charged by.  |

# Credits:
Heavily Copied from:
https://github.com/wiggal/GEN24_Ladesteuerung - for http requests
https://github.com/redpomodoro/fronius_modbus - for HACS structure