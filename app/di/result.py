from typing import TypeVar

T = TypeVar("T")
E = TypeVar("E")


def Ok(value):
    return (value, None)


def Err(error):
    return (None, error)
