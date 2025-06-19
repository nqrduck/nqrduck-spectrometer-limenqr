"""View  for LimeNQR spectrometer."""
from nqrduck_spectrometer.base_spectrometer_view import BaseSpectrometerView


class DuckLimeNQRView(BaseSpectrometerView):
    """View class for LimeNQR spectrometer."""

    def __init__(self, module):
        """Initialize the LimeNQRView object."""
        super().__init__(module)

        # Setting UI is automatically generated based on the settings specified in the model
        self.widget = self.load_settings_ui()
