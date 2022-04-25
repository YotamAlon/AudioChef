from typing import Type, Any
from dataclasses import dataclass
from pedalboard import (
    Plugin,
    Convolution,
    Compressor,
    Chorus,
    Distortion,
    Gain,
    HighpassFilter,
    LadderFilter,
    Limiter,
    LowpassFilter,
    Phaser,
    Reverb,
)


@dataclass()
class Argument:
    name: str
    type: Type
    default: Any = None
    options: list = None
    min: float = None
    max: float = None
    step: float = None

    def __post_init__(self):
        if self.type is float:
            self.min = self.min or 0
            self.max = self.max or 100
            self.step = self.step or 10


@dataclass
class TransformationWrapper:
    transform: Plugin
    arguments: list


TRASNFORMATIONS = {
    "Convolution": TransformationWrapper(
        Convolution,
        [
            Argument("impulse_response_filename", str),
            Argument("mix", float, 1.0),
        ],
    ),
    "Compressor": TransformationWrapper(
        Compressor,
        [
            Argument("threshold_db", float, 0),
            Argument("ratio", float, 1),
            Argument("attack_ms", float, 1.0),
            Argument("release_ms", float, 100),
        ],
    ),
    "Chorus": TransformationWrapper(
        Chorus,
        [
            Argument("rate_hz", float, 1.0),
            Argument("depth", float, 0.25),
            Argument("centre_delay_ms", float, 7.0),
            Argument("feedback", float, 0.0),
            Argument("mix", float, 0.5),
        ],
    ),
    "Distortion": TransformationWrapper(Distortion, [Argument("drive_db", float, 25)]),
    "Gain": TransformationWrapper(Gain, [Argument("gain_db", float, 1.0)]),
    "HighpassFilter": TransformationWrapper(
        HighpassFilter, [Argument("cutoff_frequency_hz", float, 50)]
    ),
    "LadderFilter": TransformationWrapper(
        LadderFilter,
        [
            Argument(
                "mode",
                LadderFilter.Mode,
                LadderFilter.LPF12,
                options=LadderFilter.Mode.__entries,
            ),
            Argument("cutoff_hz", float, 200),
            Argument("resonance", float, 0),
            Argument("drive", float, 1.0),
        ],
    ),
    "Limiter": TransformationWrapper(
        Limiter,
        [Argument("threshold_db", float, -10.0), Argument("release_ms", float, 100.0)],
    ),
    "LowpassFilter": TransformationWrapper(
        LowpassFilter, [Argument("cutoff_frequency_hz", float, 50)]
    ),
    "Phaser": TransformationWrapper(
        Phaser,
        [
            Argument("rate_hz", float, 1.0),
            Argument("depth", float, 0.5),
            Argument("centre_frequency_hz", float, 1300.0),
            Argument("feedback", float, 0.0),
            Argument("mix", float, 0.5),
        ],
    ),
    "Reverb": TransformationWrapper(
        Reverb,
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
