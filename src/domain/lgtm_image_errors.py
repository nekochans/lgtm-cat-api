# 絶対厳守：編集前に必ずAI実装ルールを読む
class ErrRecordCount(Exception):
    pass


class ErrInvalidImageExtension(Exception):
    pass


class ErrInvalidToken(Exception):
    pass


class ErrJwksFetchFailed(Exception):
    pass


class ErrExpiredToken(Exception):
    pass


class ErrInvalidUrl(Exception):
    pass


class ErrImageFetchFailed(Exception):
    pass


class ErrUrlNotAccessible(Exception):
    pass


class ErrEmbeddingGenerationFailed(Exception):
    pass


class ErrVectorDataCorrupted(Exception):
    pass


class ErrVectorSearchFailed(Exception):
    pass


class ErrInvalidSearchQuery(Exception):
    pass


class ErrRekognitionFailed(Exception):
    pass


class ErrNotModerationImage(Exception):
    pass


class ErrPersonFaceInImage(Exception):
    pass


class ErrNotCatImage(Exception):
    pass
