from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, validator

from auraframes.models.user import User
from auraframes.utils.dt import parse_aura_dt


class AssetPadding(BaseModel):
    top: float
    right: float
    bottom: float
    left: float


class AssetSetting(BaseModel):
    added_by_id: str
    asset_id: str
    created_at: str
    frame_id: str
    hidden: bool
    id: str
    last_impression_at: str
    reason: str  # TODO: Have only seen "user"
    selected: bool
    updated_at: str
    updated_selected_at: str


class Asset(BaseModel):
    auto_landscape_16_10_rect: str | None
    auto_portrait_4_5_rect: str | None
    burst_id: Any
    burst_selection_types: Any
    colorized_file_name: str | None
    created_at_on_client: str | None
    data_uti: str
    duplicate_of_id: str | None
    duration: float | None
    duration_unclipped: float | None
    exif_orientation: int
    favorite: bool | None
    file_name: str
    glaciered_at: str
    good_resolution: bool
    handled_at: str | None
    hdr: bool | None
    height: int
    horizontal_accuracy: float | None
    id: str
    ios_media_subtypes: int | None
    is_live: bool | None
    is_subscription: bool
    landscape_16_10_url: str | None
    landscape_16_10_url_padding: AssetPadding | None
    landscape_rect: str | None
    landscape_url: str | None
    landscape_url_padding: AssetPadding | None
    live_photo_off: bool | None
    local_identifier: str
    location: (
        list[float] | None
    )  # Lat/Long, seems to default to (-77.8943033, 34.1978216)
    location_name: str | None
    md5_hash: str | None
    minibar_landscape_url: str | None
    minibar_portrait_url: str | None
    minibar_url: str | None
    modified_at: str | None
    orientation: int | None
    original_file_name: str | None
    panorama: bool | None
    portrait_4_5_url: str | None
    portrait_4_5_url_padding: AssetPadding | None
    portrait_rect: str | None
    portrait_url: str | None
    portrait_url_padding: AssetPadding | None
    raw_file_name: str | None
    represents_burst: Any
    rotation_cw: int
    selected: bool
    source_id: str
    taken_at: str
    taken_at_granularity: Any
    taken_at_user_override_at: str | None
    thumbnail_url: str | None
    unglacierable: bool
    upload_priority: int
    uploaded_at: str
    user: User
    user_id: str
    user_landscape_16_10_rect: str | None
    user_landscape_rect: str | None
    user_portrait_4_5_rect: str | None
    user_portrait_rect: str | None
    video_clip_excludes_audio: bool | None
    video_clip_start: Any
    video_clipped_by_user_at: str | None
    video_file_name: str | None
    video_url: str | None
    widget_url: str | None
    width: int

    @property
    def taken_at_dt(self) -> datetime:
        return parse_aura_dt(self.taken_at)

    @property
    def is_local_asset(self) -> bool:
        return self.id is None


class AssetPartialId(BaseModel):
    id: str | None = None
    local_identifier: str | None = None
    user_id: str | None = None

    @validator("id")
    def check_id_or_local_id(
        cls, _id: str | None, values: dict[str, Any]
    ) -> str | None:
        if not values.get("local_identifier") and not _id:
            raise ValueError("Either id or local_identifier is required")
        return _id

    def to_request_format(self) -> dict[str, str | None]:
        # 'user_id': user_id # in the iphone version user_id is not passed in
        if self.id:
            return {"asset_id": self.id}
        else:
            return {"asset_local_identifier": self.local_identifier}
