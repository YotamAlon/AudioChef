import logging
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from components.transformation_parameter_popup import TransformationParameterPopup
from utils.transformations import TRANSFORMATIONS

logger = logging.getLogger("audiochef")


class TransformationForm(BoxLayout):
    remove_callback = ObjectProperty()
    transformations = TRANSFORMATIONS.keys()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_transformation_name: str = None
        self.arg_values = {}

    def shift_up(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, self_index + 1)

    def shift_down(self):
        self_index = self.parent.children.index(self)
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self, max(self_index - 1, 0))

    def select_transformation(self, transform_name):
        self.selected_transformation_name = transform_name
        self.ids.args_box.clear_widgets()

    def open_parameter_popup(self):
        TransformationParameterPopup(
            self.selected_transformation_name,
            TRANSFORMATIONS[self.selected_transformation_name].arguments,
            title=f"Edit {self.selected_transformation_name} parameters",
            save_callback=self.update_arg_values,
        ).open()

    def update_arg_values(self, arg_values: dict):
        self.arg_values = arg_values
        logger.debug(f"Arguments for {self.selected_transformation_name} updated to {arg_values}")

    def get_selected_tranform_and_args(self):
        if self.selected_transformation_name is None:
            return None
        return TRANSFORMATIONS[self.selected_transformation_name].transform, self.arg_values

    def load_args_dict(self, args_dict: dict):
        self.arg_values = args_dict

    def remove(self):
        self.remove_callback(self)

    def get_state(self):
        if self.selected_transformation_name is None:
            return None
        return {"transform_name": self.selected_transformation_name, "args": self.arg_values}

    def load_state(self, state):
        logger.debug(f"TransformationForm ({id(self)}): loading state {state}")
        if state is None:
            return

        self.selected_transformation_name = state["transform_name"]
        self.ids.spinner.text = state["transform_name"]
        self.load_args_dict(state["args"])
