# 絶対厳守:編集前に必ずAI実装ルールを読む

from typing import Protocol, Required, TypedDict


class FetchedImage(TypedDict):
    data: Required[bytes]
    mime_type: Required[str]


class ImageFetchRepositoryInterface(Protocol):
    async def fetch_image(self, url: str) -> FetchedImage: ...
