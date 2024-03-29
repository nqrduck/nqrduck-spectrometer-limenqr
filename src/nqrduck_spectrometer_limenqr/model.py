import logging
from nqrduck_spectrometer.base_spectrometer_model import BaseSpectrometerModel
from nqrduck_spectrometer.pulseparameters import TXPulse, RXReadout
from nqrduck_spectrometer.settings import FloatSetting, IntSetting, BooleanSetting, SelectionSetting

logger = logging.getLogger(__name__)


class LimeNQRModel(BaseSpectrometerModel):    
    # Setting constants for the names of the spectrometer settings
    CHANNEL = "TX/RX Channel"
    TX_MATCHING = "TX Matching"
    RX_MATCHING = "RX Matching"
    SAMPLING_FREQUENCY = "Sampling Frequency"
    IF_FREQUENCY = "IF Frequency"
    ACQUISITION_TIME = "Acquisition time"
    GATE_ENABLE = "Enable"
    GATE_PADDING_LEFT = "Gate padding left"
    GATE_PADDING_RIGHT = "Gate padding right"
    GATE_SHIFT = "Gate shift"
    RX_GAIN = "RX Gain"
    TX_GAIN = "TX Gain"
    RX_LPF_BW = "RX LPF BW"
    TX_LPF_BW = "TX LPF BW"
    TX_I_DC_CORRECTION = "TX I DC correction"
    TX_Q_DC_CORRECTION = "TX Q DC correction"
    TX_I_GAIN_CORRECTION = "TX I Gain correction"
    TX_Q_GAIN_CORRECTION = "TX Q Gain correction"
    TX_PHASE_ADJUSTMENT = "TX phase adjustment"
    RX_I_DC_CORRECTION = "RX I DC correction"
    RX_Q_DC_CORRECTION = "RX Q DC correction"
    RX_I_GAIN_CORRECTION = "RX I Gain correction"
    RX_Q_GAIN_CORRECTION = "RX Q Gain correction"
    RX_PHASE_ADJUSTMENT = "RX phase adjustment"
    RX_OFFSET = "RX offset"
    FFT_SHIFT = "FFT shift"

    # Constants for the Categories of the settings
    ACQUISITION = "Acquisition"
    GATE_SETTINGS = "Gate Settings"
    RX_TX_SETTINGS = "RX/TX Settings"
    CALIBRATION = "Calibration"
    SIGNAL_PROCESSING = "Signal Processing"

    # Pulse parameter constants
    TX = "TX"
    RX = "RX"

    # Settings that are not changed by the user
    OFFSET_FIRST_PULSE = 300
    

    def __init__(self, module) -> None:
        super().__init__(module)
        # Acquisition settings
        channel_options = ["1", "2"]
        channel_setting = SelectionSetting(self.CHANNEL, channel_options, "1", "TX/RX Channel")
        self.add_setting(channel_setting, self.ACQUISITION)

        tx_matching_options = ["1", "2"]
        tx_matching_setting = SelectionSetting(self.TX_MATCHING, tx_matching_options, "1", "TX Matching")
        self.add_setting(tx_matching_setting, self.ACQUISITION)

        rx_matching_options = ["1", "2"]
        rx_matching_setting = SelectionSetting(self.RX_MATCHING, rx_matching_options, "1", "RX Matching")
        self.add_setting(rx_matching_setting, self.ACQUISITION)

        sampling_frequency_setting = FloatSetting(self.SAMPLING_FREQUENCY, 30.72e6, "Sampling frequency")
        self.add_setting(sampling_frequency_setting, self.ACQUISITION)

        if_frequency_setting = FloatSetting(self.IF_FREQUENCY, 5e6, "IF Frequency")
        self.add_setting(if_frequency_setting, self.ACQUISITION)
        self.if_frequency = 5e6

        acquisition_time_setting = FloatSetting(self.ACQUISITION_TIME, 82e-6, "Acquisition time - this is from the beginning of the pulse sequence")
        self.add_setting(acquisition_time_setting, self.ACQUISITION)

        # Gate Settings
        gate_enable_setting = BooleanSetting(self.GATE_ENABLE, True, "Enable")
        self.add_setting(gate_enable_setting, self.GATE_SETTINGS)

        gate_padding_left_setting = IntSetting(self.GATE_PADDING_LEFT, 10, "Gate padding left")
        self.add_setting(gate_padding_left_setting, self.GATE_SETTINGS)

        gate_padding_right_setting = IntSetting(self.GATE_PADDING_RIGHT, 10, "Gate padding right")
        self.add_setting(gate_padding_right_setting, self.GATE_SETTINGS)

        gate_shift_setting = IntSetting(self.GATE_SHIFT, 53, "Gate shift")
        self.add_setting(gate_shift_setting, self.GATE_SETTINGS)

        # RX/TX settings
        rx_gain_setting = IntSetting(self.RX_GAIN, 55, "RX Gain")
        self.add_setting(rx_gain_setting, self.RX_TX_SETTINGS)

        tx_gain_setting = IntSetting(self.TX_GAIN, 30, "TX Gain")
        self.add_setting(tx_gain_setting, self.RX_TX_SETTINGS)

        rx_lpf_bw_setting = FloatSetting(self.RX_LPF_BW, 30.72e6/2, "RX LPF BW")
        self.add_setting(rx_lpf_bw_setting, self.RX_TX_SETTINGS)

        tx_lpf_bw_setting = FloatSetting(self.TX_LPF_BW, 130.0e6, "TX LPF BW")
        self.add_setting(tx_lpf_bw_setting, self.RX_TX_SETTINGS)

        # Calibration settings
        tx_i_dc_correction_setting = IntSetting(self.TX_I_DC_CORRECTION, -45, "TX I DC correction")
        self.add_setting(tx_i_dc_correction_setting, self.CALIBRATION)

        tx_q_dc_correction_setting = IntSetting(self.TX_Q_DC_CORRECTION, 0, "TX Q DC correction")
        self.add_setting(tx_q_dc_correction_setting, self.CALIBRATION)

        tx_i_gain_correction_setting = IntSetting(self.TX_I_GAIN_CORRECTION, 2047, "TX I Gain correction")
        self.add_setting(tx_i_gain_correction_setting, self.CALIBRATION)
    
        tx_q_gain_correction_setting = IntSetting(self.TX_Q_GAIN_CORRECTION, 2039, "TX Q Gain correction")
        self.add_setting(tx_q_gain_correction_setting, self.CALIBRATION)

        tx_phase_adjustment_setting = IntSetting(self.TX_PHASE_ADJUSTMENT, 3, "TX phase adjustment")
        self.add_setting(tx_phase_adjustment_setting, self.CALIBRATION)

        rx_i_dc_correction_setting = IntSetting(self.RX_I_DC_CORRECTION, 0, "RX I DC correction")
        self.add_setting(rx_i_dc_correction_setting, self.CALIBRATION)

        rx_q_dc_correction_setting = IntSetting(self.RX_Q_DC_CORRECTION, 0, "RX Q DC correction")
        self.add_setting(rx_q_dc_correction_setting, self.CALIBRATION)

        rx_i_gain_correction_setting = IntSetting(self.RX_I_GAIN_CORRECTION, 2047, "RX I Gain correction")
        self.add_setting(rx_i_gain_correction_setting, self.CALIBRATION)

        rx_q_gain_correction_setting = IntSetting(self.RX_Q_GAIN_CORRECTION, 2047, "RX Q Gain correction")
        self.add_setting(rx_q_gain_correction_setting, self.CALIBRATION)

        rx_phase_adjustment_setting = IntSetting(self.RX_PHASE_ADJUSTMENT, 0, "RX phase adjustment")
        self.add_setting(rx_phase_adjustment_setting, self.CALIBRATION)
        
        # Signal Processing settings
        rx_offset_setting = FloatSetting(self.RX_OFFSET, 2.4e-6, "The offset of the RX event, this changes all the time")
        self.add_setting(rx_offset_setting, self.SIGNAL_PROCESSING)

        fft_shift_setting = BooleanSetting(self.FFT_SHIFT, False, "FFT shift")
        self.add_setting(fft_shift_setting, self.SIGNAL_PROCESSING)

        # Pulse parameter options
        self.add_pulse_parameter_option(self.TX, TXPulse)
        # self.add_pulse_parameter_option(self.GATE, Gate)
        self.add_pulse_parameter_option(self.RX, RXReadout)

        # Try to load the pulse programmer module
        try:
            from nqrduck_pulseprogrammer.pulseprogrammer import pulse_programmer
            self.pulse_programmer = pulse_programmer
            logger.debug("Pulse programmer found.")
            self.pulse_programmer.controller.on_loading(self.pulse_parameter_options)
        except ImportError:
            logger.warning("No pulse programmer found.")

        self.averages = 1

    @property
    def target_frequency(self):
        return self._target_frequency
    
    @target_frequency.setter
    def target_frequency(self, value):
        self._target_frequency = value

    @property
    def averages(self):
        return self._averages
    
    @averages.setter
    def averages(self, value):
        self._averages = value

    @property
    def if_frequency(self):
        return self._if_frequency
    
    @if_frequency.setter
    def if_frequency(self, value):
        self._if_frequency = value


