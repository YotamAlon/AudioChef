import logging

from kivy.uix.popup import Popup
from helper_classes import FloatArgumentBox, FileArgumentBox, OptionsBox
from kivy.properties import ObjectProperty


logger = logging.getLogger("audiochef")


class TransformationParameterPopup(Popup):
    save_callback = ObjectProperty()

    def __init__(self, transformation_name, arguments, **kwargs):
        super().__init__(**kwargs)
        for arg in arguments:
            logger.debug(
                f"TransformationForm ({id(self)}): adding FloatArgumentBox(type={arg.type}, name={arg.name}, "
                f"text={str(arg.default) if arg.default is not None else arg.type()}"
            )
            if arg.type is float:
                self.ids.args_box.add_widget(
                    FloatArgumentBox(
                        transformation_name=transformation_name,
                        name=arg.name,
                        initial=str(arg.default),
                    )
                )
            elif arg.type is str:
                self.ids.args_box.add_widget(FileArgumentBox(name=arg.name))
            else:
                self.ids.args_box.add_widget(
                    OptionsBox(name=arg.name, options=arg.options)
                )

    def get_argument_dict(self):
        return {arg.name: arg.type(arg.text) for arg in self.ids.args_box.children}
