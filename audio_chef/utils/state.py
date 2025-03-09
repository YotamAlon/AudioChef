import logging
import typing


class State:
    """Basic implementation of a watchable state object"""

    _state: typing.ClassVar[dict[typing.Hashable, typing.Any]] = {}
    _watchers: typing.ClassVar[dict[typing.Hashable, list[typing.Callable]]] = {}
    _reducers: typing.ClassVar[dict[typing.Hashable, list[typing.Callable]]] = {}

    def set_prop(self, prop: typing.Hashable, value: typing.Any) -> None:
        if prop in self._state and self._state[prop] == value:
            return

        self._state[prop] = value
        for reducer in self._reducers.get(prop, []):
            reduced_prop, reduced_value = reducer(value)
            self.set_prop(reduced_prop, reduced_value)

        for watcher in self._watchers.get(prop, []):
            watcher(value)

    def get_prop(self, prop: str, default: typing.Any = None) -> typing.Any:
        return self._state.get(prop, default)

    def set_watcher(self, prop: str, callback: typing.Callable) -> None:
        self._watchers.setdefault(prop, []).append(callback)

    def set_reducers(self, prop: str, callback: typing.Callable[[...], tuple[typing.Hashable, typing.Any]]):
        self._reducers.setdefault(prop, []).append(callback)


state = State()
