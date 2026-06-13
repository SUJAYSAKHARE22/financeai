import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.database import db
from services.auth import hash_password, verify_password

router = APIRouter()
security = HTTPBearer()

class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

@router.post("/register", summary="Register a new user")
def register(data: AuthRequest):
    existing = db.get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed = hash_password(data.password)
    user = db.create_user(data.username, hashed)
    
    # Initialize taxpayer profile for the new user automatically
    db.get_taxpayer_profile(user["id"])
    
    return {"message": "User registered successfully", "username": user["username"]}

@router.post("/login", summary="Login and get session token")
def login(data: AuthRequest):
    user = db.get_user_by_username(data.username)
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=1)
    db.create_session(user["id"], token, expires_at)
    
    return {
        "token": token,
        "username": user["username"],
        "user_id": user["id"]
    }

@router.post("/logout", summary="Logout and invalidate token")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    db.delete_session(token)
    return {"message": "Logged out successfully"}
