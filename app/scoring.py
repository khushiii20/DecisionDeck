"""
DecisionDeck Scoring Engine
Pure, functional, thoroughly tested calculation engine for weighted decision analysis
and hard constraint satisfaction.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import math

# Floating-point tolerance for checking that weights sum to 100%
WEIGHT_SUM_TOLERANCE = 1e-4

# Constraint operators supported
SUPPORTED_OPERATORS = {">=", "<=", ">", "<", "=="}

class ScoringValidationError(Exception):
    """Raised when criteria, alternatives, weights, or ratings fail validation."""
    pass


@dataclass
class CriterionInput:
    id: str
    name: str
    weight: float  # Percentage (e.g. 40.0 for 40%)


@dataclass
class OptionInput:
    id: str
    name: str
    description: Optional[str] = None
    # Attribute values used for hard constraints, e.g. {"price": 1200, "battery_hours": 14}
    attributes: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConstraintInput:
    id: str
    name: str
    attribute_key: str  # Which option attribute to evaluate (e.g. 'price')
    operator: str       # '<=', '>=', '<', '>', '=='
    threshold: float    # Required numeric value (e.g. 1500)


@dataclass
class ConstraintEvaluationResult:
    constraint_id: str
    constraint_name: str
    satisfied: bool
    reason: str


@dataclass
class OptionScoringResult:
    option_id: str
    option_name: str
    score: float                         # Calculated weighted score
    display_score: float                 # Rounded for UI display (2 decimal places)
    rank: int                            # 1-based rank (with deterministic tie handling)
    is_tied: bool                        # True if another option has an identical score
    is_eligible: bool                    # True if all hard requirements are met
    failed_constraints: List[str]        # List of explanation strings for failed requirements
    constraint_results: List[ConstraintEvaluationResult]
    criteria_contributions: Dict[str, float]  # Weighted points per criterion: (weight * rating) / 100
    criteria_ratings: Dict[str, float]        # Raw 1-10 rating provided


@dataclass
class DecisionEvaluationOutput:
    options: List[OptionScoringResult]
    total_options_evaluated: int
    eligible_count: int
    ineligible_count: int
    weights_total: float
    all_requirements_satisfied: bool
    summary_message: str


def validate_criteria(criteria: List[CriterionInput]) -> None:
    """
    Validates criteria count, names, and percentage weights.
    Rules:
    - At least 1 criterion required (at least 2 recommended).
    - Names must not be blank or whitespace-only.
    - Weights must be non-negative.
    - Total sum of weights must equal exactly 100% (within tolerance).
    """
    if not criteria:
        raise ScoringValidationError("At least one criterion is required to evaluate alternatives.")

    seen_names = set()
    total_weight = 0.0

    for c in criteria:
        if not c.name or not c.name.strip():
            raise ScoringValidationError("Criterion name cannot be empty or whitespace.")

        clean_name = c.name.strip().lower()
        if clean_name in seen_names:
            raise ScoringValidationError(f"Duplicate criterion name detected: '{c.name}'.")
        seen_names.add(clean_name)

        if not isinstance(c.weight, (int, float)) or math.isnan(c.weight) or math.isinf(c.weight):
            raise ScoringValidationError(f"Weight for '{c.name}' must be a valid number.")

        if c.weight < 0:
            raise ScoringValidationError(f"Weight for '{c.name}' cannot be negative ({c.weight}%).")

        total_weight += c.weight

    if abs(total_weight - 100.0) > WEIGHT_SUM_TOLERANCE:
        raise ScoringValidationError(
            f"Criterion weights must sum to exactly 100%. Current sum: {round(total_weight, 2)}%."
        )


def validate_options(options: List[OptionInput]) -> None:
    """
    Validates options count and names.
    Rules:
    - At least two alternatives required for a meaningful comparison.
    - Names must not be empty or blank.
    - Duplicate names are rejected.
    """
    if not options or len(options) < 2:
        raise ScoringValidationError("At least two alternatives are required to compare choices.")

    seen_names = set()
    for opt in options:
        if not opt.name or not opt.name.strip():
            raise ScoringValidationError("Alternative name cannot be empty or whitespace.")

        clean_name = opt.name.strip().lower()
        if clean_name in seen_names:
            raise ScoringValidationError(f"Duplicate alternative name detected: '{opt.name}'.")
        seen_names.add(clean_name)


def validate_ratings(
    options: List[OptionInput],
    criteria: List[CriterionInput],
    ratings: Dict[Tuple[str, str], float]
) -> None:
    """
    Validates that:
    - Every option x criterion pair has an explicit rating.
    - Missing ratings are never silently substituted with zero.
    - Ratings are numeric values between 1 and 10 (inclusive).
    """
    for opt in options:
        for crit in criteria:
            key = (opt.id, crit.id)
            if key not in ratings:
                raise ScoringValidationError(
                    f"Missing rating for alternative '{opt.name}' on criterion '{crit.name}'. "
                    "Every rating must be explicitly provided."
                )

            val = ratings[key]
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                raise ScoringValidationError(
                    f"Rating for '{opt.name}' on '{crit.name}' must be a valid number."
                )

            if val < 1.0 or val > 10.0:
                raise ScoringValidationError(
                    f"Rating for '{opt.name}' on '{crit.name}' is {val}. "
                    "Ratings must be between 1 and 10."
                )


def evaluate_constraint(
    constraint: ConstraintInput,
    option: OptionInput
) -> ConstraintEvaluationResult:
    """
    Evaluates a single hard requirement against an option's attributes.
    Supports <=, >=, <, >, ==.
    Never silently passes an option if the attribute is missing.
    """
    attr_key = constraint.attribute_key
    threshold = constraint.threshold
    op = constraint.operator

    if op not in SUPPORTED_OPERATORS:
        raise ScoringValidationError(
            f"Unsupported constraint operator: '{op}'. Supported operators: {SUPPORTED_OPERATORS}"
        )

    if attr_key not in option.attributes:
        return ConstraintEvaluationResult(
            constraint_id=constraint.id,
            constraint_name=constraint.name,
            satisfied=False,
            reason=f"Missing attribute '{attr_key}' required by constraint '{constraint.name}'."
        )

    val = option.attributes[attr_key]
    if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
        return ConstraintEvaluationResult(
            constraint_id=constraint.id,
            constraint_name=constraint.name,
            satisfied=False,
            reason=f"Attribute '{attr_key}' value ({val}) is not a valid number."
        )

    satisfied = False
    if op == ">=":
        satisfied = val >= threshold
    elif op == "<=":
        satisfied = val <= threshold
    elif op == ">":
        satisfied = val > threshold
    elif op == "<":
        satisfied = val < threshold
    elif op == "==":
        satisfied = abs(val - threshold) < 1e-6

    if satisfied:
        reason = f"Satisfied: {attr_key} ({val}) {op} {threshold}"
    else:
        reason = f"Failed requirement: {attr_key} is {val}, but required {op} {threshold}"

    return ConstraintEvaluationResult(
        constraint_id=constraint.id,
        constraint_name=constraint.name,
        satisfied=satisfied,
        reason=reason
    )


def calculate_decision(
    options: List[OptionInput],
    criteria: List[CriterionInput],
    ratings: Dict[Tuple[str, str], float],
    constraints: Optional[List[ConstraintInput]] = None
) -> DecisionEvaluationOutput:
    """
    Main evaluation pipeline:
    1. Validates options, criteria, and ratings completeness.
    2. Checks all hard constraints for eligibility.
    3. Calculates weighted scores: Score = sum((weight * rating) / 100).
    4. Ranks eligible alternatives first, followed by ineligible ones.
    5. Implements deterministic tie handling.
    """
    validate_options(options)
    validate_criteria(criteria)
    validate_ratings(options, criteria, ratings)

    constraints = constraints or []
    scored_options: List[OptionScoringResult] = []

    for opt in options:
        # Step A: Evaluate Hard Constraints
        failed_reasons = []
        constraint_results = []
        is_eligible = True

        for c in constraints:
            eval_res = evaluate_constraint(c, opt)
            constraint_results.append(eval_res)
            if not eval_res.satisfied:
                is_eligible = False
                failed_reasons.append(eval_res.reason)

        # Step B: Calculate Weighted Score
        raw_score = 0.0
        criteria_contributions = {}
        criteria_ratings = {}

        for crit in criteria:
            r = ratings[(opt.id, crit.id)]
            contrib = (crit.weight * r) / 100.0
            raw_score += contrib
            criteria_contributions[crit.id] = contrib
            criteria_ratings[crit.id] = r

        scored_options.append(OptionScoringResult(
            option_id=opt.id,
            option_name=opt.name,
            score=raw_score,
            display_score=round(raw_score, 2),
            rank=0,  # Will be assigned during ranking
            is_tied=False,
            is_eligible=is_eligible,
            failed_constraints=failed_reasons,
            constraint_results=constraint_results,
            criteria_contributions=criteria_contributions,
            criteria_ratings=criteria_ratings
        ))

    # Step C: Ranking & Deterministic Tie Handling
    # Separate eligible and ineligible
    eligible = [o for o in scored_options if o.is_eligible]
    ineligible = [o for o in scored_options if not o.is_eligible]

    # Sort descending by unrounded score. For deterministic sorting when scores are equal, sort by option name.
    eligible.sort(key=lambda x: (-x.score, x.option_name.lower()))
    ineligible.sort(key=lambda x: (-x.score, x.option_name.lower()))

    # Assign ranks to eligible options
    current_rank = 1
    for i, opt in enumerate(eligible):
        if i > 0:
            prev_opt = eligible[i - 1]
            # If scores match within precision tolerance, they share the exact same rank
            if abs(opt.score - prev_opt.score) < 1e-6:
                opt.rank = prev_opt.rank
                opt.is_tied = True
                prev_opt.is_tied = True
            else:
                opt.rank = i + 1
        else:
            opt.rank = current_rank

    # Assign ranks to ineligible options (ranked after all eligible options, or indicated with rank)
    ineligible_start_rank = len(eligible) + 1
    for i, opt in enumerate(ineligible):
        if i > 0:
            prev_opt = ineligible[i - 1]
            if abs(opt.score - prev_opt.score) < 1e-6:
                opt.rank = prev_opt.rank
                opt.is_tied = True
                prev_opt.is_tied = True
            else:
                opt.rank = ineligible_start_rank + i
        else:
            opt.rank = ineligible_start_rank

    all_ranked = eligible + ineligible

    eligible_count = len(eligible)
    ineligible_count = len(ineligible)

    if eligible_count == 0:
        summary = "No alternatives satisfy all current hard requirements."
    elif ineligible_count > 0:
        summary = f"{eligible_count} of {len(options)} alternatives meet all requirements."
    else:
        summary = f"All {eligible_count} alternatives meet all requirements and are ranked by weighted score."

    total_weights = sum(c.weight for c in criteria)

    return DecisionEvaluationOutput(
        options=all_ranked,
        total_options_evaluated=len(options),
        eligible_count=eligible_count,
        ineligible_count=ineligible_count,
        weights_total=total_weights,
        all_requirements_satisfied=(ineligible_count == 0),
        summary_message=summary
    )
