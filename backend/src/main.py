from fastapi import APIRouter, FastAPI

from api.column_profiles.router import router as column_profile_router
from api.data_source.router import router as data_source_router


app = FastAPI()

api_v1_router = APIRouter(prefix="/api/v1")
app.include_router(data_source_router)
app.include_router(column_profile_router)

app.include_router(api_v1_router)
