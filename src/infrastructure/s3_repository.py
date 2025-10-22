# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Any

import aioboto3

from src.domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from src.domain.create_lgtm_image import UploadObjectStorageDto
from src.log.logger import get_logger

logger = get_logger(__name__)


class S3Repository(ObjectStorageRepositoryInterface):
    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name
        self.session = aioboto3.Session()

    async def upload(self, param: UploadObjectStorageDto) -> None:
        try:
            async with self.session.client("s3") as s3_client:
                extra_args: dict[str, Any] = {
                    "ContentType": self._get_content_type(param["image_extension"])
                }

                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=param["key"],
                    Body=param["body"],
                    **extra_args,
                )

                logger.info(
                    f"Successfully uploaded to S3: bucket={self.bucket_name}, key={param['key']}"
                )
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise

    def _get_content_type(self, extension: str) -> str:
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return content_types.get(extension, "application/octet-stream")
