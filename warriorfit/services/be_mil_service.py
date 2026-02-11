import json
import logging
from datetime import datetime, date
import httpx
from pydantic import BaseModel, ConfigDict
from pydantic.v1 import Field

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.core.Gender import Gender
from warriorfit.data.model.db_model import ServiceMen
from warriorfit.logic.singleton import Singleton
from warriorfit.mom.message import Message

class ServiceMenSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Pydantic model for ServiceMen validation and serialization."""
    id: int | None = None
    first_name: str = Field(..., max_length=80)
    last_name: str = Field(..., max_length=80)
    mail: str = Field(..., max_length=120)
    rank: str = Field(..., max_length=20)
    service_number: str = Field(..., max_length=50)
    birthdate: date
    gender: str = Field(..., max_length=1)
    unit: str = Field(..., max_length=100)
    para: bool = False
    ops_test: bool = False

class BEMILService(metaclass=Singleton):
    BASE_URL = ApplicationConfig().hr_url
    API_KEY = ApplicationConfig().hr_api_key

    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    def _build_serviceman(self, data: dict) -> ServiceMen:
        # Validate with Pydantic schema first
        schema = ServiceMenSchema(**data)

        # Convert to ServiceMen model
        serviceman_data = schema.model_dump(exclude_none=True)

        if "gender" in serviceman_data and isinstance(serviceman_data["gender"], str):
            try:
                serviceman_data["gender"] = Gender(serviceman_data["gender"])
            except ValueError:
                pass

        if "unit" in data and isinstance(data["unit"], dict):
            if "unit_id" not in serviceman_data:
                serviceman_data["unit_id"] = data["unit"].get("id")

        valid_fields = {
            "id",
            "first_name",
            "last_name",
            "mail",
            "rank",
            "service_number",
            "birthdate",
            "gender",
            "unit_id",
            "para",
            "ops_test",
        }
        filtered_data = {k: v for k, v in serviceman_data.items() if k in valid_fields}

        return ServiceMen(**filtered_data)

    async def get_be_mil_by_id(self, be_mil_serial_number: str) -> ServiceMen | None:
        """Retrieve a specific ServiceMen by its service number."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/servicemen?serial={be_mil_serial_number}",
                    headers={"X-API-Key": self.API_KEY},
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

    async def get_all_be_mil_from_unit(self, unit_name: str) -> list[ServiceMen] | None:
        """
        Retrieves a list of servicemen from a specified military unit by making an asynchronous
        HTTP GET request to an external API.

        :param unit_name: The name of the military unit for which to retrieve servicemen.
        :type unit_name: str
        :return: A list of ServiceMen objects corresponding to the servicemen in the specified unit,
            or None if an error occurs during the API request.
        :rtype: list[ServiceMen] | None
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/servicemen/unit/{unit_name}",
                    headers={"X-API-Key": self.API_KEY},
                )
                response.raise_for_status()  # raises error if status != 200
                resp = response.json()
                return [self._build_serviceman(item) for item in resp]
            except httpx.HTTPStatusError as e:
                self.__logger.error(f"Error fetching BEMILs from unit {unit_name}: {e}")
                return None

    async def sent_hr_message_to_hr(self, message: Message):
        """
        Sends a message to the HR system using an asynchronous HTTP POST request.

        This method utilizes the ``httpx.AsyncClient`` to send a POST request to
        the HR messages endpoint. The message is serialized to JSON before being
        sent, and the response is then returned after ensuring the request completes
        successfully. Logging is performed for the serialized message.

        :param message: The message object to be sent to the HR system. It must
            implement a ``to_dict()`` method to allow JSON serialization.
        :type message: Message
        :return: The JSON response returned by the HR system.
        :rtype: dict
        :raises httpx.HTTPStatusError: If the HTTP request results in an error response.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.BASE_URL + "/hrmessages",
                json=message.to_dict(),
                headers={
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "X-API-Key": self.API_KEY,
                },
            )
            self.__logger.info(json.dumps(message.to_dict(), indent=2))
            response.raise_for_status()
        return response.json()


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
