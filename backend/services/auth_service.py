from flask_jwt_extended import create_access_token, create_refresh_token

from models import User, db
from services.password_validator import PasswordValidator


class AuthService:
    """Authentication service for user management"""

    @staticmethod
    def register_user(email, password, full_name=None):
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            full_name: Optional full name

        Returns:
            User object

        Raises:
            ValueError: If user already exists
        """
        # Validate password strength
        password_check = PasswordValidator.validate(password)
        if not password_check["valid"]:
            raise ValueError(password_check["errors"][0])

        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create new user
        user = User(email=email, full_name=full_name, credits_remaining=50, credits_max=50)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def login_user(email, password):
        """
        Login user and return tokens.

        Args:
            email: User email
            password: User password

        Returns:
            dict with access_token, refresh_token, and user data

        Raises:
            ValueError: If credentials are invalid
        """
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is disabled")

        # Create tokens (identity must be a string)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_email(email: str):
        """Get user by email"""
        return User.query.filter_by(email=email.lower()).first()
