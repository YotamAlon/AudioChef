import dataclasses
import typing
from datetime import datetime


@dataclasses.dataclass(frozen=True)
class Transformation:
    name: str | None
    params: dict
    show_editor: typing.Callable[[dict], dict] | None = None


@dataclasses.dataclass(frozen=True)
class NameChangeParameters:
    mode: str
    wildcards_input: str
    replace_from_input: str
    replace_to_input: str

    def change_name(self, old_name: str) -> str:
        if self.mode == "wildcards":
            new_name = self.wildcards_input
            new_name = new_name.replace("$item", old_name)
            new_name = new_name.replace("$date", str(datetime.today()))
            return new_name
        else:
            if self.replace_from_input == "":
                return old_name
            return old_name.replace(self.replace_from_input, self.replace_to_input)


@dataclasses.dataclass(frozen=True)
class Preset:
    ext: str
    transformations: list[Transformation]
    name_change_parameters: NameChangeParameters

    @classmethod
    def replace_transform_at(
        cls, preset: typing.Self, index: int, new_transform: Transformation
    ) -> typing.Self:
        new_transformations = preset.transformations[:]
        new_transformations[index] = new_transform
        new_preset = dataclasses.replace(preset, transformations=new_transformations)
        return new_preset

    @classmethod
    def move_transform(
        cls, preset: typing.Self, from_index: int, to_index: int
    ) -> typing.Self:
        new_transformations = preset.transformations[:]
        transform = new_transformations.pop(from_index)
        new_transformations.insert(to_index, transform)
        new_preset = dataclasses.replace(preset, transformations=new_transformations)
        return new_preset


@dataclasses.dataclass(frozen=True)
class PresetMetadata:
    id: int | None
    default: bool
    name: str
