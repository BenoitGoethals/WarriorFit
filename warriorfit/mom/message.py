from datetime import datetime
from typing import Any


class Message:
    """A class representing a message in MOM."""

    def __init__(self, content: Any):
        self.id = 0
        self.content = content
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        content = self._content_to_dict(self.content)
        return {
            "id": self.id,
            "message": content,
            "datetime_created": self.timestamp.isoformat(),
        }

    @staticmethod
    def _content_to_dict(content: Any) -> Any:
        # Already JSON primitives
        if isinstance(content, (dict, list, tuple, str, int, float, bool)) or content is None:
            return content
        # Pydantic v2
        if hasattr(content, "model_dump"):
            return content.model_dump()
        # Common custom
        if hasattr(content, "to_dict") and callable(content.to_dict):
            return content.to_dict()
        # Dataclass
        try:
            from dataclasses import asdict, is_dataclass

            if is_dataclass(content):
                return asdict(content)  # type: ignore[arg-type]
        except Exception:
            pass
        # Shallow public attributes
        if hasattr(content, "__dict__"):
            return {
                k: Message._content_to_dict(v)
                for k, v in content.__dict__.items()
                if not k.startswith("_")
            }
        # Fallback
        return str(content)

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict())
