import traceback
import webbrowser

from kivy.uix.popup import Popup


class ErrorPopup(Popup):
    def __init__(self, **kwargs):
        self._report_link = f'mailto:yotamalon@gmail.com?subject=Error report&body={traceback.format_exc()}'
        super().__init__(**kwargs)

    def open_report_link(self):
        webbrowser.open(self._report_link)
