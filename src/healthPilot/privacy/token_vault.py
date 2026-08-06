"""In-memory token vault for reversible de-identification (PostgreSQL later)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field


@dataclass
class TokenVault:
    """Maps placeholder tokens to original values for a single session/request."""

    _forward: dict[str, str] = field(default_factory=dict)
    _reverse: dict[str, str] = field(default_factory=dict)

    def tokenize(self, entity_type: str, original: str) -> str:
        existing = self._reverse.get(original)
        if existing:
            return existing

        token = f"{{{{{entity_type}_{len(self._forward) + 1}}}}}"
        self._forward[token] = original
        self._reverse[original] = token
        return token

    def detokenize(self, text: str) -> str:
        for token, original in self._forward.items():
            text = text.replace(token, original)
        return text

    def as_dict(self) -> dict[str, str]:
        return dict(self._forward)

    @classmethod
    def from_dict(cls, mapping: dict[str, str]) -> TokenVault:
        vault = cls()
        vault._forward = dict(mapping)
        vault._reverse = {original: token for token, original in mapping.items()}
        return vault


def new_session_id() -> str:
    return str(uuid.uuid4())


TOKEN_PATTERN = re.compile(r"\{\{[A-Z0-9_]+_\d+\}\}")
