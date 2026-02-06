import bcrypt
from fastapi.security import OAuth2PasswordBearer

from warriorfit.services.service_user import UserService

# Configuration constants
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Auth:
    """
    Handles user authentication functionality including password hashing and verification.

    This class provides static methods for user authentication by verifying user
    credentials, hashing passwords, and validating hashed passwords. It interacts
    with a user service to retrieve user data and performs required cryptographic
    operations for secure authentication.

    Static Methods:
        - authenticate_user: Authenticates a user based on username and password.
        - hash_password: Hashes a plain text password using bcrypt.
        - verify_password: Verifies a plain password against a hashed password.
    """

    @staticmethod
    async def authenticate_user(username: str, password: str):
        """
        Authenticates a user by verifying the provided username and password.

        This method retrieves a user from the database using the provided username
        and verifies the authenticity of the provided password by comparing it
        with the stored password hash. If the user does not exist or the password
        does not match, it returns None. Otherwise, it returns the authenticated
        user object.

        :param username: The username of the user attempting to authenticate.
        :param password: The password provided by the user for authentication.
        :return: The authenticated user object if credentials are valid, otherwise None.
        """
        db_service = UserService()
        user = await db_service.get_user_by_username(username)
        if not user:
            return None
        if not Auth.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes a given password using bcrypt algorithm.

        This method takes a plaintext password, encodes it if it is a string, and generates a secure
        hashed password with a salt using bcrypt. The resulting hashed password is then decoded
        to a string format and returned.

        :param password: The plaintext password to be hashed.
        :type password: str
        :return: The hashed password as a string.
        :rtype: str
        """
        if isinstance(password, str):
            password = password.encode()
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies whether a plain text password matches a hashed password using the bcrypt library.
        This method checks for the type of the hashed password and processes its format accordingly
        before verifying it against the plain text password. It supports different representations
        of hashed password such as bytes, bcrypt format string, or hexadecimal format.

        :param plain_password: The plain text password to verify.
        :type plain_password: str
        :param hashed_password: The hashed password to compare with, can be in bytes, bcrypt string,
            or hexadecimal format.
        :type hashed_password: str
        :return: True if the plain password matches the hashed password, False otherwise.
        :rtype: bool
        """
        try:
            if isinstance(hashed_password, bytes):
                hash_bytes = hashed_password
            elif hashed_password.startswith("$2b$"):
                hash_bytes = hashed_password.encode()
            elif all(
                c in "0123456789abcdefABCDEF"
                for c in hashed_password.replace("\\x", "")
            ):
                hash_bytes = bytes.fromhex(hashed_password.replace("\\x", ""))
            else:
                hash_bytes = hashed_password.encode()
            return bcrypt.checkpw(plain_password.encode(), hash_bytes)
        except Exception:
            return False
