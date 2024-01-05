from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout

from components.transformation_form import TransformationForm
from models.preset import Transformation


class TransformsBox(BoxLayout):
    available_transformations: list[Transformation] = ListProperty()

    def load_state(self, transformations: list[Transformation]) -> None:
        if not self.ids.lock.selected:
            return

        self.ids.transforms_box.clear_widgets()
        for transform in transformations:
            form = TransformationForm(
                transform_name=transform.name,
                params=transform.params,
                available_transformations=self.available_transformations,
            )
            self.ids.transforms_box.add_widget(form)
            form.load()

    def load_available_tranformations(
        self, available_transformations: list[Transformation]
    ):
        self.available_transformations = available_transformations
        for form in self.ids.transforms_box.children:
            form.available_transformations = self.available_transformations
