import dataclasses
import typing

import pedalboard


@dataclasses.dataclass()
class Argument:
    name: str
    type: typing.Type
    default: typing.Any = None
    options: typing.Union[typing.List[str], None] = None
    min: typing.Union[float, None] = None
    max: typing.Union[float, None] = None
    step: typing.Union[float, None] = None

    def __post_init__(self):
        if self.type is float:
            self.min = self.min or 0
            self.max = self.max or 100
            self.step = self.step or 10


@dataclasses.dataclass
class TransformationWrapper:
    transform: typing.Type[pedalboard.Plugin]
    arguments: list


TRANSFORMATIONS = {
    "Convolution": TransformationWrapper(
        pedalboard.Convolution,
        [
            Argument("impulse_response_filename", str),
            Argument("mix", float, 1.0),
        ],
    ),
    "Compressor": TransformationWrapper(
        pedalboard.Compressor,
        [
            Argument("threshold_db", float, 0),
            Argument("ratio", float, 1),
            Argument("attack_ms", float, 1.0),
            Argument("release_ms", float, 100),
        ],
    ),
    "Chorus": TransformationWrapper(
        pedalboard.Chorus,
        [
            Argument("rate_hz", float, 1.0),
            Argument("depth", float, 0.25),
            Argument("centre_delay_ms", float, 7.0),
            Argument("feedback", float, 0.0),
            Argument("mix", float, 0.5),
        ],
    ),
    "Distortion": TransformationWrapper(pedalboard.Distortion, [Argument("drive_db", float, 25)]),
    "Gain": TransformationWrapper(pedalboard.Gain, [Argument("gain_db", float, 1.0)]),
    "HighpassFilter": TransformationWrapper(
        pedalboard.HighpassFilter, [Argument("cutoff_frequency_hz", float, 50)]
    ),
    "LadderFilter": TransformationWrapper(
        pedalboard.LadderFilter,
        [
            Argument(
                "mode",
                pedalboard.LadderFilter.Mode,
                pedalboard.LadderFilter.LPF12,
                options=[entry.name for entry in pedalboard.LadderFilter.Mode],
            ),
            Argument("cutoff_hz", float, 200),
            Argument("resonance", float, 0),
            Argument("drive", float, 1.0),
        ],
    ),
    "Limiter": TransformationWrapper(
        pedalboard.Limiter,
        [Argument("threshold_db", float, -10.0), Argument("release_ms", float, 100.0)],
    ),
    "LowpassFilter": TransformationWrapper(
        pedalboard.LowpassFilter, [Argument("cutoff_frequency_hz", float, 50)]
    ),
    "Phaser": TransformationWrapper(
        pedalboard.Phaser,
        [
            Argument("rate_hz", float, 1.0),
            Argument("depth", float, 0.5),
            Argument("centre_frequency_hz", float, 1300.0),
            Argument("feedback", float, 0.0),
            Argument("mix", float, 0.5),
        ],
    ),
    "Reverb": TransformationWrapper(
        pedalboard.Reverb,
        [
            Argument("room_size", float, 0.5),
            Argument("damping", float, 0.5),
            Argument("wet_level", float, 0.33),
            Argument("dry_level", float, 0.4),
            Argument("width", float, 1.0),
            Argument("freeze_mode", float, 0.0),
        ],
    ),
}
