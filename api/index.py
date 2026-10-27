# ==============================================================================
# API FASTAPI SERVERLESS - Sistema RAG
# Autor: Ing. Edeblangel Vanegas
# ==============================================================================

import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError

from core.database import get_db, init_db
from core.auth import get_password_hash, verify_password, create_access_token, decode_access_token
from models.user import User
from core.rag_core import RAGCore

app = FastAPI(title="Sistema RAG - Ing. Edeblangel Vanegas", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar DB
try:
    init_db()
except Exception as e:
    print(f"Error init_db: {e}")

# RAG Core singleton
rag_core = None
try:
    rag_core = RAGCore()
except Exception as e:
    print(f"Error init RAGCore: {e}")
    rag_core = None

# Static y templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


class RegisterModel(BaseModel):
    nombre: str
    apellidos: str
    cedula: str
    email: str
    telefono: Optional[str] = None
    password: str
    categoria: Optional[str] = "Usuario Estándar"


class LoginModel(BaseModel):
    email: str
    password: str


class QueryModel(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/api/auth/register")
async def register(user: RegisterModel, db: Session = Depends(get_db)):
    db_user = db.query(User).filter((User.email == user.email) | (User.cedula == user.cedula)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Usuario ya existe con ese email o cédula")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        nombre=user.nombre,
        apellidos=user.apellidos,
        cedula=user.cedula,
        email=user.email,
        telefono=user.telefono,
        password_hash=hashed_password,
        categoria=user.categoria,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Usuario registrado exitosamente", "user_id": new_user.id}


@app.post("/api/auth/login")
async def login(user: LoginModel, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    access_token = create_access_token(data={"sub": db_user.email, "categoria": db_user.categoria})
    return {"access_token": access_token, "token_type": "bearer", "categoria": db_user.categoria}


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autorizado")
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


@app.post("/api/admin/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    if current_user.categoria != "Administrador":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cargar documentos")
    if not rag_core:
        raise HTTPException(status_code=500, detail="RAG Core no inicializado (verificar GEMINI_API_KEY)")
    
    upload_dir = os.path.join(BASE_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_paths = []
    for file in files:
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail=f"Formato no soportado: {file.filename}")
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_paths.append(file_path)
    
    try:
        docs = rag_core.load_documents(file_paths)
        num_chunks = rag_core.build_vectorstore(docs)
        return {"message": f"Documentos cargados exitosamente. {len(docs)} documentos, {num_chunks} chunks procesados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar documentos: {str(e)}")


@app.post("/api/chat/query")
async def chat_query(query: QueryModel, current_user: User = Depends(get_current_user)):
    if not rag_core:
        raise HTTPException(status_code=500, detail="RAG Core no inicializado (verificar GEMINI_API_KEY)")
    try:
        result = rag_core.query(query.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en consulta: {str(e)}")


# Para Vercel
handler = app
