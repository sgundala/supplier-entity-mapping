from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from supplier_entity_mapping.api.routes import router
from supplier_entity_mapping.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    allowed_origins = [
        origin.strip()
        for origin in settings.frontend_origins.split(",")
        if origin.strip()
    ]
    app = FastAPI(title="Supplier RAG API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    dist_dir = settings.frontend_dist_dir
    assets_dir = dist_dir / "assets"
    if dist_dir.exists():
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        index_file = dist_dir / "index.html"

        @app.get("/", include_in_schema=False)
        def serve_index() -> FileResponse:
            return FileResponse(index_file)

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_frontend(full_path: str) -> FileResponse:
            candidate = dist_dir / full_path
            if full_path and candidate.exists() and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)

    return app
