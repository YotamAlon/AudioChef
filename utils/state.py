import typing


class State:
    """Basic implementation of a watchable state object"""

    _state: typing.ClassVar[dict[str, typing.Any]] = {}
    _watchers: typing.ClassVar[dict[str, list[typing.Callable]]] = {}

    def set_prop(self, prop: str, value: typing.Any) -> None:
        self._state[prop] = value
        for watcher in self._watchers.get(prop, []):
            watcher(value)

    def get_prop(self, prop: str, default: typing.Any = None) -> typing.Any:
        return self._state.get(prop, default)

    def set_watcher(self, prop: str, callback: typing.Callable) -> None:
        self._watchers.setdefault(prop, []).append(callback)


state = State()
