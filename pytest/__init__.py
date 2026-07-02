from __future__ import annotations

import re
from contextlib import AbstractContextManager


class RaisesContext(AbstractContextManager["RaisesContext"]):
    def __init__(self, expected_exception: type[BaseException], match: str | None = None) -> None:
        self.expected_exception = expected_exception
        self.match = match

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            raise AssertionError(f"Did not raise {self.expected_exception.__name__}")

        if not issubclass(exc_type, self.expected_exception):
            return False

        if self.match is not None and not re.search(self.match, str(exc)):
            raise AssertionError(
                f"Exception message {exc!s} does not match pattern {self.match!r}"
            )

        return True


def raises(expected_exception: type[BaseException], match: str | None = None) -> RaisesContext:
    return RaisesContext(expected_exception, match=match)

