from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from warriorfit.data.model.db_model import HierarchyNode
from warriorfit.data.repositories.abc_repository import ABCRepository


class HierarchyRepository(ABCRepository):
    def __init__(self, config=None):
        super().__init__(config=config)

    async def get_full_tree(self) -> HierarchyNode | None:
        """Load the root node with 4 levels of children eagerly (BN → Cie → Plt → Sec)."""
        query = (
            select(HierarchyNode)
            .where(HierarchyNode.parent_id.is_(None))
            .options(
                selectinload(HierarchyNode.children)
                .selectinload(HierarchyNode.children)
                .selectinload(HierarchyNode.children)
                .selectinload(HierarchyNode.children)
            )
        )
        try:
            async with self.SessionLocal() as session:
                result = await session.execute(query)
                return result.scalar_one_or_none()
        except SQLAlchemyError:
            self._logger.exception("Failed to load hierarchy tree")
            return None

    async def delete_all(self) -> None:
        try:
            async with self.SessionLocal() as session, session.begin():
                await session.execute(delete(HierarchyNode))
        except SQLAlchemyError:
            self._logger.exception("Failed to delete hierarchy nodes")

    async def save_root(self, root: HierarchyNode) -> bool:
        try:
            async with self.SessionLocal() as session, session.begin():
                session.add(root)
            return True
        except SQLAlchemyError:
            self._logger.exception("Failed to save hierarchy root")
            return False
