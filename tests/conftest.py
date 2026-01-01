"""Shared test fixtures for auraframes tests."""

import pytest

from auraframes.client import Client


@pytest.fixture
def mock_user() -> dict:
    """Sample user response from login API."""
    return {
        "id": "user-123",
        "name": "Test User",
        "email": "test@example.com",
        "auth_token": "test-auth-token-abc123",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "short_id": None,
        "show_push_prompt": False,
        "latest_app_version": None,
        "attribution_id": None,
        "attribution_string": None,
        "test_account": False,
        "avatar_file_name": None,
        "has_frame": True,
        "analytics_optout": False,
        "admin_account": False,
    }


@pytest.fixture
def mock_frame() -> dict:
    """Sample frame response from API."""
    return {
        "id": "frame-456",
        "name": "Living Room",
        "user_id": "user-123",
        "software_version": "1.0.0",
        "build_version": "100",
        "hw_android_version": "11",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "handled_at": "2024-01-01T00:00:00Z",
        "deleted_at": None,
        "updated_at_on_client": None,
        "orientation": 1,
        "auto_brightness": True,
        "min_brightness": 10,
        "max_brightness": 100,
        "brightness": 50,
        "sense_motion": True,
        "default_speed": "normal",
        "slideshow_interval": 15,
        "slideshow_auto": True,
        "digits": 4,
        "contributors": None,
        "contributor_tokens": [],
        "hw_serial": "ABC123",
        "matting_color": "white",
        "trim_color": "black",
        "is_handling": False,
        "calibrations_last_modified_at": "2024-01-01T00:00:00Z",
        "gestures_on": True,
        "portrait_pairing_off": None,
        "live_photos_on": True,
        "auto_processed_playlist_ids": [],
        "time_zone": "America/Los_Angeles",
        "wifi_network": "HomeWifi",
        "cold_boot_at": None,
        "is_charity_water_frame": False,
        "num_assets": 100,
        "thanks_on": True,
        "frame_queue_url": None,
        "client_queue_url": "https://sqs.example.com/queue",
        "scheduled_display_sleep": False,
        "scheduled_display_on_at": None,
        "scheduled_display_off_at": None,
        "forced_wifi_state": None,
        "forced_wifi_recipient_email": None,
        "is_analog_frame": False,
        "control_type": "digital",
        "display_aspect_ratio": "16:10",
        "has_claimable_gift": None,
        "gift_billing_hint": None,
        "locale": "en",
        "frame_type": None,
        "description": None,
        "representative_asset_id": None,
        "sort_mode": None,
        "email_address": "frame@aura.com",
        "features": None,
        "letterbox_style": None,
        "user": {
            "id": "user-123",
            "name": "Test User",
            "email": "test@example.com",
            "auth_token": "token",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "short_id": None,
            "show_push_prompt": False,
            "latest_app_version": None,
            "attribution_id": None,
            "attribution_string": None,
            "test_account": False,
            "avatar_file_name": None,
            "has_frame": True,
            "analytics_optout": False,
            "admin_account": False,
        },
        "playlists": [],
        "delivered_frame_gift": None,
        "last_feed_item": {},
        "last_impression": None,
        "last_impression_at": "2024-01-01T00:00:00Z",
        "child_albums": [],
        "smart_adds": [],
        "recent_assets": [],
    }


@pytest.fixture
def client() -> Client:
    """Fresh HTTP client for testing."""
    return Client()
