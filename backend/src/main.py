from fastapi import APIRouter, FastAPI

from api.column_profiles.router import router as column_profile_router
from api.data_source.router import router as data_source_router
from api.projects.router import router as project_router
from api.rules.router import router as rule_router


app = FastAPI()

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(data_source_router)
api_v1_router.include_router(project_router)
api_v1_router.include_router(column_profile_router)
api_v1_router.include_router(rule_router)

app.include_router(api_v1_router)
