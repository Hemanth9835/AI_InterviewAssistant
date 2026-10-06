from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

try:
    from .auth import create_access_token, get_token_payload, hash_password, verify_password
    from .database import Question, SessionLocal, User, init_db
    from .services import (
        LanguageModelRequestError,
        MissingOpenAIKeyError,
        generate_interview_prompt,
    )
except ImportError:
    from auth import create_access_token, get_token_payload, hash_password, verify_password
    from database import Question, SessionLocal, User, init_db
    from services import LanguageModelRequestError, MissingOpenAIKeyError, generate_interview_prompt

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-interviewassistant-staticsite.onrender.com",
    ],
   allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=False)


class GenerateRequest(BaseModel):
    focus: str = Field(default="", max_length=200)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    role: Literal[
        "data_analyst",
        "data_engineer",
        "data_scientist",
        "machine_learning_engineer",
        "mlops",
        "ai_engineering",
    ] = "data_scientist"


class GenerateResponse(BaseModel):
    prompt: str


class LoginRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str


def get_database_session() -> Session:
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_database_session),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = get_token_payload(credentials)
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid login token.") from exc
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists.")
    return user


@app.on_event("startup")
def create_database_tables() -> None:
    init_db()


@app.get("/")
async def root():
    return {"message": "Interview question API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_database_session)):
    user = db.query(User).filter(User.name == request.name.strip()).first()
    if user is None or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid user name or password.")
    try:
        token = create_access_token(user.id, user.name)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return LoginResponse(access_token=token, name=user.name)


@app.post("/api/auth/register", response_model=LoginResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_database_session)):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="User name cannot be empty.")
    if db.query(User).filter(User.name == name).first() is not None:
        raise HTTPException(status_code=409, detail="That user name is already in use.")

    user = User(name=name, password=hash_password(request.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That user name is already in use.") from exc
    try:
        token = create_access_token(user.id, user.name)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return LoginResponse(access_token=token, name=user.name)


@app.get("/api/auth/me")
def current_user(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_prompt(
    request: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session),
):
    try:
        prompt = await generate_interview_prompt(
            request.focus,
            request.difficulty,
            request.role,
        )
    except MissingOpenAIKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LanguageModelRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    generated_question = Question(
        user_id=user.id,
        question=prompt,
        focus=request.focus.strip(),
        difficulty=request.difficulty,
        role=request.role,
    )
    db.add(generated_question)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="The generated question could not be saved.",
        ) from exc
    return GenerateResponse(prompt=prompt)
