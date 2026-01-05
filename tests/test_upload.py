"""Tests for image upload flow.

The upload flow is complex (10 steps per README):
1. Select frame and retrieve data
2. Create asset with GUID
3. Call /frames/{id}/select_asset.json
4. Poll SQS
5. Repeat select_asset call
6. Upload to S3 (images.senseapp.co)
7. Populate asset with S3 response
8. Batch update asset via /assets/batch_update.json
9. Poll SQS again

These tests focus on the critical integration points.
"""

import os
from typing import Any

import boto3
from moto import mock_aws
from pytest_httpx import HTTPXMock

from auraframes.api.frameApi import FrameApi
from auraframes.aws.s3client import S3Client, get_md5
from auraframes.client import Client
from auraframes.models.asset import AssetPartialId


class TestAssetModel:
    """Tests for Asset model used in uploads."""

    def test_asset_partial_id_for_upload(self) -> None:
        """AssetPartialId is used to initiate uploads with minimal data."""
        # AssetPartialId is used for upload initiation (not full Asset)
        partial = AssetPartialId(local_identifier="local-uuid-123")
        assert partial.local_identifier == "local-uuid-123"

        # Verify it can be converted to request format
        request_format = partial.to_request_format()
        assert "asset_local_identifier" in request_format
        assert request_format["asset_local_identifier"] == "local-uuid-123"


class TestMd5Hash:
    """Tests for MD5 hash functionality."""

    def test_get_md5_returns_base64_hash(self) -> None:
        """get_md5 should return base64 encoded MD5 hash."""
        data = b"test data for hashing"
        md5_hash = get_md5(data)

        # MD5 hash of "test data for hashing" base64 encoded
        assert isinstance(md5_hash, str)
        assert len(md5_hash) > 0

    def test_get_md5_consistent_for_same_data(self) -> None:
        """get_md5 should return same hash for same data."""
        data = b"consistent data"
        hash1 = get_md5(data)
        hash2 = get_md5(data)
        assert hash1 == hash2

    def test_get_md5_different_for_different_data(self) -> None:
        """get_md5 should return different hashes for different data."""
        hash1 = get_md5(b"data1")
        hash2 = get_md5(b"data2")
        assert hash1 != hash2


@mock_aws
class TestS3Upload:
    """Tests for S3 upload operations using moto."""

    def test_s3_client_uploads_to_correct_bucket(self) -> None:
        """S3Client should upload to images.senseapp.co bucket."""
        # Set up mock AWS credentials
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

        # Create the bucket
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="images.senseapp.co")

        # Create S3Client with mocked credentials
        client = S3Client.__new__(S3Client)
        client.region_name = "us-east-1"
        client.credentials = {
            "AccessKeyId": "testing",
            "SecretKey": "testing",
            "SessionToken": "testing",
        }
        client.s3_client = s3

        # Upload test data
        test_data = b"test image data"
        filename, md5 = client.upload_file(test_data, ".jpg")

        # Verify file was uploaded
        assert filename.endswith(".jpg")
        assert md5 == get_md5(test_data)

        # Verify file exists in bucket
        response = s3.head_object(Bucket="images.senseapp.co", Key=filename)
        assert response["ContentLength"] == len(test_data)

    def test_s3_client_get_file(self) -> None:
        """S3Client.get_file should return file metadata."""
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="images.senseapp.co")
        s3.put_object(Bucket="images.senseapp.co", Key="test.jpg", Body=b"test data")

        client = S3Client.__new__(S3Client)
        client.s3_client = s3

        result = client.get_file("test.jpg")
        assert result["ContentLength"] == 9  # len(b"test data")


class TestUploadFlow:
    """Integration tests for the upload flow components."""

    def test_select_asset_creates_placeholder(
        self, httpx_mock: HTTPXMock, mock_frame: dict[str, Any]
    ) -> None:
        """select_asset should create a placeholder asset on the frame."""
        frame_id = mock_frame["id"]
        httpx_mock.add_response(
            url=f"https://api.pushd.com/v5/frames/{frame_id}/select_asset.json",
            method="POST",
            json={"number_failed": 0},
        )

        client = Client()
        api = FrameApi(client)

        asset_partial = AssetPartialId(local_identifier="upload-local-123")
        result = api.select_asset(frame_id, asset_partial)

        assert result == 0  # No failures

        request = httpx_mock.get_request()
        assert request is not None
        assert request.method == "POST"

    def test_batch_update_sets_asset_metadata(
        self, httpx_mock: HTTPXMock, mock_asset: dict[str, Any]
    ) -> None:
        """batch_update should update asset with S3 file info."""
        from auraframes.api.assetApi import AssetApi
        from auraframes.models.asset import Asset

        httpx_mock.add_response(
            url="https://api.pushd.com/v5/assets/batch_update.json",
            method="PUT",
            json={
                "ids": [mock_asset["id"]],
                "successes": [{"local_identifier": mock_asset["local_identifier"]}],
            },
        )

        client = Client()
        api = AssetApi(client)

        # Simulate asset after S3 upload
        asset = Asset(**mock_asset)
        asset.file_name = "new-s3-filename.jpg"
        asset.md5_hash = "newmd5hash123"

        ids, successes = api.batch_update(asset)

        assert mock_asset["id"] in ids
        assert len(successes) == 1
