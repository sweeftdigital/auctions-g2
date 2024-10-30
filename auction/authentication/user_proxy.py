class UserProxy:
    USER_TYPE_BUYER = "Buyer"
    USER_TYPE_SELLER = "Seller"
    PROFILE_TYPE_INDIVIDUAL = "Individual"
    PROFILE_TYPE_COMPANY = "Company"

    def __init__(self, payload: dict):
        self.payload = payload
        self.id = payload.get("user_id", "")
        self.is_authenticated = True
        self.token_type = payload.get("token_type", "")
        self.exp = payload.get("exp")
        self.iat = payload.get("iat")
        self.jti = payload.get("jti")
        self.is_verified = payload.get("is_verified", False)
        self._user_type = payload.get("user_type", "")
        self._user_profile_type = payload.get("user_profile_type", "")
        self.country = payload.get("country")
        self.email = payload.get("email")
        self.phone_number = payload.get("phone_number")
        self.two_factor_authentication_activated = payload.get(
            "two_factor_authentication_activated", False
        )
        self.is_social_account = payload.get("is_social_account", False)
        self.first_name = payload.get("first_name", "")
        self.last_name = payload.get("last_name", "")
        self.theme = payload.get("theme", "")
        self.language = payload.get("language", "")
        self.avatar = payload.get("avatar", None)
        self.nickname = payload.get("nickname", None)

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_buyer(self) -> bool:
        """Check if the user is a buyer."""
        return self._user_type == self.USER_TYPE_BUYER

    @property
    def is_seller(self) -> bool:
        """Check if the user is a seller."""
        return self._user_type == self.USER_TYPE_SELLER

    def is_individual(self) -> bool:
        """Check if the user has an individual profile."""
        return self._user_profile_type == self.PROFILE_TYPE_INDIVIDUAL

    def is_company(self) -> bool:
        """Check if the user has a company profile."""
        return self._user_profile_type == self.PROFILE_TYPE_COMPANY

    def has_verified_account(self) -> bool:
        """Check if the user account is verified."""
        return self.is_verified

    def requires_two_factor_auth(self) -> bool:
        """Check if the user has two-factor authentication enabled."""
        return self.two_factor_authentication_activated

    def get_contact_info(self) -> dict:
        """Return a dictionary containing the user's contact information."""
        return {"email": self.email, "phone_number": self.phone_number}

    def has_email(self) -> bool:
        """Check if the user has an email address."""
        return bool(self.email)

    def has_phone_number(self) -> bool:
        """Check if the user has a phone number."""
        return bool(self.phone_number)

    def get_settings(self) -> dict:
        """Return a dictionary containing the user's settings."""
        return {"theme": self.theme, "language": self.language}

    @property
    def is_anonymous(self):
        """Return False because this is a proxy for authenticated users."""
        return False

    def __str__(self) -> str:
        return (
            f"UserProxy (ID: {self.id}, Email: {self.email}, "
            f"Type: {self._user_type}, Profile: {self._user_profile_type}, "
            f"Verified: {self.is_verified})"
        )

    def __repr__(self) -> str:
        return (
            f"<UserProxy id={self.id} email={self.email} type={self._user_type} "
            f"profile={self._user_profile_type} verified={self.is_verified}>"
        )
