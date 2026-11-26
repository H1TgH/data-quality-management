from functools import wraps

from fastapi import HTTPException, status

from core.projects.exceptions import ProjectNotFoundException


def handle_project_exceptions(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ProjectNotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    return wrapped
