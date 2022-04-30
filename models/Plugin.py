from peewee import Model, CharField, BlobField
from models import db_proxy


class Plugin(Model):
    name = CharField(max_length=255)
    vst3_file = BlobField()

    class Meta:
        db = db_proxy
