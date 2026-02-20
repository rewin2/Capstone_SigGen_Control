# Capstone_SigGen_Control
 40 Ghz Signal Generator Control program for LMX2820

 Installation:

This repository require the spidev library to communicate with the LMX2820. This should be done in a virtual environment on Debian-based systems.

1. Clone repository:
'''bash
    git clone https://github.com/rewin2/Capstone_SigGen_Control.git
    cd Capstone_SigGen_Control
    '''

2. Install python

    sudo apt install python3

3. Install python virtual environment package

    sudo apt install python3-venv

4. Enter repository

    cd Capstone_SigGen_Control

5. Create virtual environment

    python3 -n venv .venv

6. Activate virtual environment

    source .venv/vin/activate

7. Install spidev on virtual environment

    pip install spidev

8. Start Controller with

    python3 main.py