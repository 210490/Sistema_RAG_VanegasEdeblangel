# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS - Sistema RAG
# Autor: Ing. Edeblangel Vanegas
# ==============================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Adaptado para Vercel Serverless: usar /tmp o local
if os.getenv("ENVIRONMENT") == "production" or os.getenv("VERCEL"):
    DB_DIR = "/tmp"
else:
    DB_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(DB_DIR, "rag_sistema.db")
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
