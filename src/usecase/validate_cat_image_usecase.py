# 絶対厳守：編集前に必ずAI実装ルールを読む
"""猫画像判定ユースケース"""

from domain.image_analysis_interface import ImageAnalysisServiceInterface
from domain.repository.image_fetch_repository_interface import (
    ImageFetchRepositoryInterface,
)
from domain.lgtm_image_errors import (
    ErrInvalidUrl,
    ErrUrlNotAccessible,
    ErrImageFetchFailed,
    ErrNotModerationImage,
    ErrPersonFaceInImage,
    ErrNotCatImage,
)
from domain.cat_image_validation_policy import (
    CatImageValidationPolicy,
    CatImageValidationResult,
    DEFAULT_VALIDATION_POLICY,
)


class ValidateCatImageUseCase:
    def __init__(
        self,
        image_analysis_service: ImageAnalysisServiceInterface,
        image_fetch_repository: ImageFetchRepositoryInterface,
        policy: CatImageValidationPolicy = DEFAULT_VALIDATION_POLICY,
    ) -> None:
        self.image_analysis_service = image_analysis_service
        self.image_fetch_repository = image_fetch_repository
        self.policy = policy

    async def execute(self, image_url: str) -> CatImageValidationResult:
        """
        猫画像のバリデーションを実行する。

        Args:
            image_url: 検証対象の画像URL

        Returns:
            CatImageValidationResult: バリデーション結果

        Raises:
            ErrRekognitionFailed: Rekognitionサービスの障害時に発生。
                インフラ層の障害を示すため意図的にキャッチせず伝播させ、
                Controller層で500エラーに変換される。

        Note:
            画像取得エラーやバリデーション失敗（クライアント起因）は
            例外をキャッチしてis_acceptable=Falseのレスポンスに変換する。
        """
        try:
            fetched_image = await self.image_fetch_repository.fetch_image(image_url)
            image_bytes = fetched_image["data"]

            await self._validate_moderation(image_bytes)

            await self._validate_no_person_face(image_bytes)

            await self._validate_cat_presence(image_bytes)

            return CatImageValidationResult(is_acceptable=True)

        except (ErrInvalidUrl, ErrUrlNotAccessible, ErrImageFetchFailed):
            return CatImageValidationResult(
                is_acceptable=False, reason="image fetch failed"
            )
        except ErrNotModerationImage:
            return CatImageValidationResult(
                is_acceptable=False, reason="not moderation image"
            )
        except ErrPersonFaceInImage:
            return CatImageValidationResult(
                is_acceptable=False, reason="person face in the image"
            )
        except ErrNotCatImage:
            return CatImageValidationResult(is_acceptable=False, reason="not cat image")

    async def _validate_moderation(self, image_bytes: bytes) -> None:
        labels = await self.image_analysis_service.detect_moderation_labels(
            image_bytes, self.policy["moderation_min_confidence"]
        )
        if labels:
            raise ErrNotModerationImage("Inappropriate content detected")

    async def _validate_no_person_face(self, image_bytes: bytes) -> None:
        faces = await self.image_analysis_service.detect_faces(image_bytes)
        min_confidence: float = self.policy["face_detection_min_confidence"]
        for face in faces:
            confidence = face["confidence"]
            if confidence > min_confidence:
                raise ErrPersonFaceInImage(
                    f"Person face detected with confidence {confidence}"
                )

    async def _validate_cat_presence(self, image_bytes: bytes) -> None:
        labels = await self.image_analysis_service.detect_labels(
            image_bytes,
            self.policy["labels_max_count"],
            self.policy["labels_min_confidence"],
        )
        min_confidence: float = self.policy["cat_label_min_confidence"]
        for label in labels:
            if label["name"] == "Cat" and label["confidence"] > min_confidence:
                return
        raise ErrNotCatImage("Cat not detected in image")
