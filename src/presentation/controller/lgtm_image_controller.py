# 絶対厳守：編集前に必ずAI実装ルールを読む

from fastapi.responses import JSONResponse

from src.domain.lgtm_image import LgtmImage
from src.domain.lgtm_image_errors import ErrRecordCount
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)
from src.presentation.controller.lgtm_image_response import (
    LgtmImageItem,
    LgtmImageRandomListResponse,
)
from src.usecase.extract_random_lgtm_images_usecase import (
    ExtractRandomLgtmImagesUsecase,
)


class LgtmImageController:
    @staticmethod
    async def exec(
        repository: LgtmImageRepositoryInterface,
        base_url: str,
    ) -> JSONResponse:
        try:
            images: list[LgtmImage] = await ExtractRandomLgtmImagesUsecase.execute(
                repository, base_url
            )
            image_items = [
                LgtmImageItem(id=image["id"], url=image["url"])  # type: ignore[arg-type]
                for image in images
            ]
            response = LgtmImageRandomListResponse(LgtmImages=image_items)
            return JSONResponse(content=response.model_dump(mode="json", by_alias=True))
        except ErrRecordCount:
            return JSONResponse(
                status_code=404,
                content={"error": "Insufficient LGTM images available"},
            )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"Internal server error: {str(e)}"},
            )
