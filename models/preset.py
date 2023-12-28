import dataclasses

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
