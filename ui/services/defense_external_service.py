import datetime

from logic.singleton import Singleton
from core.service_men import ServiceMen
from core.Gender import Gender
import datetime

class DefenseExternalService(metaclass=Singleton):

    service_men_dict = {
        "SN100001": ServiceMen(
            id=1,
            first_name="Thomas",
            last_name="Peeters",
            rank="Caporal",
            service_number="SN100001",
            birthdate=datetime.datetime(1995, 3, 15),
            gender=Gender.MALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100002": ServiceMen(
            id=2,
            first_name="Julie",
            last_name="Dubois",
            rank="Lieutenant",
            service_number="SN100002",
            birthdate=datetime.datetime(1993, 7, 22),
            gender=Gender.FEMALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100003": ServiceMen(
            id=3,
            first_name="Kevin",
            last_name="Van Damme",
            rank="Sergent",
            service_number="SN100003",
            birthdate=datetime.datetime(1994, 11, 8),
            gender=Gender.MALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100004": ServiceMen(
            id=4,
            first_name="Emma",
            last_name="Janssens",
            rank="Caporal-Chef",
            service_number="SN100004",
            birthdate=datetime.datetime(1996, 5, 30),
            gender=Gender.FEMALE,
            unit="Bataillon Carabiniers Prince Baudouin - Grenadiers",
        ),
        "SN100005": ServiceMen(
            id=5,
            first_name="Lucas",
            last_name="Maes",
            rank="Premier Sergent",
            service_number="SN100005",
            birthdate=datetime.datetime(1992, 9, 12),
            gender=Gender.MALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100006": ServiceMen(
            id=6,
            first_name="Sarah",
            last_name="De Vos",
            rank="Adjudant",
            service_number="SN100006",
            birthdate=datetime.datetime(1991, 4, 25),
            gender=Gender.FEMALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100007": ServiceMen(
            id=7,
            first_name="Nicolas",
            last_name="Lambert",
            rank="Sergent",
            service_number="SN100007",
            birthdate=datetime.datetime(1997, 2, 18),
            gender=Gender.MALE,
            unit="1-3 Bn Lanciers",
        ),
        "SN100008": ServiceMen(
            id=8,
            first_name="Laura",
            last_name="Willems",
            rank="Caporal",
            service_number="SN100008",
            birthdate=datetime.datetime(1995, 8, 3),
            gender=Gender.FEMALE,
            unit="3e Parachutistes",
        ),
        "SN100009": ServiceMen(
            id=9,
            first_name="Mathias",
            last_name="Claes",
            rank="Premier Soldat",
            service_number="SN100009",
            birthdate=datetime.datetime(1998, 6, 14),
            gender=Gender.MALE,
            unit="Special Forces Group",
        ),
        "SN100010": ServiceMen(
            id=10,
            first_name="Sophie",
            last_name="Martens",
            rank="Lieutenant",
            service_number="SN100010",
            birthdate=datetime.datetime(1994, 12, 7),
            gender=Gender.FEMALE,
            unit="Brigade Légère",
        ),
        "SN100011": ServiceMen(
            id=11,
            first_name="David",
            last_name="Vermeer",
            rank="Caporal-Chef",
            service_number="SN100011",
            birthdate=datetime.datetime(1996, 10, 29),
            gender=Gender.MALE,
            unit="Régiment de Génie",
        ),
        "SN100012": ServiceMen(
            id=12,
            first_name="Charlotte",
            last_name="Wouters",
            rank="Sergent",
            service_number="SN100012",
            birthdate=datetime.datetime(1993, 1, 20),
            gender=Gender.FEMALE,
            unit="Marine Component",
        ),
        "SN100013": ServiceMen(
            id=13,
            first_name="Simon",
            last_name="De Smet",
            rank="Premier Caporal",
            service_number="SN100013",
            birthdate=datetime.datetime(1997, 7, 11),
            gender=Gender.MALE,
            unit="Composante Air",
        ),
        "SN100014": ServiceMen(
            id=14,
            first_name="Alice",
            last_name="Verhoeven",
            rank="Adjudant",
            service_number="SN100014",
            birthdate=datetime.datetime(1992, 3, 8),
            gender=Gender.FEMALE,
            unit="Composante Médicale",
        ),
        "SN100015": ServiceMen(
            id=15,
            first_name="Maxime",
            last_name="Leroy",
            rank="Sergent-Chef",
            service_number="SN100015",
            birthdate=datetime.datetime(1995, 11, 26),
            gender=Gender.MALE,
            unit="Composante Terre",
        ),
        "SN100016": ServiceMen(
            id=16,
            first_name="Eva",
            last_name="Jacobs",
            rank="Caporal",
            service_number="SN100016",
            birthdate=datetime.datetime(1994, 5, 17),
            gender=Gender.FEMALE,
            unit="ISTAR Battalion",
        ),
        "SN100017": ServiceMen(
            id=17,
            first_name="Arthur",
            last_name="Mertens",
            rank="Premier Sergent-Major",
            service_number="SN100017",
            birthdate=datetime.datetime(1991, 8, 9),
            gender=Gender.MALE,
            unit="Bataillon QG",
        ),
        "SN100018": ServiceMen(
            id=18,
            first_name="Léa",
            last_name="Dupont",
            rank="Lieutenant",
            service_number="SN100018",
            birthdate=datetime.datetime(1996, 4, 2),
            gender=Gender.FEMALE,
            unit="Bataillon Logistics",
        ),
        "SN100019": ServiceMen(
            id=19,
            first_name="Vincent",
            last_name="Gerard",
            rank="Caporal-Chef",
            service_number="SN100019",
            birthdate=datetime.datetime(1998, 9, 23),
            gender=Gender.MALE,
            unit="Medium Brigade",
        ),
        "SN100020": ServiceMen(
            id=20,
            first_name="Marie",
            last_name="Thijs",
            rank="Sergent",
            service_number="SN100020",
            birthdate=datetime.datetime(1997, 12, 15),
            gender=Gender.FEMALE,
            unit="Bataillon ISTAR",
        ),
    }

    belgian_units = {
        "BN_12_13": "Bataillon 12/13 de Ligne",
        "BN_CARA_GREN": "Bataillon Carabiniers Prince Baudouin - Grenadiers",
        "REG_2_4_CHAS": "2/4 Régiment de Chasseurs à Pied",
        "BN_1_3_LANC": "1/3 Bataillon de Lanciers",
        "BN_2_CDO": "2 Bataillon de Commandos",
        "BN_3_PARA": "3 Bataillon de Parachutistes",
        "SFG": "Special Forces Group",
        "GP_6_CIS": "6 Groupe CIS",
        "BN_ISTAR": "Bataillon ISTAR",
        "BN_4_GEN": "4 Bataillon de Génie",
        "BN_ARTI": "Bataillon Artillerie",
        "BN_LOG": "Bataillon Logistique",
        "GP_4_LOG": "4 Groupe Logistique",
        "BN_18_LOG": "18 Bataillon Logistique",
        "WING_1": "1 Wing",
        "WING_2_TAC": "2 Wing Tactical",
        "WING_10_TAC": "10 Wing Tactical",
        "WING_15_TRANS": "15 Wing Transport",
        "WING_HELI": "Wing Heli",
        "MED_COMP": "Composante Médicale",
        "NAV_COMP": "Composante Marine"
    }



    def get_serviceman_by_serial(self, serial_nbr):
        serviceman = self.service_men_dict.get(serial_nbr)
        if serviceman:
            return serviceman
        else:
            raise ValueError(f"Serviceman with serial number {serial_nbr} not found.")

    def get_all_servicemen(self):
        return self.service_men_dict.values()


    def get_belgian_unit(self, unit_code):
        return self.belgian_units.get(unit_code, "Unknown Unit")

    def get_all_belgian_units(self):
        return self.belgian_units.values()

    def get_all_mil_form_unit(self,unit):
        return [x for x in self.service_men_dict.values() if unit == x.unit]

assert DefenseExternalService().get_belgian_unit("BN_CARA_GREN") == "Bataillon Carabiniers Prince Baudouin - Grenadiers"
assert DefenseExternalService().get_serviceman_by_serial("SN100018").last_name == "Dupont"

test_list = DefenseExternalService().get_all_mil_form_unit("1-3 Bn Lanciers")
for x in test_list:
    print(f"{x.last_name} {x.first_name} {x.service_number} - {x.unit}")