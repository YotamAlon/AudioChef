from typing import Any


class State:
    """Basic implementation of a state object"""
    _state = {}

    def set_prop(self, prop: str, value: Any) -> None:
        self._state[prop] = value

    def get_prop(self, prop: str) -> Any:
        return self._state.get(prop, None)


state = State()