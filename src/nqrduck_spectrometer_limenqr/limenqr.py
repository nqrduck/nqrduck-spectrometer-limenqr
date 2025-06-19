"""BaseSpectrometer for Lime NQR spectrometer."""

from nqrduck_spectrometer.base_spectrometer import BaseSpectrometer
from .model import DuckLimeNQRModel
from .view import DuckLimeNQRView
from .controller import DuckLimeNQRController

LimeNQR = BaseSpectrometer(DuckLimeNQRModel, DuckLimeNQRView, DuckLimeNQRController)
