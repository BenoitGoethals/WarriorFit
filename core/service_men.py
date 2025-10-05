import datetime

from core.Gender import Gender
from core.unit import Unit


class ServiceMen:
    def __init__(self,*, id: int=0,first_name, last_name: str, rank: str, service_number: str,
                 birthdate: datetime.datetime, gender: Gender, unit: Unit, para:bool=False, ops_test:bool=False):
        self.id:int = id
        self.first_name:str = first_name
        self.last_name:str = last_name
        self.rank:str = rank
        self.service_number:str = service_number
        self.birthdate:datetime.datetime = birthdate
        self.gender:Gender = gender
        self.unit:Unit = unit
        self.para:bool = para
        self.ops_test:bool = ops_test


    def age_from_birthdate(self) -> int:
        d = self.birthdate.date()
        today = datetime.date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def age_from_birthdate_and_session_date(self,date_session:datetime.date) -> int:
        today = datetime.date.today()
        return today.year - date_session.year - ((today.month, today.day) < (date_session.month, date_session.day))

    def __repr__(self):
        return f"ServiceMen(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', rank='{self.rank}', service_number='{self.service_number}', birthdate='{self.birthdate}', gender='{self.gender}', unit='{self.unit}', para='{self.para}', ops_test='{self.ops_test}')"
    def __str__(self):
        return f"{self.rank} {self.first_name} {self.last_name} ({self.service_number}) - Unit: {self.unit} -Para {self.para} -Para Test {self.ops_test} -Ops Test {self.ops_test} "