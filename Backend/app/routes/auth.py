from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Merchant
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, MerchantResponse
from app.utils.security import hash_password, verify_password, create_access_token, get_current_merchant

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register_merchant(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new merchant with Argon2 hashed password.
    Returns JWT access token.
    """
    existing = db.query(Merchant).filter(Merchant.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Merchant email is already registered"
        )

    hashed_pw = hash_password(payload.password)

    merchant = Merchant(
        name=payload.name,
        email=payload.email,
        password_hash=hashed_pw
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    token = create_access_token({"sub": merchant.id, "email": merchant.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        merchant={"id": merchant.id, "name": merchant.name, "email": merchant.email}
    )


@router.post("/login", response_model=TokenResponse)
def login_merchant(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates merchant credentials using Argon2 and returns JWT access token.
    """
    merchant = db.query(Merchant).filter(Merchant.email == payload.email).first()
    if not merchant or not verify_password(payload.password, merchant.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": merchant.id, "email": merchant.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        merchant={"id": merchant.id, "name": merchant.name, "email": merchant.email}
    )


@router.get("/me", response_model=MerchantResponse)
def get_current_merchant_profile(current_merchant: Merchant = Depends(get_current_merchant)):
    """Returns profile for currently authenticated merchant."""
    return current_merchant
