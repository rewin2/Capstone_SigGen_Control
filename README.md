# Capstone_SigGen_Control
40 Ghz Signal Generator Control program for LMX2820

## Installation:

This repository require the spidev library to communicate with the LMX2820. This should be done in a virtual environment on Debian-based systems.

### Clone repository:

    git clone https://github.com/rewin2/Capstone_SigGen_Control.git
    cd Capstone_SigGen_Control


### Install python
 
    sudo apt install python3

### Install python virtual environment package

    sudo apt install python3-venv

### Enter repository

    cd Capstone_SigGen_Control

### Create virtual environment

    python3 -n venv .venv

### Activate virtual environment

    source .venv/vin/activate

### Install spidev on virtual environment

    pip install spidev

### Start Controller with

    python3 main.py

---