"""
Pydantic v2 Schemas for DecisionDeck API
Handles request validation and response serialization.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict


# ===================== Authentication Schemas =====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===================== Sub-Entity Schemas =====================

class RatingCreate(BaseModel):
    option_id: str
    criterion_id: str
    rating: float = Field(..., ge=1.0, le=10.0, description="Rating must be between 1.0 and 10.0")


class RatingResponse(BaseModel):
    id: str
    option_id: str
    criterion_id: str
    rating: float
    model_config = ConfigDict(from_attributes=True)


class ConstraintCreate(BaseModel):
    name: str = Field(..., min_length=1)
    attribute_key: str = Field(..., min_length=1)
    operator: str = Field(..., pattern="^(<=|>=|<|>|==)$")
    threshold: float


class ConstraintResponse(BaseModel):
    id: str
    decision_id: str
    name: str
    attribute_key: str
    operator: str
    threshold: float
    model_config = ConfigDict(from_attributes=True)


class OptionCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    display_order: int = 0
    attributes: Dict[str, float] = Field(default_factory=dict)


class OptionResponse(BaseModel):
    id: str
    decision_id: str
    name: str
    description: Optional[str] = None
    display_order: int
    attributes: Dict[str, float]
    model_config = ConfigDict(from_attributes=True)


class CriterionCreate(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.0, le=100.0)
    display_order: int = 0


class CriterionResponse(BaseModel):
    id: str
    decision_id: str
    name: str
    weight: float
    display_order: int
    model_config = ConfigDict(from_attributes=True)


# ===================== Decision Schemas =====================

class DecisionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    options: List[OptionCreate] = Field(default_factory=list)
    criteria: List[CriterionCreate] = Field(default_factory=list)
    ratings: List[RatingCreate] = Field(default_factory=list)
    constraints: List[ConstraintCreate] = Field(default_factory=list)


class DecisionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    options: Optional[List[OptionCreate]] = None
    criteria: Optional[List[CriterionCreate]] = None
    ratings: Optional[List[RatingCreate]] = None
    constraints: Optional[List[ConstraintCreate]] = None


class DecisionSummaryResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    options_count: int
    criteria_count: int
    model_config = ConfigDict(from_attributes=True)


class DecisionDetailResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    options: List[OptionResponse]
    criteria: List[CriterionResponse]
    ratings: List[RatingResponse]
    constraints: List[ConstraintResponse]
    model_config = ConfigDict(from_attributes=True)


# ===================== Evaluation / Scoring Schemas =====================

class ConstraintEvaluationSchema(BaseModel):
    constraint_id: str
    constraint_name: str
    satisfied: bool
    reason: str


class OptionScoreSchema(BaseModel):
    option_id: str
    option_name: str
    score: float
    display_score: float
    rank: int
    is_tied: bool
    is_eligible: bool
    failed_constraints: List[str]
    constraint_results: List[ConstraintEvaluationSchema]
    criteria_contributions: Dict[str, float]
    criteria_ratings: Dict[str, float]


class DecisionEvaluationResponse(BaseModel):
    options: List[OptionScoreSchema]
    total_options_evaluated: int
    eligible_count: int
    ineligible_count: int
    weights_total: float
    all_requirements_satisfied: bool
    summary_message: str


class SimulateWeightsRequest(BaseModel):
    # Maps criterion_id -> temporary_weight (float)
    temporary_weights: Dict[str, float]
