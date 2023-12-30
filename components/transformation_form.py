import dataclasses
import logging

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from components.transformation_parameter_popup import TransformationParameterPopup
from consts import CURRENT_PRESET
from models.preset import Transformation, Preset
from utils.state import state
from utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class TransformationForm(BoxLayout):
    remove_callback = ObjectProperty()
    transformations = TRANSFORMATIONS.keys()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_transformation_name: str = None
        self.arg_values = {}

    @property
    def index(self) -> int:
        self_index = self.parent.children.index(self)
        return len(self.parent.children) - self_index - 1

    def shift_up(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, self_index + 1)
        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_preset = Preset.move_transform(preset, self.index, self.index + 1)
        state.set_prop(CURRENT_PRESET, new_preset)

    def shift_down(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, max(self_index - 1, 0))
        preset: Preset = state.get_prop(CURRENT_PRESET)
        new_preset = Preset.move_transform(preset, self.index, max(self.index - 1, 0))
        state.set_prop(CURRENT_PRESET, new_preset)

    def select_transformation(self, transform_name: str):
        if transform_name == self.selected_transformation_name:
            return
        self.selected_transformation_name = transform_name
        preset: Preset = state.get_prop(CURRENT_PRESET)
        transform = preset.transformations[self.index]
        new_transform = dataclasses.replace(transform, name=transform_name)
        new_preset = Preset.replace_transform_at(preset, self.index, new_transform)
        state.set_prop(CURRENT_PRESET, new_preset)
        self.ids.args_box.clear_widgets()

    def open_parameter_popup(self):
        if self.selected_transformation_name:
            preset: Preset = state.get_prop(CURRENT_PRESET)
            transform = preset.transformations[self.index]
            if transform.show_editor:
                transform.show_editor()
            else:
                TransformationParameterPopup(
                    self.selected_transformation_name,
                    TRANSFORMATIONS[self.selected_transformation_name].arguments,
                    title=f"Edit {self.selected_transformation_name} parameters",
                    save_callback=self.update_arg_values,
                ).open()
        else:
            # TODO: Open a popup here to let the user know he must select a transformation first
            pass

    def update_arg_values(self, arg_values: dict):
        self.arg_values = arg_values
        preset: Preset = state.get_prop(CURRENT_PRESET)
        transform = preset.transformations[self.index]
        new_transform = dataclasses.replace(transform, params=arg_values)
        new_preset = preset.replace_transform_at(preset, self.index, new_transform)
        state.set_prop(CURRENT_PRESET, new_preset)
        logger.debug(
            f"Arguments for {self.selected_transformation_name} updated to {arg_values}"
        )

    def get_selected_tranform_and_args(self):
        if self.selected_transformation_name is None:
            return None
        return (
            TRANSFORMATIONS[self.selected_transformation_name].transform,
            self.arg_values,
        )

    def load_args_dict(self, args_dict: dict):
        self.arg_values = args_dict

    def remove(self):
        self.remove_callback(self)

    def get_state(self):
        if self.selected_transformation_name is None:
            return None
        return {
            "transform_name": self.selected_transformation_name,
            "args": self.arg_values,
        }

    def load_state(self, state: Transformation):
        logger.debug(f"TransformationForm ({id(self)}): loading state {state}")
        if state is None:
            return

        self.selected_transformation_name = state.name
        self.ids.spinner.text = state.name or ""
        self.load_args_dict(state.params)
