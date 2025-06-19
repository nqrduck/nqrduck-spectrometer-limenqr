"""Model for the Lime NQR spectrometer."""

import logging
from nqrduck_spectrometer.base_spectrometer_model import BaseSpectrometerModel
from  quackseq_limenqr.limenqr_model import LimeNQRModel
logger = logging.getLogger(__name__)


class DuckLimeNQRModel(BaseSpectrometerModel):
    """Model for the Lime NQR spectrometer."""
   

    def __init__(self, module) -> None:
        """Initializes the Lime NQR model."""
        super().__init__(module)
        
        self.quackseq_model = LimeNQRModel()
        self.visualize_settings()

        self.quackseq_visuals

        # Try to load the pulse programmer module
        try:
            from nqrduck_pulseprogrammer.pulseprogrammer import pulse_programmer

            self.pulse_programmer = pulse_programmer
            logger.debug("Pulse programmer found.")
            self.pulse_programmer.controller.on_loading()
        except ImportError:
            logger.warning("No pulse programmer found.")

    @property
    def target_frequency(self):
        """The target frequency of the spectrometer."""
        return self._target_frequency

    @target_frequency.setter
    def target_frequency(self, value):
        self._target_frequency = value

    @property
    def averages(self):
        """The number of averages to be taken."""
        return self._averages

    @averages.setter
    def averages(self, value):
        self._averages = value

    @property
    def if_frequency(self):
        """The intermediate frequency to which the input signal is down converted during analog-to-digital conversion."""
        return self._if_frequency

    @if_frequency.setter
    def if_frequency(self, value):
        self._if_frequency = value
