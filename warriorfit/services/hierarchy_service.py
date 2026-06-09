import json
import logging
from pathlib import Path
from typing import Any

from warriorfit.data.model.db_model import HierarchyNode
from warriorfit.data.repositories.hierarchy_repository import HierarchyRepository


class HierarchyService:
    def __init__(self, repo: HierarchyRepository = None):
        self._repo = repo if repo is not None else HierarchyRepository()
        self._logger = logging.getLogger(__name__)

    async def get_tree(self) -> dict[str, Any] | None:
        root = await self._repo.get_full_tree()
        return self._node_to_dict(root) if root is not None else None

    async def load_from_file(self, path: str | Path) -> bool:
        path = Path(path)
        if not path.exists():
            self._logger.error("Hierarchy seed file not found: %s", path)
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self._logger.exception("Failed to read hierarchy file %s", path)
            return False
        return await self.import_tree(data)

    async def save_to_file(self, path: str | Path) -> bool:
        tree = await self.get_tree()
        if tree is None:
            self._logger.warning("No hierarchy in DB to export")
            return False
        try:
            Path(path).write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            self._logger.exception("Failed to write hierarchy to %s", path)
            return False
        return True

    async def import_tree(self, data: dict[str, Any]) -> bool:
        await self._repo.delete_all()
        root = self._dict_to_node(data)
        return await self._repo.save_root(root)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _node_to_dict(self, node: HierarchyNode) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": node.name,
            "echelon": node.echelon,
        }
        if node.callsign:
            d["callsign"] = node.callsign
        if node.establishment_strength is not None:
            d["establishment_strength"] = node.establishment_strength
        if node.role:
            d["role"] = node.role
        if node.children:
            d["children"] = [self._node_to_dict(c) for c in node.children]
        return d

    def _dict_to_node(self, data: dict[str, Any]) -> HierarchyNode:
        node = HierarchyNode(
            name=data["name"],
            echelon=data["echelon"],
            callsign=data.get("callsign"),
            establishment_strength=data.get("establishment_strength"),
            role=data.get("role"),
        )
        for child_data in data.get("children", []):
            child = self._dict_to_node(child_data)
            node.children.append(child)
        return node
