from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="LGTM Cat API")


class LgtmImageRandomListResponse(BaseModel):
    id: str
    url: str


class LgtmImageRecentlyCreatedListResponse(BaseModel):
    id: str
    url: str


class LgtmImageCreateRequest(BaseModel):
    image: str
    imageExtension: str


class LgtmImageCreateResponse(BaseModel):
    imageUrl: str


@app.get("/lgtm-images", response_model=List[LgtmImageRandomListResponse])
async def extract_random_lgtm_images() -> List[LgtmImageRandomListResponse]:
    return [
        LgtmImageRandomListResponse(
            id="1",
            url="https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
        )
    ]


@app.post("/lgtm-images", response_model=LgtmImageCreateResponse)
async def create_lgtm_image(lgtm_image_create: LgtmImageCreateRequest) -> LgtmImageCreateResponse:
    return LgtmImageCreateResponse(
        imageUrl="https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp"
    )


@app.get(
    "/lgtm-images/recently-created", response_model=LgtmImageRecentlyCreatedListResponse
)
async def extract_recently_created_lgtm_images() -> List[LgtmImageRecentlyCreatedListResponse]:
    return [
        LgtmImageRecentlyCreatedListResponse(
            id="1",
            url="https://lgtm-images.lgtmeow.com/2021/03/16/23/5947f291-a46e-453c-a230-0d756d7174cb.webp",
        )
    ]


def start() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
