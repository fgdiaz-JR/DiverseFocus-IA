"""
API Gateway for DiverseFocus-IA.

Handles authentication, rate limiting, and proxying to internal microservices.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    jwt_secret: str = "change_this_to_a_random_256_bit_secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    ai_inference_url: str = "http://ai-inference:8001"
    voice_video_url: str = "http://voice-video:8002"
    user_profile_url: str = "http://user-profile:8003"

    class Config:
        env_file = ".env"


settings = Settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="DiverseFocus-IA API Gateway",
    description="API Gateway with JWT auth and service proxying for DiverseFocus-IA",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory demo user store (replace with DB lookup in production)
# ---------------------------------------------------------------------------
DEMO_USERS: dict[str, dict[str, Any]] = {
    "demo": {
        "user_id": "user-001",
        "username": "demo",
        "hashed_password": pwd_context.hash("demo1234"),
    }
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    return decode_access_token(credentials.credentials)


# ---------------------------------------------------------------------------
# Proxy helper
# ---------------------------------------------------------------------------

async def proxy_request(
    target_url: str,
    request: Request,
    current_user: dict[str, Any],
) -> JSONResponse:
    """Forward an incoming request to an internal service and return its response."""
    body = await request.body()
    headers = {
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "X-User-Id": current_user.get("sub", ""),
        "X-Username": current_user.get("username", ""),
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers=headers,
                params=dict(request.query_params),
            )
        return JSONResponse(
            content=response.json() if response.content else {},
            status_code=response.status_code,
        )
    except httpx.ConnectError as exc:
        logger.error("Service unreachable: %s – %s", target_url, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Upstream service unavailable: {target_url}",
        ) from exc
    except httpx.TimeoutException as exc:
        logger.error("Timeout reaching: %s – %s", target_url, exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Upstream service timed out",
        ) from exc


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "api-gateway"}


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Auth"])
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    user = DEMO_USERS.get(body.username)
    if not user or not pwd_context.verify(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(
        {"sub": user["user_id"], "username": user["username"]}
    )
    return TokenResponse(access_token=token)


@app.post("/api/v1/ai/simplify", tags=["AI"])
@limiter.limit("30/minute")
async def simplify_text(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    target = f"{settings.ai_inference_url}/simplify"
    return await proxy_request(target, request, current_user)


@app.post("/api/v1/ai/transcribe", tags=["AI"])
@limiter.limit("10/minute")
async def transcribe_audio(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    target = f"{settings.voice_video_url}/transcribe"
    return await proxy_request(target, request, current_user)


@app.get("/api/v1/user/profile", tags=["User"])
@limiter.limit("60/minute")
async def get_profile(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    user_id = current_user.get("sub", "")
    target = f"{settings.user_profile_url}/profile/{user_id}"
    return await proxy_request(target, request, current_user)


@app.put("/api/v1/user/profile", tags=["User"])
@limiter.limit("30/minute")
async def update_profile(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    user_id = current_user.get("sub", "")
    target = f"{settings.user_profile_url}/profile/{user_id}"
    return await proxy_request(target, request, current_user)


@app.post("/api/v1/user/tasks", tags=["User"])
@limiter.limit("60/minute")
async def create_task(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    target = f"{settings.user_profile_url}/tasks"
    return await proxy_request(target, request, current_user)


@app.get("/api/v1/user/tasks", tags=["User"])
@limiter.limit("60/minute")
async def get_tasks(
    request: Request,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> JSONResponse:
    user_id = current_user.get("sub", "")
    target = f"{settings.user_profile_url}/tasks/{user_id}"
    return await proxy_request(target, request, current_user)
