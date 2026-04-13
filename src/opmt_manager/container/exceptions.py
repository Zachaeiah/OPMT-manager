from typing import Type, Optional

class DependencyNotFoundError(KeyError):
    def __init__(
        self,
        cls: Type,
        name: Optional[str] = None,
        path: Optional[list[tuple[Type, Optional[str]]]] = None,
        available: Optional[list[tuple[Type, Optional[str]]]] = None,
    ):
        self.cls = cls
        self.name = name
        self.path = path or []
        self.available = available or []

        super().__init__(self._build_message())

    def _build_message(self) -> str:
        parts = [
            f"Dependency not found: {self.cls.__name__}"
        ]

        if self.name:
            parts.append(f"(name='{self.name}')")

        if self.path:
            chain = " -> ".join(
                f"{c.__name__}:{n}" if n else c.__name__
                for c, n in self.path
            )
            parts.append(f"\nResolution path: {chain}")

        if self.available:
            avail = ", ".join(
                f"{c.__name__}:{n}" if n else c.__name__
                for c, n in self.available
            )
            parts.append(f"\nAvailable providers: {avail}")

        return " ".join(parts)