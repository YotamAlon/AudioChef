import typing

import kivy.properties  # type: ignore
import kivy.uix.popup  # type: ignore
from audio_chef.utils.transformations import Argument
from audio_chef.components.helper_classes import FloatArgumentBox, FileArgumentBox, OptionsBox


class TransformationParameterPopup(kivy.uix.popup.Popup):
    def __init__(
        self,
        index: int,
        transformation_name: str,
        arguments: typing.List[Argument],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.index = index
        for arg in arguments:
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

    def get_arguments(self):
        return {arg.name: arg.get_value() for arg in self.ids.args_box.children}
