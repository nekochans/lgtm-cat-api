# 絶対厳守：編集前に必ずAI実装ルールを読む

from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException

from config import (
    get_cognito_app_client_id,
    get_cognito_region,
    get_cognito_user_pool_id,
)
from domain.lgtm_image_errors import (
    ErrExpiredToken,
    ErrInvalidToken,
    ErrJwksFetchFailed,
)
from domain.repository.token_verifier_repository_interface import (
    TokenVerifierRepositoryInterface,
)
from infrastructure.cognito_token_verifier_repository import (
    CognitoTokenVerifierRepository,
)


def create_token_verifier_repository(
    region: str = Depends(get_cognito_region),
    user_pool_id: str = Depends(get_cognito_user_pool_id),
    app_client_id: str = Depends(get_cognito_app_client_id),
) -> TokenVerifierRepositoryInterface:
    return CognitoTokenVerifierRepository(region, user_pool_id, app_client_id)


async def verify_token(
    token_verifier: Annotated[
        TokenVerifierRepositoryInterface, Depends(create_token_verifier_repository)
    ],
    authorization: str = Header(..., description="Bearer token"),
) -> dict[str, Any]:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        return await token_verifier.verify(token)
    except ErrJwksFetchFailed as e:
        raise HTTPException(status_code=503, detail=str(e))
    except (ErrInvalidToken, ErrExpiredToken) as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")
