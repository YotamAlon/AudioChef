from kivy.uix.boxlayout import BoxLayout

from components.transformation_form import TransformationForm
from models.preset import Transformation


class TransformsBox(BoxLayout):
    def load_state(self, transformations: list[Transformation]) -> None:
        if not self.ids.lock.selected:
            return

        self.ids.transforms_box.clear_widgets()
        for transform in transformations:
            form = TransformationForm(
                transform_name=transform.name, params=transform.params
            )
            self.ids.transforms_box.add_widget(form)
            form.load()
