from warriorfit.data.model.db_model import Reservation, User
from warriorfit.data.repositories.reservation_repository import ReservationRepository
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.data.repositories.user_repository import UserRepository
from warriorfit.services.service import Service
from warriorfit.services.notify_mail import NotifyMail


def build_email_add_reservation(reservation: Reservation) -> str:
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


def build_email_update_reservation(reservation: Reservation) -> str:
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
    def __init__(
        self,
        reservation_repository: ReservationRepository = None,
        servicemen_repository: ServicemenRepository = None,
        user_repository: UserRepository = None,
        config=None,
        notify_mail=None,
    ):
        super().__init__(user_repository=user_repository, config=config)
        self._repo = (
            reservation_repository
            if reservation_repository is not None
            else ReservationRepository()
        )
        self._repo_service_men = (
            servicemen_repository
            if servicemen_repository is not None
            else ServicemenRepository()
        )
        self.user_repo = (
            user_repository if user_repository is not None else UserRepository()
        )
        self._notify_mail = notify_mail

    async def add_reservation(self, reservation) -> Reservation | None:
        res = await self._repo.add_reservation(reservation)
        if res:
            await self.add_audit_log(
                details=f"Reservation {reservation.id} added", action="add"
            )
            user = await self.user_repo.get_user_by_serial(reservation.serial_number)
            if user:
                notify = (
                    self._notify_mail if self._notify_mail is not None else NotifyMail()
                )
                await notify.send_mail(
                    body=build_email_add_reservation(reservation),
                    subject="Room reservation",
                    to=str(user.email),
                )
        return res

    async def get_reservation_by_id(self, id_r) -> Reservation | None:
        return await self._repo.get_reservation(id_r)

    async def get_all_reservations(self) -> list[Reservation]:
        return await self._repo.get_all_reservation()

    async def delete_reservation(self, id_r) -> bool:
        res = await self._repo.delete_reservation(id_r)
        if res:
            await self.add_audit_log(
                details=f"Reservation {id_r} deleted", action="delete"
            )
        return res

    async def update_reservation(self, reservation) -> Reservation | None:
        res = await self._repo.update_reservation(reservation)
        if res:
            await self.add_audit_log(
                details=f"Reservation {reservation.id} updated", action="update"
            )
        return res

    async def get_rooms(self):
        return await self._repo.get_rooms()

    async def get_all_pti(self) -> list[User]:
        return await self.user_repo.get_all_pti()  # type: ignore[return-value]
