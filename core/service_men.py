import datetime

from core.Gender import Gender
from core.unit import Unit


class ServiceMen:
    def __init__(self,*, id: int=0,first_name:str, last_name: str, mail:str, rank: str, service_number: str,
                 birthdate: datetime.datetime, gender: Gender, unit: Unit, para:bool=False, ops_test:bool=False):
        self.id:int = id
        self.first_name:str = first_name
        self.last_name:str = last_name
        self.mail:str = mail
        self.rank:str = rank
        self.service_number:str = service_number
        self.birthdate:datetime.datetime = birthdate
        self.gender:Gender = gender
        self.unit:Unit = unit
        self.para:bool = para
        self.ops_test:bool = ops_test


    def age_from_birthdate(self) -> int:
        if  isinstance(self.birthdate,str):
            d= datetime.datetime.strptime(self.birthdate, "%Y-%m-%d")
            #d = self.birthdate.date()
        else:
           d = self.birthdate.date()
        today = datetime.date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def age_from_birthdate_and_session_date(self,date_session:datetime.date) -> int:
        today = datetime.date.today()
        return today.year - date_session.year - ((today.month, today.day) < (date_session.month, date_session.day))

    def __str__(self):
        return f"{self.first_name} {self.last_name}  {self.mail}"
    def __repr__(self):
        return f"{self.first_name} {self.last_name}  {self.mail}"