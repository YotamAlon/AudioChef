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
