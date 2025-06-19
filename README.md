# NQRduck Module: Spectrometer LimeNQR

This module is a part of the NQRduck project. It is a submodule of the [spectrometer module](https://git.private.coffee/nqrduck/nqrduck-spectrometer) for the NQRduck project. It is designed to be used with the [NQRduck](https://git.private.coffee/nqrduck) project.

The module provides a Graphical User Interface (GUI) for the control of the LimeSDR based spectrometer. It is designed to be used with the NQRduck project. The GUI is based on the [PyQt5](https://pypi.org/project/PyQt5/) library

The  original code for the control of the LimeSDR based spectrometer was part of the paper by A. Doll; Pulsed and continuous-wave magnetic resonance spectroscopy using a low-cost software-defined radio. AIP Advances 1 November 2019; 9 (11): 115110. <https://doi.org/10.1063/1.5127746>. More information about the original code can be found in the [LimeDriver](https://git.private.coffee/nqrduck/limedriver) project.

The currently supported LimeSDR devices are:

- LimeSDR Mini v2.0 (probably also v1.x, but not tested)
- LimeSDR USB

## Installation

### Requirements

- [LimeSuite](https://wiki.myriadrf.org/Lime_Suite)
- [HDF5](https://www.hdfgroup.org/solutions/hdf5/)

You can find more information about the installation of dependencies in the [LimeDriver](https://git.private.coffee/nqrduck/limedriver) project.

Additional dependencies should be installed  by the pyproject.toml file when installing this module.

### Setup

To install the module you need the NQRduck core. You can find the installation instructions for the NQRduck core [here](https://git.private.coffee/nqrduck/nqrduck).

Ideally you should install the module in a virtual environment. You can create a virtual environment by running the following command in the terminal:

```bash
python -m venv nqrduck
```

You can install this module and the dependencies by running the following command in the terminal after cloning the repositor and navigating to the module directory:

```bash
pip install .
```

Alternatively you can install the module via the PyPi package manager by running the following command in the terminal:

```bash
pip install nqrduck-spectrometer-limenqr
```

## Usage

The module is used together with the NQRduck [pulseprogrammer](htpps://git.private.coffee/nqrduck-pulseprogrammer) module.

### Notes

- When using the LimeSDR USB use the TX Matching: 0 and RX Matching: 0 for  frequencies below  1.5GHz in the settings of the module.
- For the LimeSDR Mini 2.0 use the TX Matching: 4 and RX Matching: 4 for automatic selection of the matching  network.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
