import logging
import httpx
from logic.singleton import Singleton
from military_api_rest.service_men_be import ServiceMenBE

BASE_URL = "http://127.0.0.1:8001"


class BEMILService(metaclass=Singleton):
    """Service class for managing BEMIL-related operations."""

    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    async def get_all_be_mil_from_unit(
        self, unit_name: str
    ) -> list[ServiceMenBE] | None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{BASE_URL}/service-men/unit/{unit_name}")
                response.raise_for_status()  # raises error if status != 200
                resp = response.json()
                return [ServiceMenBE(**item) for item in resp]
            except httpx.HTTPStatusError as e:
                self.__logger.error(f"Error fetching BEMILs from unit {unit_name}: {e}")
                return None

    async def get_be_mil_by_id(self, be_mil_serial_number: str) -> ServiceMenBE | None:
        """Retrieve a specific ServiceMen by its service number."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{BASE_URL}/service-men/{be_mil_serial_number}"
                )
                response.raise_for_status()
                data = response.json()
                return ServiceMenBE(**data)
            except httpx.HTTPStatusError as e:
                self.__logger.error(
                    f"Error fetching BEMIL by serial number {be_mil_serial_number}: {e}"
                )
                return None


#
# if __name__ == "__main__":
#     import asyncio
#
#     async def _main():
#         be_mil_service = BEMILService()
#         result = await be_mil_service.get_all_be_mil_from_unit("1/3 Bn Lanciers")
#         for item in result:
#             print(item)
#         one = await be_mil_service.get_be_mil_by_id("BE-20250001")
#         print("Single:", one)
#
#         two = await be_mil_service.get_be_mil_by_id("BE-20250002")
#         print("Single:", two)
#
#
#     asyncio.run(_main())
