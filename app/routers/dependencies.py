from fastapi import Header, HTTPException, status


def get_store_id(x_store_id: int | None = Header(default=None)) -> int:
    if x_store_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Store-Id header is required.",
        )
    return x_store_id
