"""Controller module for the Lime NQR spectrometer."""

import logging

from nqrduck_spectrometer.base_spectrometer_controller import BaseSpectrometerController
from quackseq.measurement import Measurement, MeasurementError
from quackseq_limenqr.limenqr import LimeNQR


logger = logging.getLogger(__name__)


class DuckLimeNQRController(BaseSpectrometerController):
    """Controller class for the Lime NQR spectrometer."""

    def __init__(self, module):
        """Initializes the LimeNQRController."""
        super().__init__(module)

    def start_measurement(self):
        """Starts the measurement procedure."""
        sequence = self.module.model.pulse_programmer.model.pulse_sequence

        limenqr = LimeNQR()

        limenqr.model = self.module.model.quackseq_model

        limenqr.model.target_frequency = self.module.model.target_frequency
        limenqr.model.averages = self.module.model.averages

        measurement_data = limenqr.run_sequence(sequence)

        # Emit the data to the nqrduck core
        if not isinstance(measurement_data, MeasurementError):
            self.emit_status_message("Finished Measurement")
            self.emit_measurement_data(measurement_data)
        else:
            # The error is the name of the error message
            error = measurement_data.name
            self.emit_measurement_error("Measurement failed - no data could be retrieved. Error: " + error)

    def emit_measurement_data(self, measurement_data: Measurement) -> None:
        """Emits the measurement data to the GUI.

        Args:
            measurement_data (Measurement): The measurement data
        """
        logger.debug("Emitting measurement data")
        self.module.nqrduck_signal.emit("measurement_data", measurement_data)

    def emit_status_message(self, message: str) -> None:
        """Emits a status message to the GUI.

        Args:
            message (str): The status message
        """
        self.module.nqrduck_signal.emit("statusbar_message", message)

    def emit_measurement_error(self, error_message: str) -> None:
        """Emits a measurement error to the GUI.

        Args:
            error_message (str): The error message
        """
        logger.error(error_message)
        self.module.nqrduck_signal.emit("measurement_error", error_message)

    def set_frequency(self, value: float) -> None:
        """This method sets the target frequency of the spectrometer.

        Args:
            value (float): The target frequency in MHz
        """
        logger.debug("Setting frequency to: %s", value)
        try:
            self.module.model.target_frequency = float(value)
            logger.debug("Successfully set frequency to: %s", value)
        except ValueError:
            logger.warning("Could not set frequency to: %s", value)
            self.module.nqrduck_signal.emit(
                "notification", ["Error", "Could not set frequency to: " + value]
            )
            self.module.nqrduck_signal.emit("failure_set_frequency", value)

    def set_averages(self, value: int) -> None:
        """This method sets the number of averages for the spectrometer.

        Args:
        value (int): The number of averages
        """
        logger.debug("Setting averages to: %s", value)
        try:
            self.module.model.averages = int(value)
            logger.debug("Successfully set averages to: %s", value)
        except ValueError:
            logger.warning("Could not set averages to: %s", value)
            self.module.nqrduck_signal.emit(
                "notification", ["Error", "Could not set averages to: " + value]
            )
            self.module.nqrduck_signal.emit("failure_set_averages", value)
