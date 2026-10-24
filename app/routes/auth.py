"""
Authentication API Routes for DecisionDeck
Handles registration, login, logout, and current user profile verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account with an email address and salted bcrypt password hash.
    Rejects duplicate registrations.
    """
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Hash the password securely
    hashed = hash_password(user_in.password)

    # Create user in database
    new_user = User(
        email=user_in.email,
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue JWT token
    access_token = create_access_token(data={"sub": new_user.id, "email": new_user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user by email and password, returning a signed JWT access token.
    Generic error prevents leaking whether the email or password was wrong.
    """
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(data={"sub": user.id, "email": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
def logout():
    """
    Logs out the user. The frontend clears the stored token.
    """
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile details.
    """
    return UserResponse.model_validate(current_user)
