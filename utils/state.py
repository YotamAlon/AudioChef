import typing


class State:
    """Basic implementation of a state object"""
    _state: typing.ClassVar[typing.Dict[str, typing.Any]] = {}

    def set_prop(self, prop: str, value: typing.Any) -> None:
        self._state[prop] = value

    def get_prop(self, prop: str) -> typing.Any:
        return self._state.get(prop, None)


state = State()
