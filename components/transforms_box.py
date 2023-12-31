import dataclasses

from kivy.uix.boxlayout import BoxLayout

from components.transformation_form import TransformationForm
from consts import CURRENT_PRESET
from controller import logger
from models.preset import Transformation, Preset
from utils.state import state


class TransformsBox(BoxLayout):
    def load_from_state(self, transformations: list[Transformation]) -> None:
        self.ids.transforms_box.clear_widgets()
        for transform in transformations:
            self.ids.transforms_box.add_widget(
                TransformationForm(remove_callback=self.remove_transform_item))
            logger.debug(self.children)
            self.ids.transforms_box.children[0].load_state(transform)

    def add_transform_item_click_handler(self):
        preset: Preset = state.get_prop(CURRENT_PRESET)
        transformations = preset.transformations + [
            Transformation(name=None, params={})
        ]
        new_preset = dataclasses.replace(preset, transformations=transformations)
        state.set_prop(CURRENT_PRESET, new_preset)

    def remove_transform_item(self, form_to_remove: TransformationForm) -> None:
        tranform_index = form_to_remove.index
        self.ids.transforms_box.remove_widget(form_to_remove)

        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_transformations = preset.transformations[:tranform_index] + preset.transformations[tranform_index + 1:]
        new_preset = dataclasses.replace(preset, transformations=new_transformations)
        state.set_prop(CURRENT_PRESET, new_preset)
