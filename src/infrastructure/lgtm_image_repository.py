# 絶対厳守：編集前に必ずAI実装ルールを読む

from src.domain.lgtm_image import LgtmImageId
from src.domain.lgtm_image_object import LgtmImageObject
from src.domain.repository.lgtm_image_repository_interface import (
    LgtmImageRepositoryInterface,
)


class LgtmImageRepository(LgtmImageRepositoryInterface):
    """LGTM画像リポジトリの実装.

    現在はモックデータを返す実装.
    将来的にはデータベースやS3などの実装に置き換える.
    """

    # モックデータ（将来的にはDBから取得）
    _MOCK_IMAGES = [
        LgtmImageObject(
            id=LgtmImageId(1),
            path="2021/03/16/23",
            filename="5947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(2),
            path="2021/03/16/23",
            filename="6947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(3),
            path="2021/03/16/23",
            filename="7947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(4),
            path="2021/03/16/23",
            filename="8947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(5),
            path="2021/03/16/23",
            filename="9947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(6),
            path="2021/03/16/23",
            filename="a947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(7),
            path="2021/03/16/23",
            filename="b947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(8),
            path="2021/03/16/23",
            filename="c947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(9),
            path="2021/03/16/23",
            filename="d947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
        LgtmImageObject(
            id=LgtmImageId(10),
            path="2021/03/16/23",
            filename="e947f291-a46e-453c-a230-0d756d7174cb.webp",
        ),
    ]

    async def find_all_ids(self) -> list[LgtmImageId]:
        return [image["id"] for image in self._MOCK_IMAGES]

    async def find_by_ids(self, ids: list[LgtmImageId]) -> list[LgtmImageObject]:
        id_set = set(ids)
        return [image for image in self._MOCK_IMAGES if image["id"] in id_set]
