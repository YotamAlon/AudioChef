from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class ExtBox(BoxLayout):
    ext_text = StringProperty()

    def load_state(self, ext: str):
        if not self.ids.lock.selected:
            return

        self.ext_text = ext
