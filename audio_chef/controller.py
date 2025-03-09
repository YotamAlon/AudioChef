import peewee

from audio_chef.adapters.repository import (
    PluginModel,
    PluginRepository,
    PresetModel,
    PresetRepository,
    db_proxy,
)
from audio_chef.app import ControllerProtocol
from audio_chef.models.preset import NameChangeParameters, Preset, Transformation


class Controller(ControllerProtocol):
    def get_default_preset(self) -> Preset:
        default_preset = PresetRepository.get_default()
        if default_preset:
            preset = default_preset
        else:
            preset = Preset(
                ext="",
                transformations=[],
                name_change_parameters=NameChangeParameters(
                    mode="replace",
                    wildcards_input="",
                    replace_from_input="",
                    replace_to_input="",
                ),
            )
        return preset

    def get_available_transformations(self) -> list[Transformation]:
        return PluginRepository.get_available_transformations()

    def save_plugin(self, plugin_path: str) -> None:
        PluginRepository.save_plugin(plugin_path)

    def get_preset_by_id(self, preset_id: int) -> Preset:
        return PresetRepository.get_by_id(preset_id)

    def initialize_db(self) -> None:
        db = peewee.SqliteDatabase("presets.db")
        db_proxy.initialize(db)
        db.create_tables([PresetModel, PluginModel])
