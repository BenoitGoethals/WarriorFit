import logging
from datetime import datetime
import httpx
from warriorfit.core.Gender import Gender
from warriorfit.data.model.db_model import ServiceMen
from warriorfit.logic.singleton import Singleton
class BEMILService(metaclass=Singleton):
    BASE_URL = "http://192.168.0.30:8400"

    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    def _build_serviceman(self, data: dict) -> ServiceMen:
        if "gender" in data and isinstance(data["gender"], str):
            try:
                data["gender"] = Gender(data["gender"])
            except ValueError:
                pass

        if "birthdate" in data and isinstance(data["birthdate"], str):
            try:
                data["birthdate"] = datetime.strptime(data["birthdate"], "%Y-%m-%d").date()
            except ValueError:
                pass

        if "unit" in data and isinstance(data["unit"], dict):
            if "unit_id" not in data:
                data["unit_id"] = data["unit"].get("id")

        valid_fields = {
            "id", "first_name", "last_name", "mail", "rank", "service_number",
            "birthdate", "gender", "unit_id", "para", "ops_test"
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return ServiceMen(**filtered_data)

    async def get_be_mil_by_id(self, be_mil_serial_number: str) -> ServiceMen | None:
        """Retrieve a specific ServiceMen by its service number."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/servicemen?serial={be_mil_serial_number}"
                )
                response.raise_for_status()
                data = response.json()
                if not data:
                    return None
                return self._build_serviceman(data)

            except httpx.HTTPStatusError as e:
                self.__logger.error(
                    f"Error fetching BEMIL by serial number {be_mil_serial_number}: {e}"
                )
                return None

    async def get_all_be_mil_from_unit(
            self, unit_name: str
    ) -> list[ServiceMen] | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.BASE_URL}/servicemen/unit/{unit_name}")
                response.raise_for_status()  # raises error if status != 200
                resp = response.json()
                return [self._build_serviceman(item) for item in resp]
            except httpx.HTTPStatusError as e:
                self.__logger.error(f"Error fetching BEMILs from unit {unit_name}: {e}")
                return None



if __name__ == "__main__":
    import asyncio

    async def _main():
        be_mil_service = BEMILService()
        # result = await be_mil_service.get_all_be_mil_from_unit("1/3 Bn Lanciers")
        # for item in result:
        #     print(item)
        one = await be_mil_service.get_be_mil_by_id("SN-90210")
        print("Single:", one)

        two = await be_mil_service.get_be_mil_by_id("SN-90211")
        print("Single:", two)


    asyncio.run(_main())
