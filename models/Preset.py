from peewee import Model, CharField, BooleanField, SqliteDatabase
from models import JSONField

db = SqliteDatabase('presets.db')


class Preset(Model):
    name = CharField(max_length=255)
    default = BooleanField()
    ext = CharField(max_length=64)
    transformations = JSONField()
    name_changer = JSONField()

    class Meta:
        database = db
