from enum import StrEnum, IntEnum


class CustomStrEnum(StrEnum):
    """Custom string enum."""

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value

    @classmethod
    def get_values(cls) -> list:
        """Return a list of values."""
        return [item.value for item in cls]


class CustomIntEnum(IntEnum):
    """Custom integer enum."""

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return str(self.value)

    @classmethod
    def get_values(cls) -> list:
        """Return a list of values."""
        return [item.value for item in cls]
