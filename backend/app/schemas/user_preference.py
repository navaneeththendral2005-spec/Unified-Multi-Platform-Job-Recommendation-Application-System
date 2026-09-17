from pydantic import BaseModel


class UserPreferenceCreate(BaseModel):

    preferred_roles: list[str]

    preferred_locations: list[str]

    willing_to_relocate: bool

    experience_level: str