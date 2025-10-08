from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.service_men import ServiceMen
from core.unit import Unit
from military_api_rest.db_service_service_men import DbServiceServiceMen


class ServiceMenResponse(BaseModel):
    service_number: str
    first_name: str | None = None
    last_name: str | None = None
    mail: str | None = None
    rank: str | None = None
    unit: str | None = None
    birthdate: str | None = None
    gender: str | None = None
    para: bool = False
    ops_test: bool = False


class UnitResponse(BaseModel):
    name: str
    base_location: str




class ServiceMenApi:
    def __init__(self):
        self.db_service = DbServiceServiceMen()
        self.app = FastAPI(
            title="Service Men API",
            description="API for querying service men by service number",
            version="1.0.0",
            docs_url="/swagger",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )
        self._add_routes()

    def _add_routes(self):
        @self.app.get("/service-men/{service_number}", response_model=ServiceMenResponse)
        async def get_service_man(service_number: str):
            data: List[ServiceMen] = await self.db_service.get_service_men_by_service_number(service_number)
            if not data:
                raise HTTPException(status_code=404, detail="Service member not found")
            return ServiceMenResponse(
                service_number=data[0].service_number,
                first_name=data[0].first_name,
                last_name=data[0].last_name,
                mail=data[0].mail,
                rank=data[0].rank,
                unit=data[0].unit.name,
                birthdate=str(data[0].birthdate),
                gender=data[0].gender.value,
                para=data[0].para,
                ops_test=data[0].ops_test,
            )
        @self.app.get("/service-men/unit/{unit_name}", response_model=List[ServiceMenResponse])
        async def get_all_service_men_from_unit(unit_name:str):
            data: List[ServiceMen] = await self.db_service.all_service_men_from_a_unit(unit_name)
            if not data:
                raise HTTPException(status_code=404, detail="Service member not found")
            return [ServiceMenResponse(
                service_number=member.service_number,
                first_name=member.first_name,
                last_name=member.last_name,
                mail=member.mail,
                rank=member.rank,
                unit=member.unit.name,
                birthdate=str(member.birthdate),
                gender=member.gender.value,
                para=member.para,
                ops_test=member.ops_test,
            ) for member in data]

        @self.app.get("/units", response_model=List[UnitResponse])
        async def get_all_units():
            data: List[Unit] = await self.db_service.get_all_units()
            if not data:
                raise HTTPException(status_code=404, detail="Service member not found")
            else:
                data_response: List[UnitResponse] = []
                for unit in data:
                    data_response.append(UnitResponse(name=unit.name, base_location=unit.base_location))
                return data_response



# Create an instance of the API
api = ServiceMenApi()
# Export the FastAPI application instance
app = api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")


