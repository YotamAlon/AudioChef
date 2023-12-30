import dataclasses


@dataclasses.dataclass(frozen=True)
class Plugin:
    path: str
    params: dict
