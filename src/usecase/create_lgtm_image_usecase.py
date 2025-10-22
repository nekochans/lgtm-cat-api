# 絶対厳守：編集前に必ずAI実装ルールを読む

import base64
from datetime import datetime, timezone

from src.domain.create_lgtm_image import (
    UploadedLgtmImage,
    build_object_prefix,
    create_upload_object_strage_dto,
    create_uploaded_lgtm_image,
)
from src.domain.repository.object_storage_repository_interface import (
    ObjectStorageRepositoryInterface,
)
from src.domain.repository.unique_id_generator_interface import (
    UniqueIdGeneratorInterface,
)
from src.log.logger import get_logger

logger = get_logger(__name__)


class CreateLgtmImageUsecase:
    @staticmethod
    async def execute(
        object_storage_repository: ObjectStorageRepositoryInterface,
        id_generator: UniqueIdGeneratorInterface,
        base_url: str,
        image: str,
        image_extension: str,
    ) -> UploadedLgtmImage:
        logger.info(
            "Executing CreateLgtmImageUsecase",
            extra={"image_extension": image_extension},
        )

        # base64デコード
        try:
            decoded_image = base64.b64decode(image)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise

        # オブジェクトのプレフィックスを生成（現在時刻をUTCで取得）
        now_utc = datetime.now(timezone.utc)
        prefix = build_object_prefix(now_utc)

        # 画像名を生成
        image_name = id_generator.generate()

        # アップロードパラメータを作成
        upload_param = create_upload_object_strage_dto(
            body=decoded_image,
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
            "CreateLgtmImageUsecase completed successfully",
            extra={"image_url": uploaded_image["url"]},
        )

        return uploaded_image
