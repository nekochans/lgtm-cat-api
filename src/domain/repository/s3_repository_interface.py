# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Protocol

from src.domain.create_lgtm_image import UploadS3Param


class S3RepositoryInterface(Protocol):
    async def upload(self, param: UploadS3Param) -> None: ...
