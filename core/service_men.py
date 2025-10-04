import datetime

from core.Gender import Gender
from core.unit import Unit


class ServiceMen:
    def __init__(self,*, id: int,first_name, last_name: str, rank: str, service_number: str,
                 birthdate: datetime.datetime, gender: Gender, unit: Unit):
        self.id:int = id
        self.first_name:str = first_name
        self.last_name:str = last_name
        self.rank:str = rank
        self.service_number:str = service_number
        self.birthdate:datetime.datetime = birthdate
        self.gender:Gender = gender
        self.unit:Unit = unit


    def age_from_birthdate(self) -> int:
        d = self.birthdate.date()
        today = datetime.date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def age_from_birthdate_and_session_date(self,date_session:datetime.date) -> int:
        today = datetime.date.today()
        return today.year - date_session.year - ((today.month, today.day) < (date_session.month, date_session.day))

    def __repr__(self):
        return (f"<ServiceMen(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, rank={self.rank}, "
                f"service_number={self.service_number}, birthdate={self.birthdate}, gender={self.gender}, unit={self.unit})>")

    def __str__(self):
        return f"{self.rank} {self.first_name} {self.last_name} ({self.service_number}) - Unit: {self.unit}"
