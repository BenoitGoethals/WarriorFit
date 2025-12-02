from warriorfit.data.model.db_model import Reservation
from warriorfit.data.repositories.reservation_repository import ReservationRepository
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository

from warriorfit.services.service import Service
from warriorfit.ui.pages.notify_mail import NotifyMail


def build_email_add_reservation(reservation:Reservation)->str:
    html = f"""
    <html>
    <body>
        <h2>New Fitness Room Reservation</h2>
        <p>A new reservation has been created with the following details:</p>
        <ul>
            <li>Reservation ID: {reservation.id}</li>
            <li>Date: {reservation.date}</li>
            <li>Start Time: {reservation.start_time}</li>
            <li>End Time: {reservation.end_time}</li>
            <li>User: {reservation.serial_number}</li>
        </ul>
    </body>
    </html>
    """
    return html


def build_email_update_reservation(reservation:Reservation)->str:
    html = f"""
    <html>
    <body>
        <h2>Updated Fitness Room Reservation</h2>
        <p>A reservation has been modified with the following details:</p>
        <ul>
            <li>Reservation ID: {reservation.id}</li>
            <li>Date: {reservation.date}</li>
            <li>Start Time: {reservation.start_time}</li>
            <li>End Time: {reservation.end_time}</li>
            <li>User: {reservation.serial_number}</li>
        </ul>
    </body>
    </html>
    """
    return html


class ReserveFitnessRoomService(Service):

    def __init__(self):
        super().__init__()
        self._repo=ReservationRepository()
        self._repo_service_men=ServicemenRepository()


    async def add_reservation(self, reservation)-> Reservation | None:
        res= await self._repo.add_reservation(reservation)
        if res:
            await self.add_audit_log(details=f"Reservation {reservation.id} added", action="add")
            military= await self._repo_service_men.get_by_service_number(reservation.serial_number)
            if military:
                await NotifyMail().send_mail(
                    body=build_email_add_reservation(reservation), subject="Result Test", to=str(military.mail))

        return res

    async def get_reservation_by_id(self, id_r)->Reservation|None:
        return await self._repo.get_reservation(id_r)

    async def get_all_reservations(self)->list[Reservation]:
        return await self._repo.get_all_reservation()

    async def delete_reservation(self, id_r)->bool:
        res= await self._repo.delete_reservation(id_r)
        if res:
            await self.add_audit_log(details=f"Reservation {id_r} deleted", action="delete")
        return res

    async def update_reservation(self,reservation)->Reservation|None:
        res = await self._repo.update_reservation(reservation)
        if res:
            await self.add_audit_log(details=f"Reservation {reservation.id} updated", action="update")
        return res