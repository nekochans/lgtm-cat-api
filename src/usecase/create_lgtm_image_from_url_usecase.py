# 絶対厳守:編集前に必ずAI実装ルールを読む

from datetime import datetime, timezone

from domain.create_lgtm_image import (
    UploadedLgtmImage,
    build_object_prefix,
    create_upload_object_storage_dto,
    create_uploaded_lgtm_image,
    generate_lgtm_image_name,
)
from domain.image_format import mime_type_to_extension
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from log.logger import get_logger
from log.url_sanitizer import sanitize_url_for_logging

logger = get_logger(__name__)


class CreateLgtmImageFromUrlUseCase:
    @staticmethod
    async def execute(
        image_fetch_repository: ImageFetchRepositoryInterface,
        object_storage_repository: ObjectStorageRepositoryInterface,
        base_url: str,
        image_url: str,
    ) -> UploadedLgtmImage:
        # URLをサニタイズ（クエリパラメータやトークンを除去）
        safe_url = sanitize_url_for_logging(image_url)

        logger.info(
            "Executing CreateLgtmImageFromUrlUseCase",
            extra={"image_url": safe_url},
        )

        # 外部URLから画像を取得（MIMEタイプも含む）
        fetched_image = await image_fetch_repository.fetch_image(image_url)

        logger.info(
            f"Successfully fetched image from URL ({len(fetched_image['data'])} bytes, type: {fetched_image['mime_type']})",
            extra={
                "image_url": safe_url,
                "size": len(fetched_image["data"]),
                "mime_type": fetched_image["mime_type"],
            },
        )

        # MIMEタイプから拡張子を取得
        image_extension = mime_type_to_extension(fetched_image["mime_type"])

        # オブジェクトのプレフィックスを生成（現在時刻をUTCで取得）
        now_utc = datetime.now(timezone.utc)
        prefix = build_object_prefix(now_utc)

        # 画像名を生成
        image_name = generate_lgtm_image_name()

        # アップロードパラメータを作成
        upload_param = create_upload_object_storage_dto(
            body=fetched_image["data"],
            prefix=prefix,
            image_name=image_name,
            image_extension=image_extension,
        )

        # アップロード
        await object_storage_repository.upload(upload_param)

        # アップロード済み画像エンティティを作成
        uploaded_image = create_uploaded_lgtm_image(
            domain=base_url, prefix=prefix, image_name=image_name
        )

        logger.info(
            "CreateLgtmImageFromUrlUseCase completed successfully",
            extra={"image_url": uploaded_image["url"]},
        )

        return uploaded_image
