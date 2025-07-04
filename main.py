from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse 
from fastapi.templating import Jinja2Templates
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from app.db.database import Base, engine, check_tables_exist
from app.security import auth
from app.security.limiter import create_limiter
from app.users import routes as users
from app.admin import routes as admin
import uvicorn
import logging
import os
import asyncio


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    logger.info("Inicializando aplicación...")
    await initialize_database()
    yield
    logger.info("Cerrando aplicación...")


app = FastAPI(lifespan=lifespan)


create_limiter(app)

app.include_router(auth.router, tags=["Auth"])
app.include_router(users.router, tags=["Users"])
app.include_router(admin.router, tags=["Admin"])


templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static/", StaticFiles(directory="frontend/static/"), name="static")


security_schemes = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Mi API",
        version="1.0",
        description="Autenticación JWT con OTP",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = security_schemes
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


async def initialize_database():
    """Inicialización asíncrona de la base de datos"""
    try:
        if not await asyncio.to_thread(check_tables_exist):
            logger.info("Creando tablas...")
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            logger.info("Tablas creadas exitosamente")
        else:
            logger.info("Las tablas ya existen en la base de datos")
    except Exception as e:
        logger.error(f"Error crítico durante la inicialización: {str(e)}")
        raise RuntimeError("Error en inicialización de base de datos")



@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home/index.html", {"request": request})



@app.get("/favicon.ico/")
async def get_favicon():
    return FileResponse("frontend/static/favicon.ico")
    

if __name__ == "__main__":    
    host = os.environ.get("HOST", "127.0.0.1") 
    port = int(os.environ.get("PORT", 8010))
    reload = os.environ.get("ENV") == "development" 
        
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        workers=int(os.environ.get("WORKERS", 1))
    )       