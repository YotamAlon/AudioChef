import typing

T = typing.TypeVar("T")


def find_first(
    iterable: typing.Iterable[T], match_func: typing.Callable[[T], bool]
) -> T | None:
    for item in iterable:
        if match_func(item):
            return item

    return None
