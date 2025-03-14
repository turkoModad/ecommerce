import uvicorn
from fastapi import FastAPI
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from app.db.database import Base, engine, check_tables_exist
from app.security import auth


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

app.include_router(auth.router, prefix="/auth", tags=["auth"])


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
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)       