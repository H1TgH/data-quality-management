from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth.router import router as auth_router
from api.column_profiles.router import router as column_profile_router
from api.data_source.router import router as data_source_router
from api.projects.router import router as project_router
from api.rules.router import router as rule_router
from api.runs.router import router as run_souter


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(data_source_router)
api_v1_router.include_router(project_router)
api_v1_router.include_router(column_profile_router)
api_v1_router.include_router(rule_router)
api_v1_router.include_router(run_souter)

app.include_router(api_v1_router)
