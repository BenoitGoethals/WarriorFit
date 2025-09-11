import datetime
import random
from typing import Optional

from data.db.db_model import User, TestSession, PhefTest
from core.role import Role
from core.type_fitness_test import TypeFitnessTest
from ui.services.db_service import DBService

# Constants
DEFAULT_ROLE = Role.USER
INVALID_EMAIL_MSG = "Invalid email address"
INVALID_USERNAME_MSG = "Username must be between 3 and 50 characters"

async def main():
    """
    Main function to demonstrate user creation and database operations.
    
    Returns:
        Optional[User]: Created user instance if successful, None otherwise
    """
    try:
        db_service = DBService("../config/config.yml")
      #  await test_user(db_service)

        await test_test_session(db_service)





    except ValueError as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


async def test_test_session(db_service):
    await db_service.delete_all_test_sessions()
    test_session01 = TestSession(
        executed=True,
        description="Test session for user",
        datetime_start=datetime.datetime.now(),
        serial_number_pti=f"SN-{random.Random().randint(1000, 9999)}",
        type_test=TypeFitnessTest.PHEF

    )
    test_session01: TestSession = await db_service.add_test_session(test_session01)
    print(f"Test session created: {test_session01.serial_number_pti}, User ID: {test_session01.description}")
   # [print(s) for s in await db_service.get_all_test_sessions()]

    for i in range(10):
        phef_test = PhefTest(
            serial_number=f"SN-{random.randint(1000, 9999)}",
            passed=True,
            running_time=12.5,  # seconds/minutes as your app expects
            planking_time=2.3  # seconds/minutes as your app expects
        )
        sess = await db_service.add_fitness_test_to_TestSession(test_session01.id, phef_test)
        print(sess)
    for s in await db_service.get_all_fitness_tests_from_test_session(test_session01.id):
        print(s)

    for s in await db_service.get_all_fitness_tests_that_passed_from_year(2025):
        print(s.serial_number)
        print(s.passed)
        print(s.type)


async def test_user(db_service):
    await db_service.delete_all_users()  # Clear existing users for testing
    for i in range(100):
        user = User(
            username="uset" + str(random.Random().randint(5, 1000)),
            password_hash="password" + str(random.Random().randint(5, 1000)),
            email=f"beoit.goethals{str(random.Random().randint(5, 1000))}@fdsf.com",
            role=Role.USER if i % 2 == 0 else Role.ADMIN,
            is_active=True,
            serial_number=f"SN-{random.Random().randint(1000, 9999)}",

        )
        user01 = await db_service.add_user(user)
        print(user01)
    user01 = User(
        username="benoit",
        password_hash="password",
        email="sdsa@sdsa",
        is_active=True,
        serial_number=f"SN-{random.Random().randint(1000, 9999)}"
    )
    user01.role = Role.ADMIN
    await db_service.add_user(user01)
    userret = await db_service.get_user_by_username("benoit")
    if userret:
        print(f"User created: {userret.username}, Email: {userret.email}, Role: {userret.role}")
    else:
        print("User creation failed or user not found.")
    all_users = await db_service.get_all_users()
    for user in all_users:
        print(user.username, user.email, user.role)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


