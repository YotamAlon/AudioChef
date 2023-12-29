import dataclasses
from datetime import datetime

from peewee import Model, CharField, BooleanField

from models import JSONField, db_proxy


@dataclasses.dataclass(frozen=True)
class Transformation:
    name: str
    params: dict


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
    name: str
    ext: str
    transformations: list[Transformation]
    name_change_parameters: NameChangeParameters


class PresetModel(Model):
    name = CharField(max_length=255)
    default = BooleanField(default=False)
    ext = CharField(max_length=64, default="")
    transformations = JSONField()
    name_changer = JSONField()

    class Meta:
        database = db_proxy

    @classmethod
    def rename(cls, preset_id, new_name):
        preset = cls.get(cls.id == preset_id)
        preset.name = new_name
        preset.save()

    @classmethod
    def make_default(cls, preset_id, val):
        preset = cls.get(cls.id == preset_id)
        preset.default = val
        preset.save()
