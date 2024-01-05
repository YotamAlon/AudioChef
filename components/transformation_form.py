import logging

from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout

from components.transformation_parameter_popup import TransformationParameterPopup
from models.preset import Transformation
from utils.functions import find_first
from utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class TransformationForm(BoxLayout):
    available_transformations: list[Transformation] = ListProperty()

    def __init__(
        self, transform_name: str | None = None, params: dict | None = None, **kwargs
    ):
        super().__init__(**kwargs)
        self.selected_transformation_name: str = transform_name
        self.arg_values: dict = params or {}

    def load(self):
        self.ids.spinner.text = self.selected_transformation_name or ""

    @property
    def index(self) -> int:
        self_index = self.parent.children.index(self)
        return len(self.parent.children) - self_index - 1

    def open_parameter_popup(self):
        if self.selected_transformation_name:
            transform = find_first(
                self.available_transformations,
                lambda t: t.name == self.selected_transformation_name,
            )
            if transform.show_editor:
                transform.show_editor()
            else:
                TransformationParameterPopup(
                    self.index,
                    self.selected_transformation_name,
                    TRANSFORMATIONS[self.selected_transformation_name].arguments,
                    title=f"Edit {self.selected_transformation_name} parameters",
                ).open()
        else:
            # TODO: Open a popup here to let the user know he must select a transformation first
            pass
