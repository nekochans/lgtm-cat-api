# 絶対厳守：編集前に必ずAI実装ルールを読む
"""S3オブジェクトを参照した猫画像判定ユースケース"""

from domain.cat_image_validation_policy import (
    DEFAULT_VALIDATION_POLICY,
    CatImageValidationPolicy,
    CatImageValidationResult,
)
from domain.image_analysis_interface import ImageAnalysisServiceInterface
from domain.lgtm_image_errors import (
    ErrNotCatImage,
    ErrNotModerationImage,
    ErrPersonFaceInImage,
)


class ValidateCatImageFromS3UseCase:
    def __init__(
        self,
        image_analysis_service: ImageAnalysisServiceInterface,
        policy: CatImageValidationPolicy = DEFAULT_VALIDATION_POLICY,
    ) -> None:
        self.image_analysis_service = image_analysis_service
        self.policy = policy

    async def execute(self, bucket: str, key: str) -> CatImageValidationResult:
        """
        S3オブジェクトを参照して猫画像のバリデーションを実行する。

        Args:
            bucket: S3バケット名
            key: S3オブジェクトキー

        Returns:
            CatImageValidationResult: バリデーション結果

        Raises:
            ErrRekognitionFailed: Rekognitionサービスの障害時に発生。
                S3オブジェクトが存在しない場合やアクセス権限がない場合も含む。
                インフラ層の障害を示すため意図的にキャッチせず伝播させ、
                Controller層で500エラーに変換される。

        Note:
            バリデーション判定結果（猫未検出、不適切コンテンツ、人の顔検出）は
            例外をキャッチしてis_acceptable=Falseのレスポンスに変換する。
        """
        try:
            await self._validate_moderation(bucket, key)

            await self._validate_no_person_face(bucket, key)

            await self._validate_cat_presence(bucket, key)

            return CatImageValidationResult(is_acceptable=True)

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

    async def _validate_moderation(self, bucket: str, key: str) -> None:
        labels = await self.image_analysis_service.detect_moderation_labels_from_s3(
            bucket, key, self.policy["moderation_min_confidence"]
        )
        if labels:
            raise ErrNotModerationImage("Inappropriate content detected")

    async def _validate_no_person_face(self, bucket: str, key: str) -> None:
        faces = await self.image_analysis_service.detect_faces_from_s3(bucket, key)
        min_confidence: float = self.policy["face_detection_min_confidence"]
        for face in faces:
            confidence = face["confidence"]
            if confidence > min_confidence:
                raise ErrPersonFaceInImage(
                    f"Person face detected with confidence {confidence}"
                )

    async def _validate_cat_presence(self, bucket: str, key: str) -> None:
        labels = await self.image_analysis_service.detect_labels_from_s3(
            bucket,
            key,
            self.policy["labels_max_count"],
            self.policy["labels_min_confidence"],
        )
        min_confidence: float = self.policy["cat_label_min_confidence"]
        for label in labels:
            if label["name"] == "Cat" and label["confidence"] > min_confidence:
                return
        raise ErrNotCatImage("Cat not detected in image")
