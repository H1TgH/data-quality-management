from functools import wraps

from fastapi import HTTPException, status

from core.rules.exceptions import ProjectOrDataSourceNotFoundException, RuleNotFoundException


def handle_rule_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)

        except (ProjectOrDataSourceNotFoundException, RuleNotFoundException) as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            ) from exc

    return wrapper
