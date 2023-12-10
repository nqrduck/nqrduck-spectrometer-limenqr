import logging
import tempfile
from pathlib import Path
import numpy as np
from decimal import Decimal
from nqrduck.module.module_controller import ModuleController
from nqrduck_spectrometer.base_spectrometer_controller import BaseSpectrometerController
from nqrduck_spectrometer.measurement import Measurement
from nqrduck_spectrometer.pulseparameters import TXPulse, RXReadout

logger = logging.getLogger(__name__)


class LimeNQRController(BaseSpectrometerController):
    def __init__(self, module):
        super().__init__(module)

    def start_measurement(self):
        self.log_start_message()

        lime = self.initialize_lime()
        if not lime:
            return -1

        self.setup_lime_parameters(lime)
        self.setup_temporary_storage(lime)

        self.emit_status_message("Started Measurement")

        if not self.perform_measurement(lime):
            self.emit_status_message("Measurement failed")
            self.emit_measurement_error("Error with measurement data. Did you set an RX event?")
            return -1

        measurement_data = self.process_measurement_results(lime)

        if measurement_data:
            self.emit_measurement_data(measurement_data)
            self.emit_status_message("Finished Measurement")
        else:
            self.emit_measurement_error("Measurement failed. Unable to retrieve data.")

    def log_start_message(self):
        """This method logs a message when the measurement is started."""
        logger.debug("Starting measurement with spectrometer: %s", self.module.model.name)

    def initialize_lime(self):
        """This method initializes the limr object that is used to communicate with the pulseN driver."""
        try:
            from .contrib.limr import limr
            driver_path = str(Path(__file__).parent / "contrib/pulseN_test_USB.cpp")
            return limr(driver_path)
        except ImportError as e:
            logger.error("Error while importing limr: %s", e)
        except Exception as e:
            logger.error("Error while initializing Lime driver: %s", e)
        return None

    def setup_lime_parameters(self, lime):
        """This method sets the parameters of the limr object according to the settings set in the spectrometer module.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
        """
        lime.noi = -1
        lime.nrp = 1
        lime = self.update_settings(lime)
        lime = self.translate_pulse_sequence(lime)
        lime.nav = self.module.model.averages
        self.log_lime_parameters(lime)

    def setup_temporary_storage(self, lime):
        """This method sets up the temporary storage for the measurement data.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
        """
        temp_dir = tempfile.TemporaryDirectory()
        logger.debug("Created temporary directory at: %s", temp_dir.name)
        lime.spt = Path(temp_dir.name)   # Temporary storage path
        lime.fpa = "temp"                # Temporary filename prefix or related config
    
    def perform_measurement(self, lime):
        """This method executes the measurement procedure.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            
        Returns:
            bool: True if the measurement was successful, False otherwise
        """
        logger.debug("Running the measurement procedure")
        try:
            lime.run()
            lime.readHDF()
            return True
        except Exception as e:
            logger.error("Failed to execute the measurement: %s", e)
            return False

    def process_measurement_results(self, lime):
        """This method processes the measurement results and returns a Measurement object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver

        Returns:
            Measurement: The measurement data
        """
        rx_begin, rx_stop = self.translate_rx_event(lime)
        if rx_begin is None or rx_stop is None:
            return None
        logger.debug("RX event begins at: %sµs and ends at: %sµs", rx_begin, rx_stop)
        return self.calculate_measurement_data(lime, rx_begin, rx_stop)

    def calculate_measurement_data(self, lime, rx_begin, rx_stop):
        """This method calculates the measurement data from the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            rx_begin (float): The start time of the RX event in µs
            rx_stop (float): The stop time of the RX event in µs

        Returns:
            Measurement: The measurement data
        """
        try:
            evidx = self.find_evaluation_range_indices(lime, rx_begin, rx_stop)
            tdx, tdy = self.extract_measurement_data(lime, evidx)
            fft_shift = self.get_fft_shift()
            return Measurement(tdx, tdy, self.module.model.target_frequency, frequency_shift=fft_shift)
        except Exception as e:
            logger.error("Error processing measurement result: %s", e)
            return None

    def find_evaluation_range_indices(self, lime, rx_begin, rx_stop):
        """This method finds the indices of the evaluation range in the measurement data.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            rx_begin (float): The start time of the RX event in µs
            rx_stop (float): The stop time of the RX event in µs
        
        Returns:
            list: The indices of the evaluation range in the measurement data"""
        return np.where((lime.HDF.tdx > rx_begin) & (lime.HDF.tdx < rx_stop))[0]

    def extract_measurement_data(self, lime, indices):
        """This method extracts the measurement data from the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            indices (list): The indices of the evaluation range in the measurement data

        Returns:
            tuple: A tuple containing the time vector and the measurement data
        """
        tdx = lime.HDF.tdx[indices] - lime.HDF.tdx[indices][0]
        tdy = lime.HDF.tdy[indices] / lime.nav
        return tdx, tdy

    def get_fft_shift(self):
        """This method returns the FFT shift value from the settings.
        
        Returns:
            int: The FFT shift value"""
        fft_shift_enabled = self.module.model.get_setting_by_name(self.module.model.FFT_SHIFT).value
        return self.module.model.if_frequency if fft_shift_enabled else 0

    def emit_measurement_data(self, measurement_data):
        """This method emits the measurement data to the GUI.
        
        Args:
            measurement_data (Measurement): The measurement data
        """
        logger.debug("Emitting measurement data")
        self.module.nqrduck_signal.emit("measurement_data", measurement_data)

    def emit_status_message(self, message):
        """This method emits a status message to the GUI.
        
        Args:
            message (str): The status message
        """
        self.module.nqrduck_signal.emit("statusbar_message", message)

    def emit_measurement_error(self, error_message):
        """This method emits a measurement error to the GUI.
        
        Args:
            error_message (str): The error message
        """
        logger.error(error_message)
        self.module.nqrduck_signal.emit("measurement_error", error_message)

    def log_lime_parameters(self, lime):
        """This method logs the parameters of the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
        """
        for key in sorted(lime.parsinp):
            val = getattr(lime, key, [])
            if val:
                logger.debug(f"{key}: {val} {lime.parsinp[key][1]}")

    def update_settings(self, lime):
        """This method sets the parameters of the limr object according to the settings set in the spectrometer module.

        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver

        Returns:
            limr: The updated limr object"""

        logger.debug(
            "Updating settings for spectrometer: %s for measurement",
            self.module.model.name,
        )
        lime.t3d = [0, 0, 0, 0]
        # I don't like this code
        for category in self.module.model.settings.keys():
            for setting in self.module.model.settings[category]:
                logger.debug("Setting %s has value %s", setting.name, setting.value)
                # Acquisiton settings
                if setting.name == self.module.model.SAMPLING_FREQUENCY:
                    lime.sra = setting.get_setting()
                # Careful this doesn't only set the IF frequency but the local oscillator frequency
                elif setting.name == self.module.model.IF_FREQUENCY:
                    lime.lof = (
                        self.module.model.target_frequency - setting.get_setting()
                    )
                    self.module.model.if_frequency = setting.get_setting()
                elif setting.name == self.module.model.ACQUISITION_TIME:
                    lime.tac = setting.get_setting()
                # Gate settings
                elif setting.name == self.module.model.GATE_ENABLE:
                    lime.t3d[0] = int(setting.value)
                elif setting.name == self.module.model.GATE_PADDING_LEFT:
                    lime.t3d[1] = int(setting.get_setting())
                elif setting.name == self.module.model.GATE_SHIFT:
                    lime.t3d[2] = int(setting.get_setting())
                elif setting.name == self.module.model.GATE_PADDING_RIGHT:
                    lime.t3d[3] = int(setting.get_setting())
                # RX/TX settings
                elif setting.name == self.module.model.TX_GAIN:
                    lime.tgn = setting.get_setting()
                elif setting.name == self.module.model.RX_GAIN:
                    lime.rgn = setting.get_setting()
                elif setting.name == self.module.model.RX_LPF_BW:
                    lime.rlp = setting.get_setting()
                elif setting.name == self.module.model.TX_LPF_BW:
                    lime.tlp = setting.get_setting()
                # Calibration settings
                elif setting.name == self.module.model.TX_I_DC_CORRECTION:
                    lime.tdi = setting.get_setting()
                elif setting.name == self.module.model.TX_Q_DC_CORRECTION:
                    lime.tdq = setting.get_setting()
                elif setting.name == self.module.model.TX_I_GAIN_CORRECTION:
                    lime.tgi = setting.get_setting()
                elif setting.name == self.module.model.TX_Q_GAIN_CORRECTION:
                    lime.tgq = setting.get_setting()
                elif setting.name == self.module.model.TX_PHASE_ADJUSTMENT:
                    lime.tpc = setting.get_setting()
                elif setting.name == self.module.model.RX_I_DC_CORRECTION:
                    lime.rdi = setting.get_setting()
                elif setting.name == self.module.model.RX_Q_DC_CORRECTION:
                    lime.rdq = setting.get_setting()
                elif setting.name == self.module.model.RX_I_GAIN_CORRECTION:
                    lime.rgi = setting.get_setting()
                elif setting.name == self.module.model.RX_Q_GAIN_CORRECTION:
                    lime.rgq = setting.get_setting()
                elif setting.name == self.module.model.RX_PHASE_ADJUSTMENT:
                    lime.rpc = setting.get_setting()

        return lime

    def translate_pulse_sequence(self, lime):
        """This method translates the pulse sequence to the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
        """
        events = self.fetch_pulse_sequence_events()

        for event in events:
            self.log_event_details(event)
            for parameter in event.parameters.values():
                self.log_parameter_details(parameter)

                if self.is_translatable_tx_parameter(parameter):
                    pulse_shape, pulse_amplitude = self.prepare_pulse_amplitude(event, parameter)
                    pulse_amplitude, modulated_phase = self.modulate_pulse_amplitude(pulse_amplitude, event, lime)

                    if not lime.pfr:  # If the pulse frequency list is empty
                        self.initialize_pulse_lists(lime, pulse_amplitude, pulse_shape, modulated_phase)
                    else:
                        self.extend_pulse_lists(lime, pulse_amplitude, pulse_shape, modulated_phase)
                        self.calculate_and_set_offsets(lime, pulse_shape, events, event, pulse_amplitude)

        # Set repetition time event as last event's duration and update number of pulses
        lime.trp = float(event.duration)
        lime.npu = len(lime.pfr)
        return lime

    # Helper functions below:

    def fetch_pulse_sequence_events(self):
        """This method fetches the pulse sequence events from the pulse programmer module.
        
        Returns:
            list: The pulse sequence events"""
        return self.module.model.pulse_programmer.model.pulse_sequence.events

    def log_event_details(self, event):
        logger.debug("Event %s has parameters: %s", event.name, event.parameters)

    def log_parameter_details(self, parameter):
        logger.debug("Parameter %s has options: %s", parameter.name, parameter.options)

    def is_translatable_tx_parameter(self, parameter):
        """This method checks if a parameter a pulse with a transmit pulse shape (amplitude nonzero)
        
        Args:
            parameter (Parameter): The parameter to check"""
        return (parameter.name == self.module.model.TX and
                parameter.get_option_by_name(TXPulse.RELATIVE_AMPLITUDE).value > 0)

    def prepare_pulse_amplitude(self, event, parameter):
        """This method prepares the pulse amplitude for the limr object.
        
        Args:
            event (Event): The event that contains the parameter
            parameter (Parameter): The parameter that contains the pulse shape and amplitude
        
        Returns:
            tuple: A tuple containing the pulse shape and the pulse amplitude"""
        pulse_shape = parameter.get_option_by_name(TXPulse.TX_PULSE_SHAPE).value
        pulse_amplitude = abs(pulse_shape.get_pulse_amplitude(event.duration)) * \
                          parameter.get_option_by_name(TXPulse.RELATIVE_AMPLITUDE).value
        pulse_amplitude = np.clip(pulse_amplitude, -0.99, 0.99)
        return pulse_shape, pulse_amplitude

    def modulate_pulse_amplitude(self, pulse_amplitude, event, lime):
        """This method modulates the pulse amplitude for the limr object. We need to do this to have the pulse at IF frequency instead  of LO frequency.
        
        Args:
            pulse_amplitude (float): The pulse amplitude
            event (Event): The event that contains the parameter
            lime (limr): The limr object that is used to communicate with the pulseN driver
        
        Returns:
            tuple: A tuple containing the modulated pulse amplitude and the modulated phase
        """
        num_samples = int(float(event.duration) * lime.sra)
        tdx = np.linspace(0, float(event.duration), num_samples, endpoint=False)
        shift_signal = np.exp(1j * 2 * np.pi * self.module.model.if_frequency * tdx)
        pulse_complex = pulse_amplitude * shift_signal
        modulated_amplitude = np.abs(pulse_complex)
        modulated_phase = self.unwrap_phase(np.angle(pulse_complex))
        return modulated_amplitude, modulated_phase

    def unwrap_phase(self, phase):
        """This method unwraps the phase of the pulse.
        
        Args:
            phase (float): The phase of the pulse"""
        return (np.unwrap(phase) + 2 * np.pi) % (2 * np.pi)

    def initialize_pulse_lists(self, lime, pulse_amplitude, pulse_shape, modulated_phase):
        """This method initializes the pulse lists of the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            pulse_amplitude (float): The pulse amplitude
            pulse_shape (PulseShape): The pulse shape
            modulated_phase (float): The modulated phase
        """
        lime.pfr = [float(self.module.model.if_frequency)] * len(pulse_amplitude)
        lime.pdr = [float(pulse_shape.resolution)] * len(pulse_amplitude)
        lime.pam = list(pulse_amplitude)
        lime.pof = ([self.module.model.OFFSET_FIRST_PULSE] +
                    [int(pulse_shape.resolution * Decimal(lime.sra))] * (len(pulse_amplitude) - 1))
        lime.pph = list(modulated_phase)

    def extend_pulse_lists(self, lime, pulse_amplitude, pulse_shape, modulated_phase):
        """This method extends the pulse lists of the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            pulse_amplitude (float): The pulse amplitude
            pulse_shape (PulseShape): The pulse shape
            modulated_phase (float): The modulated phase
        """
        lime.pfr.extend([float(self.module.model.if_frequency)] * len(pulse_amplitude))
        lime.pdr.extend([float(pulse_shape.resolution)] * len(pulse_amplitude))
        lime.pam.extend(list(pulse_amplitude))
        lime.pph.extend(list(modulated_phase))

    def calculate_and_set_offsets(self, lime, pulse_shape, events, current_event, pulse_amplitude):
        """This method calculates and sets the offsets for the limr object.
        
        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver
            pulse_shape (PulseShape): The pulse shape
            events (list): The pulse sequence events
            current_event (Event): The current event
            pulse_amplitude (float): The pulse amplitude
        """
        blank_durations = self.get_blank_durations_before_event(events, current_event)

        # Calculate the total time that has passed before the current event
        total_blank_duration = sum(blank_durations)
        # Calculate the offset for the current pulse
        # The first pulse offset is already set, so calculate subsequent ones
        offset_for_current_pulse = int(np.ceil(total_blank_duration * lime.sra))

        # Offset for the current pulse should be added only once
        lime.pof.append(offset_for_current_pulse)

        # Set the offset for the remaining samples of the current pulse (excluding the first sample)
        # We subtract 1 because we have already set the offset for the current pulse's first sample
        offset_per_sample = int(float(pulse_shape.resolution) * lime.sra)
        lime.pof.extend([offset_per_sample] * (len(pulse_amplitude) - 1))

    def get_blank_durations_before_event(self, events, current_event):
        """This method returns the blank durations before the current event.
        
        Args:
            events (list): The pulse sequence events
            current_event (Event): The current event
            
        Returns:
            list: The blank durations before the current event
        """
        blank_durations = []
        previous_events_without_tx_pulse = self.get_previous_events_without_tx_pulse(events, current_event)
        for event in previous_events_without_tx_pulse:
            blank_durations.append(float(event.duration))
        return blank_durations

    def get_previous_events_without_tx_pulse(self, events, current_event):
        """This method returns the previous events without a transmit pulse.
        
        Args:
            events (list): The pulse sequence events
            current_event (Event): The current event
        
        Returns:
            list: The previous events without a transmit pulse
        """
        index = events.index(current_event)
        previous_events = events[:index]
        result = []
        for event in reversed(previous_events):
            translatable = any(self.is_translatable_tx_parameter(param) for param in event.parameters.values())
            if not translatable:
                result.append(event)
            else:
                break
        return reversed(result)  # Reversed to maintain the original order if needed elsewhere


    def translate_rx_event(self, lime):
        """This method translates the RX event of the pulse sequence to the limr object.

        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver

        Returns:
            tuple: A tuple containing the start and stop time of the RX event in µs
        """
        CORRECTION_FACTOR = self.module.model.get_setting_by_name(self.module.model.RX_OFFSET).value
        events = self.module.model.pulse_programmer.model.pulse_sequence.events

        rx_event = self.find_rx_event(events)
        if not rx_event:
            return None, None

        previous_events_duration = self.calculate_previous_events_duration(events, rx_event)
        rx_duration = float(rx_event.duration)

        offset = self.calculate_offset(lime)

        rx_begin = float(previous_events_duration) + float(offset) + CORRECTION_FACTOR
        rx_stop = rx_begin + rx_duration
        return rx_begin * 1e6, rx_stop * 1e6

    def find_rx_event(self, events):
        """This method finds the RX event in the pulse sequence.
        
        Args:
            events (list): The pulse sequence events
        
        Returns:
            Event: The RX event
        """
        for event in events:
            parameter = event.parameters.get(self.module.model.RX)
            if parameter and parameter.get_option_by_name(RXReadout.RX).value:
                self.log_event_details(event)
                self.log_parameter_details(parameter)
                return event
        return None

    def calculate_previous_events_duration(self, events, rx_event):
        """This method calculates the duration of the previous events.
        
        Args:
            events (list): The pulse sequence events
            rx_event (Event): The RX event
        
        Returns:
            float: The duration of the previous events
        """
        previous_events = events[: events.index(rx_event)]
        return sum(event.duration for event in previous_events)

    def calculate_offset(self, lime):
        """This method calculates the offset for the RX event.

        Args:
            lime (limr): The limr object that is used to communicate with the pulseN driver 
        
        Returns:
            float: The offset for the RX event
        """
        return self.module.model.OFFSET_FIRST_PULSE * (1 / lime.sra)


    def set_frequency(self, value: float):
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

    def set_averages(self, value: int):
        """This method sets the number of averages for the spectrometer.

        Args:
            value (int): The number of averages"""
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
