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
