import asyncio
from typing import Any, Coroutine
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from warriorfit.data.db.abc_repository import ABCRepository
from warriorfit.data.db.db_model import HrMessage


class MomRepository(ABCRepository):

    def __init__(self):
        super().__init__()

    async def add_hr_message(self,msg:HrMessage)->HrMessage | None:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(msg)
                await session.refresh(msg)
            return msg
        except IntegrityError as e:
            self._logger.error(f"Integrity error adding cross {getattr(msg, 'id', 'unknown')}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self._logger.error(f"Database error adding cross {getattr(msg, 'id', 'unknown')}: {str(e)}")
            return None

    async def get_all_hr_messages(self)-> list[Any] | None | Any:
        try:
            query = select(HrMessage)
            results = await self.fetch_and_log(query, "HrMessage")
            return results
        except SQLAlchemyError as e:
            self._logger.error(f"Database error fetching cross: {str(e)}")
            return []
        except Exception as e:
            self._logger.error(f"Unexpected error fetching cross: {str(e)}")

    async def delete_hr_message(self,id_msg:int)-> bool | None:
        try:
            async with self.SessionLocal() as session:
                query= select(HrMessage).where(HrMessage.id==id_msg)
                msg= await self.fetch_and_log(query, "HrMessage")
                if msg:
                    await session.delete(msg)
                    await session.commit()
                    return True
        except SQLAlchemyError as e:
            self._logger.error(f"Database error deleting cross {id_msg}: {str(e)}")
            return False
    
    async def get_last_added_hr_message_by_send_date(self)->HrMessage | None:
        try:
            async with self.SessionLocal() as session:
                query = select(HrMessage).order_by(HrMessage.datetime_created.desc())
                result = await session.execute(query)
                return result.scalars().first()
        except SQLAlchemyError as e:
            self._logger.error(f"Database error fetching cross: {str(e)}")
            return None
        except Exception as e:
            self._logger.error(f"Unexpected error fetching cross: {str(e)}")

async def main():
        repo = MomRepository()

        # one = await repo.add_hr_message(HrMessage(message="test", datetime_created=datetime.now()))
        # print(await repo.get_all_hr_messages())
        # two = await repo.add_hr_message(HrMessage(message="test2", datetime_created=datetime.now()))
        # print(await repo.get_all_hr_messages())
        # three = await repo.add_hr_message(HrMessage(message="test3", datetime_created=datetime.now()))
        # print(await repo.get_all_hr_messages())
        # # if one:
        # #     await repo.delete_hr_message(one.id)
        # print(await repo.get_all_hr_messages())
        last_one = await repo.get_last_added_hr_message_by_send_date()
        
        if last_one:
            print(last_one.message, last_one.datetime_created, last_one.id)
        else:
            print("No messages found.")


if __name__ == "__main__":
    asyncio.run(main())




