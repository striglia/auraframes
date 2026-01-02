from typing import Any

import boto3
import botocore

SESSION_CONFIG = botocore.config.Config(
    user_agent="aws-sdk-android/2.13.1 Linux/5.4.61-android11 Dalvik/2.1.0/0 en_US"
)


# TODO: Convert this to use os.environ vars?
class AWSClient:
    def __init__(self, pool_id: str, region_name: str = "us-east-1") -> None:
        # boto3.set_stream_logger('', logging.DEBUG)

        self.region_name = region_name
        self.cognito: Any = boto3.client(
            "cognito-identity", region_name=self.region_name
        )
        self.credentials: dict[str, Any] = {}
        if pool_id:
            self.auth(pool_id)

    def auth(self, pool_id: str) -> None:
        ident_resp = self.cognito.get_id(IdentityPoolId=pool_id)
        cred_resp = self.cognito.get_credentials_for_identity(
            IdentityId=ident_resp["IdentityId"]
        )
        self.credentials = cred_resp["Credentials"]
