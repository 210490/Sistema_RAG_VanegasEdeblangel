# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS - Sistema RAG
# Autor: Ing. Edeblangel Vanegas
# ==============================================================================

import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def get_data_dir() -> str:
    """
    Retorna un directorio con permisos de escritura para la base de datos, uploads y ChromaDB.
    Soporta Vercel (AWS Lambda /tmp), Contenedores Docker (/data), y Desarrollo local.
    """
    # 1. Variable explícita de entorno
    custom = os.getenv("DATA_DIR") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if custom:
        try:
            os.makedirs(custom, exist_ok=True)
            return custom
        except Exception:
            pass

    # 2. Vercel o AWS Lambda (solo /tmp es escribible)
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_dir = os.path.join(tempfile.gettempdir(), "rag_data")
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    # 3. En Windows, usar carpeta local 'data' en la raíz del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.name == "nt":
        local_data = os.path.join(base_dir, "data")
        os.makedirs(local_data, exist_ok=True)
        return local_data

    # 4. Entornos contenedores Linux (Docker / Render / Railway): verificar escritura en /data
    if os.path.exists("/data"):
        try:
            test_file = "/data/.writable_test"
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
            return "/data"
        except Exception:
            pass

    try:
        os.makedirs("/data", exist_ok=True)
        test_file = "/data/.writable_test"
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return "/data"
    except Exception:
        pass

    # 5. Fallback a carpeta local del proyecto
    local_data = os.path.join(base_dir, "data")
    try:
        os.makedirs(local_data, exist_ok=True)
        return local_data
    except Exception:
        pass

    # 6. Fallback seguro a temporal del sistema
    fallback = os.path.join(tempfile.gettempdir(), "rag_data")
    os.makedirs(fallback, exist_ok=True)
    return fallback


DATA_DIR = get_data_dir()
DB_PATH = os.path.join(DATA_DIR, "rag_sistema.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models.user import User  # noqa
    Base.metadata.create_all(bind=engine)
    print(f"[INFO] Base de datos inicializada en: {DB_PATH}")
