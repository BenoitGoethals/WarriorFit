import datetime

from core.Gender import Gender



class ServiceMen:
    def __init__(self,*, id: int,first_name, last_name: str, rank: str, service_number: str,
                 birthdate: datetime.datetime, gender: Gender, unit: str):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.rank = rank
        self.service_number = service_number
        self.birthdate = birthdate
        self.gender = gender
        self.unit = unit


    def age_from_birthdate(self) -> int:
        d = self.birthdate.date()
        today = datetime.date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def age_from_birthdate_and_session_date(self,date_session:datetime.date) -> int:

        today = datetime.date.today()
        return today.year - date_session.year - ((today.month, today.day) < (date_session.month, date_session.day))

    def __repr__(self):
        return f"ServiceMen(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', " \
               f"rank='{self.rank}', service_number='{self.service_number}', birthdate={self.birthdate}, " \

    def __str__(self):
        return f"{self.rank} {self.first_name} {self.last_name} ({self.service_number}) - Unit: {self.unit}"
