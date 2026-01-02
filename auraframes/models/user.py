from pydantic import BaseModel


class User(BaseModel):
    id: str
    created_at: str
    updated_at: str
    name: str
    email: str
    short_id: str | None
    show_push_prompt: bool
    latest_app_version: str | None
    attribution_id: str | None
    attribution_string: str | None
    test_account: bool | None
    avatar_file_name: str | None
    has_frame: bool | None
    analytics_optout: bool = None
    admin_account: bool | None = False
    auth_token: str = None
