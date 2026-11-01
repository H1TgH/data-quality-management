from fastapi import APIRouter, FastAPI

from api.data_source.router import data_source_router


app = FastAPI()

api_v1_router = APIRouter(prefix="/api/v1")
app.include_router(data_source_router)

app.include_router(api_v1_router)
