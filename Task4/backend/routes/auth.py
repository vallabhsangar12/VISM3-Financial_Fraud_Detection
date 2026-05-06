# ============================================================
# Auth Routes — backend/routes/auth.py
# JWT token issuance and validation
# ============================================================

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

try:
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False

# ── Config (in production, load from .env) ─────────────────────────────────────
SECRET_KEY  = "fraud-system-super-secret-key-change-in-production"
ALGORITHM   = "HS256"
TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Mock user store (replace with DB in production) ───────────────────────────
USERS_DB = {
    "admin":    {"username": "admin",    "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", "role": "admin"},
    "analyst":  {"username": "analyst",  "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", "role": "analyst"},
    # hashed_password above = bcrypt("secret")
}

if JOSE_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _verify_password(plain: str, hashed: str) -> bool:
    if not JOSE_AVAILABLE:
        return plain == "secret"   # Fallback for demo
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    if not JOSE_AVAILABLE:
        return "demo-token-no-jose"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/token", summary="Obtain JWT access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate with username/password and receive a JWT bearer token.

    Demo credentials:
    - username: **admin**  | password: **secret**
    - username: **analyst** | password: **secret**
    """
    user = USERS_DB.get(form_data.username)
    if not user or not _verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _create_token(
        {"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_EXPIRE_MINUTES * 60}


async def get_current_user(token: str = Depends(oauth2_scheme if JOSE_AVAILABLE else lambda: "demo")):
    """Dependency: Validate JWT and return the current user dict."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not JOSE_AVAILABLE:
        return {"username": "admin", "role": "admin"}
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    user = USERS_DB.get(username)
    if user is None:
        raise credentials_exc
    return user
