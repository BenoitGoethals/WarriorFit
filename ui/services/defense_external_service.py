import datetime

from core.service_men import ServiceMen
from logic.singleton import Singleton

class DefenseExternalService(metaclass=Singleton):

    service_men_dict = {
    "SN100001": ServiceMen(
        1, "Thomas", "Peeters", "Caporal", "SN100001",
        datetime.datetime(1995, 3, 15), "M", "1er Régiment de Chasseurs à Cheval"
    ),
    "SN100002": ServiceMen(
        2, "Julie", "Dubois", "Lieutenant", "SN100002",
        datetime.datetime(1993, 7, 22), "F", "12e/13e Bataillon de Ligne"
    ),
    "SN100003": ServiceMen(
        3, "Kevin", "Van Damme", "Sergent", "SN100003",
        datetime.datetime(1994, 11, 8), "M", "2/4 Régiment de Chasseurs à Pied"
    ),
    "SN100004": ServiceMen(
        4, "Emma", "Janssens", "Caporal-Chef", "SN100004",
        datetime.datetime(1996, 5, 30), "F", "Bataillon Carabiniers Prince Baudouin - Grenadiers"
    ),
    "SN100005": ServiceMen(
        5, "Lucas", "Maes", "Premier Sergent", "SN100005",
        datetime.datetime(1992, 9, 12), "M", "4e Bataillon de Génie"
    ),
    "SN100006": ServiceMen(
        6, "Sarah", "De Vos", "Adjudant", "SN100006",
        datetime.datetime(1991, 4, 25), "F", "1 Wing Belgique"
    ),
    "SN100007": ServiceMen(
        7, "Nicolas", "Lambert", "Sergent", "SN100007",
        datetime.datetime(1997, 2, 18), "M", "2e Bataillon de Commandos"
    ),
    "SN100008": ServiceMen(
        8, "Laura", "Willems", "Caporal", "SN100008",
        datetime.datetime(1995, 8, 3), "F", "3e Parachutistes"
    ),
    "SN100009": ServiceMen(
        9, "Mathias", "Claes", "Premier Soldat", "SN100009",
        datetime.datetime(1998, 6, 14), "M", "Special Forces Group"
    ),
    "SN100010": ServiceMen(
        10, "Sophie", "Martens", "Lieutenant", "SN100010",
        datetime.datetime(1994, 12, 7), "F", "Brigade Légère"
    ),
    "SN100011": ServiceMen(
        11, "David", "Vermeer", "Caporal-Chef", "SN100011",
        datetime.datetime(1996, 10, 29), "M", "Régiment de Génie"
    ),
    "SN100012": ServiceMen(
        12, "Charlotte", "Wouters", "Sergent", "SN100012",
        datetime.datetime(1993, 1, 20), "F", "Marine Component"
    ),
    "SN100013": ServiceMen(
        13, "Simon", "De Smet", "Premier Caporal", "SN100013",
        datetime.datetime(1997, 7, 11), "M", "Composante Air"
    ),
    "SN100014": ServiceMen(
        14, "Alice", "Verhoeven", "Adjudant", "SN100014",
        datetime.datetime(1992, 3, 8), "F", "Composante Médicale"
    ),
    "SN100015": ServiceMen(
        15, "Maxime", "Leroy", "Sergent-Chef", "SN100015",
        datetime.datetime(1995, 11, 26), "M", "Composante Terre"
    ),
    "SN100016": ServiceMen(
        16, "Eva", "Jacobs", "Caporal", "SN100016",
        datetime.datetime(1994, 5, 17), "F", "ISTAR Battalion"
    ),
    "SN100017": ServiceMen(
        17, "Arthur", "Mertens", "Premier Sergent-Major", "SN100017",
        datetime.datetime(1991, 8, 9), "M", "Bataillon QG"
    ),
    "SN100018": ServiceMen(
        18, "Léa", "Dupont", "Lieutenant", "SN100018",
        datetime.datetime(1996, 4, 2), "F", "Bataillon Logistics"
    ),
    "SN100019": ServiceMen(
        19, "Vincent", "Gerard", "Caporal-Chef", "SN100019",
        datetime.datetime(1998, 9, 23), "M", "Medium Brigade"
    ),
    "SN100020": ServiceMen(
        20, "Marie", "Thijs", "Sergent", "SN100020",
        datetime.datetime(1997, 12, 15), "F", "Bataillon ISTAR"
    )
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

assert DefenseExternalService().get_belgian_unit("BN_CARA_GREN") == "Bataillon Carabiniers Prince Baudouin - Grenadiers"
assert DefenseExternalService().get_serviceman_by_serial("SN100018").last_name == "Dupont"