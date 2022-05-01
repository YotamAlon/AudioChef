from peewee import Model, CharField, BooleanField
from models import JSONField, db_proxy


class Preset(Model):
    name = CharField(max_length=255)
    default = BooleanField()
    ext = CharField(max_length=64)
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
