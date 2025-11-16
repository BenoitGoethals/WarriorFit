import sqlite3
import asyncio
import logging
from core.Gender import Gender

from logic.singleton import Singleton
from military_api_rest.service_men_be import ServiceMenBE
from military_api_rest.unit_be import UnitBE

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        from utils.Os import Os  # optional helper if available
        project_root = Os.get_project_root()
    except Exception:
        project_root = None
    if project_root:
        log_dir = project_root / "logs"
        try:
            log_dir.mkdir(exist_ok=True)
            fh = logging.FileHandler(log_dir / "service_men_db.log", mode="a")
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class DbServiceServiceMen(metaclass=Singleton):
    """#Deprecated Service class for managing DB operations."""

    def __init__(self, db_file: str = "military_be.db"):
        self.db_file = db_file
        logger.info(f"DbServiceServiceMen initialized with db_file={db_file}")

    def _connect(self):
        """Create a new DB connection."""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = None
            return conn
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            raise

    async def get_all_service_men(self) -> list[ServiceMenBE]:
        try:
            loop = asyncio.get_running_loop()
            def _work():
                conn = self._connect()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT s.*,u.name as unit_name, u.base_location FROM service_men s JOIN units u ON s.unit_id = u.id ORDER BY s.id;")
                    rows = cursor.fetchall()
                    return rows or []
                finally:
                    conn.close()
            rows = await loop.run_in_executor(None, _work)
            logger.info(f"Fetched {len(rows)} service men")
            service_mens = []
            for row in rows:
                sm = ServiceMenBE(id=row[0], service_number=row[5], last_name=row[2], first_name=row[1], birthdate=row[6],
                                gender=Gender.M if row[6] == 'M' else Gender.F,
                                unit=UnitBE(id=row[10], name=row[11], base_location=row[12]), rank=row[4],
                                para=row[8], ops_test=row[9],mail=row[3])
                service_mens.append(sm)
            return service_mens
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_all_service_men: {e}")
            return []
        except RuntimeError as e:
            logger.error(f"Runtime error in get_all_service_men: {e}")
            return []

    async def get_service_men_by_service_number(self, service: str)->list[ServiceMenBE]:
        if service is None:
            logger.warning("get_service_men_by_service_number called with None service number")
            return None
        try:
            loop = asyncio.get_running_loop()

            def _work():
                conn = self._connect()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT s.*, u.name as unit_name,u.base_location FROM service_men s JOIN units u ON s.unit_id = u.id WHERE s.service_number = ? ORDER BY s.id;",
                        (service,),
                    )
                    rows = cursor.fetchall()
                    return rows or []
                finally:
                    conn.close()

            rows = await loop.run_in_executor(None, _work)
            logger.info(f"Fetched {len(rows)} service men for service_number={service}")
            service_mens = []
            for row in rows:
                sm = ServiceMenBE(id=row[0], service_number=row[5], last_name=row[2], first_name=row[1], birthdate=row[6],
                                gender=Gender.M if row[6] == 'M' else Gender.F,
                                unit=UnitBE(id=row[10], name=row[11], base_location=row[12]), rank=row[4],
                                para=row[8], ops_test=row[9], mail=row[3])
                service_mens.append(sm)
            return service_mens
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_service_men_by_service_number({service}): {e}")
            return []
        except RuntimeError as e:
            logger.error(f"Runtime error in get_service_men_by_service_number({service}): {e}")
            return []

    async def get_all_units(self):
        try:
            loop = asyncio.get_running_loop()
            def _work():
                conn = self._connect()
                try:
                    cursor = conn.cursor()
                    cursor.execute("Select id, name, base_location from units")
                    rows = cursor.fetchall()
                    return rows or []
                finally:
                    conn.close()
            rows = await loop.run_in_executor(None, _work)
            logger.info(f"Fetched {len(rows)} units")
            units = []
            for row in rows:
                unit = UnitBE(id=row[0], name=row[1], base_location=row[2])
                units.append(unit)
            return units
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_all_units: {e}")
            return []
        except RuntimeError as e:
            logger.error(f"Runtime error in get_all_units: {e}")
            return []

    async def all_service_men_from_a_unit(self, unit: str):
        if unit is None:
            logger.warning("all_service_men_from_a_unit called with None unit")
            return None
        try:
            loop = asyncio.get_running_loop()
            def _work():
                conn = self._connect()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT s.*, u.name as unit_name,u.base_location FROM service_men s JOIN units u ON s.unit_id = u.id WHERE u.name = ? ORDER BY s.id;",
                        (unit,))
                    rows = cursor.fetchall()
                    return rows or []
                finally:
                    conn.close()
            rows = await loop.run_in_executor(None, _work)
            logger.info(f"Fetched {len(rows)} service men for unit='{unit}'")
            service_mens = []
            for row in rows:
                sm = ServiceMenBE(id=row[0], service_number=row[5], last_name=row[2], first_name=row[1], birthdate=row[6],
                                gender=Gender.M if row[6] == 'M' else Gender.F,
                                unit=UnitBE(id=row[10], name=row[11], base_location=row[12]), rank=row[4],
                                para=row[8], ops_test=row[9], mail=row[3])
                service_mens.append(sm)
            return service_mens
        except sqlite3.Error as e:
            logger.error(f"SQLite error in all_service_men_from_a_unit('{unit}'): {e}")
            return []
        except RuntimeError as e:
            logger.error(f"Runtime error in all_service_men_from_a_unit('{unit}'): {e}")
            return []



#Deprecated
if __name__ == "__main__":
    async def _main():
        db = DbServiceServiceMen()
        print(await db.get_all_service_men())
        print(await db.get_all_units())
        print(await db.get_service_men_by_service_number("BE-20250001"))
        for row in await db.all_service_men_from_a_unit("1-3 Bn Lanciers"):
            print(row)
    asyncio.run(_main())