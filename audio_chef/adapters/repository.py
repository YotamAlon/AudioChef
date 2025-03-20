import dataclasses
import json
import uuid
from collections.abc import Callable

import pedalboard
import peewee
from peewee import DatabaseProxy

from audio_chef.models.preset import (
    Preset,
    Transformation,
    NameChangeParameters,
    PresetMetadata, NameChangeMode,
)
from audio_chef.utils.transformations import TRANSFORMATIONS

db_proxy = DatabaseProxy()


def initialize_db(db_name: str) -> None:
    db = peewee.SqliteDatabase(db_name)
    db_proxy.initialize(db)
    db.create_tables([PresetModel, PluginModel])


class JSONField(peewee.TextField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


class PresetModel(peewee.Model):
    name = peewee.CharField(max_length=256)
    default = peewee.BooleanField(default=False)
    ext = peewee.CharField(max_length=64, default="")
    transformations = JSONField()
    name_changer = JSONField()

    class Meta:
        database = db_proxy


class PresetRepository:
    @classmethod
    def get_metadata(cls) -> list[PresetMetadata]:
        presets = PresetModel.select()
        return [cls.metadata_from_model(preset_model) for preset_model in presets]

    @classmethod
    def get_by_id(cls, preset_id: int) -> Preset:
        preset_model = PresetModel.get(id=preset_id)
        return cls.preset_from_model(preset_model)

    @classmethod
    def get_default(cls) -> Preset | None:
        default_preset = PresetModel.get_or_none(default=True)
        return cls.preset_from_model(default_preset) if default_preset else None

    @classmethod
    def make_default(cls, preset_id: int) -> None:
        default_preset = PresetModel.get_or_none(default=True)
        if default_preset:
            default_preset.default = False
            default_preset.save()

        preset_model = PresetModel.get(id=preset_id)
        preset_model.default = True
        preset_model.save()

    @classmethod
    def rename_preset(cls, preset_id: int, new_name: str) -> None:
        preset = PresetModel.get(PresetModel.id == preset_id)
        preset.name = new_name
        preset.save()

    @classmethod
    def save_preset(cls, preset: Preset) -> PresetMetadata:
        preset_model = PresetModel.create(
            name=str(uuid.uuid4()),
            ext=preset.ext,
            transformations=[
                dataclasses.asdict(transform) for transform in preset.transformations
            ],
            name_changer=dataclasses.asdict(preset.name_change_parameters),
        )
        return cls.metadata_from_model(preset_model)

    @classmethod
    def delete(cls, preset_id: int) -> None:
        PresetModel.delete_by_id(preset_id)

    @staticmethod
    def metadata_from_model(model: PresetModel) -> PresetMetadata:
        return PresetMetadata(
            id=model.id,
            default=model.default,
            name=model.name,
        )

    @staticmethod
    def preset_from_model(model: PresetModel) -> Preset:
        return Preset(
            ext=model.ext,
            transformations=[
                Transformation(
                    name=transformation["name"], params=transformation["params"]
                )
                for transformation in model.transformations
            ],
            name_change_parameters=NameChangeParameters(
                mode=NameChangeMode(model.name_changer["mode"]),
                wildcards_input=model.name_changer["wildcards_input"],
                replace_from_input=model.name_changer["replace_from_input"],
                replace_to_input=model.name_changer["replace_to_input"],
            ),
        )


class PluginModel(peewee.Model):
    name = peewee.CharField(max_length=256)
    path = peewee.CharField(max_length=2048)
    params = JSONField(default={})

    class Meta:
        database = db_proxy


class PluginRepository:
    @classmethod
    def save_plugin(cls, path: str) -> None:
        pedalboard_plugin: pedalboard.VST3Plugin = pedalboard.load_plugin(path)
        PluginModel.get_or_create(name=pedalboard_plugin.name, path=path)

    @classmethod
    def get_available_transformations(cls) -> list[Transformation]:
        static_transformations = TRANSFORMATIONS.keys()
        transformations = [
            Transformation(name=transform_name, params={})
            for transform_name in static_transformations
        ]
        plugins = PluginModel.select()
        transformations.extend(
            [
                Transformation(
                    name=plugin.name,
                    params={},
                    show_editor=cls._get_show_editor_func(plugin),
                )
                for plugin in plugins
            ]
        )
        return sorted(transformations, key=lambda t: t.name)

    @staticmethod
    def _get_show_editor_func(plugin_model: PluginModel) -> Callable[[dict], dict]:
        def show_editor(params: dict) -> dict:
            plugin = pedalboard.load_plugin(plugin_model.path, parameter_values=params)
            plugin.show_editor()
            return {param.python_name: param.type(getattr(plugin, param.python_name)) for param in plugin.parameters.values()}

        return show_editor
