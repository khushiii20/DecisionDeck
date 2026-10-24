"""
Unit Tests for DecisionDeck Weighted Scoring Engine & Constraint Satisfaction
Covers:
- Standard specification calculation (8.1 example)
- Deterministic ties
- Boundary and validation checks
- Hard constraint filtering
- Floating-point accuracy
"""

import pytest
import math
from app.scoring import (
    CriterionInput,
    OptionInput,
    ConstraintInput,
    calculate_decision,
    ScoringValidationError,
    WEIGHT_SUM_TOLERANCE,
)


def test_example_calculation_produces_8_point_1():
    """
    Verifies the specification example:
    Career relevance: 40%
    Personal interest: 30%
    Ease of learning: 20%
    Affordability: 10%
    Option ratings: 8, 9, 7, 8
    Score = (0.40 * 8) + (0.30 * 9) + (0.20 * 7) + (0.10 * 8) = 8.1
    """
    criteria = [
        CriterionInput(id="c1", name="Career Relevance", weight=40.0),
        CriterionInput(id="c2", name="Personal Interest", weight=30.0),
        CriterionInput(id="c3", name="Ease of Learning", weight=20.0),
        CriterionInput(id="c4", name="Affordability", weight=10.0),
    ]

    options = [
        OptionInput(id="o1", name="Cloud Engineer"),
        OptionInput(id="o2", name="Mobile Developer"),
    ]

    ratings = {
        ("o1", "c1"): 8.0,
        ("o1", "c2"): 9.0,
        ("o1", "c3"): 7.0,
        ("o1", "c4"): 8.0,
        # Option 2 baseline ratings
        ("o2", "c1"): 6.0,
        ("o2", "c2"): 7.0,
        ("o2", "c3"): 6.0,
        ("o2", "c4"): 7.0,
    }

    result = calculate_decision(options, criteria, ratings)

    o1_res = next(o for o in result.options if o.option_id == "o1")
    assert math.isclose(o1_res.score, 8.1, rel_tol=1e-5)
    assert o1_res.display_score == 8.1
    assert o1_res.rank == 1
    assert o1_res.is_eligible is True
    assert not o1_res.is_tied


def test_equal_scores_result_in_deterministic_tie():
    """Equal scores must be assigned identical ranks and flagged as tied."""
    criteria = [
        CriterionInput(id="c1", name="Quality", weight=50.0),
        CriterionInput(id="c2", name="Cost", weight=50.0),
    ]
    options = [
        OptionInput(id="o1", name="Option Alpha"),
        OptionInput(id="o2", name="Option Beta"),
    ]
    ratings = {
        ("o1", "c1"): 8.0,
        ("o1", "c2"): 6.0,  # Score: 4.0 + 3.0 = 7.0
        ("o2", "c1"): 6.0,
        ("o2", "c2"): 8.0,  # Score: 3.0 + 4.0 = 7.0
    }

    result = calculate_decision(options, criteria, ratings)

    assert result.options[0].rank == 1
    assert result.options[1].rank == 1
    assert result.options[0].is_tied is True
    assert result.options[1].is_tied is True
    assert math.isclose(result.options[0].score, 7.0)
    assert math.isclose(result.options[1].score, 7.0)


def test_weight_change_alters_rankings():
    """Shifting weights from one criterion to another correctly flips option rankings."""
    options = [
        OptionInput(id="o1", name="Option Speed"),
        OptionInput(id="o2", name="Option Quality"),
    ]
    ratings = {
        ("o1", "c1"): 9.0, ("o1", "c2"): 5.0,
        ("o2", "c1"): 5.0, ("o2", "c2"): 9.0,
    }

    # Case A: Priority on c1 (Speed: 80%, Quality: 20%)
    criteria_a = [
        CriterionInput(id="c1", name="Speed", weight=80.0),
        CriterionInput(id="c2", name="Quality", weight=20.0),
    ]
    res_a = calculate_decision(options, criteria_a, ratings)
    assert res_a.options[0].option_id == "o1"
    assert res_a.options[0].rank == 1

    # Case B: Priority on c2 (Speed: 20%, Quality: 80%)
    criteria_b = [
        CriterionInput(id="c1", name="Speed", weight=20.0),
        CriterionInput(id="c2", name="Quality", weight=80.0),
    ]
    res_b = calculate_decision(options, criteria_b, ratings)
    assert res_b.options[0].option_id == "o2"
    assert res_b.options[0].rank == 1


def test_weights_sum_validation():
    """Weights summing to less than 100% or greater than 100% are rejected."""
    options = [OptionInput("o1", "A"), OptionInput("o2", "B")]
    ratings = {
        ("o1", "c1"): 5.0, ("o1", "c2"): 5.0,
        ("o2", "c1"): 5.0, ("o2", "c2"): 5.0,
    }

    # Under 100%
    crit_under = [CriterionInput("c1", "Crit1", 40.0), CriterionInput("c2", "Crit2", 50.0)]
    with pytest.raises(ScoringValidationError, match="must sum to exactly 100%"):
        calculate_decision(options, crit_under, ratings)

    # Over 100%
    crit_over = [CriterionInput("c1", "Crit1", 60.0), CriterionInput("c2", "Crit2", 50.0)]
    with pytest.raises(ScoringValidationError, match="must sum to exactly 100%"):
        calculate_decision(options, crit_over, ratings)


def test_negative_weights_rejected():
    """Negative weights must raise ScoringValidationError."""
    options = [OptionInput("o1", "A"), OptionInput("o2", "B")]
    crit = [CriterionInput("c1", "C1", -10.0), CriterionInput("c2", "C2", 110.0)]
    ratings = {("o1", "c1"): 5.0, ("o1", "c2"): 5.0, ("o2", "c1"): 5.0, ("o2", "c2"): 5.0}

    with pytest.raises(ScoringValidationError, match="cannot be negative"):
        calculate_decision(options, crit, ratings)


def test_missing_ratings_rejected_not_zeroed():
    """Engine must reject missing ratings rather than silently assuming zero."""
    options = [OptionInput("o1", "A"), OptionInput("o2", "B")]
    crit = [CriterionInput("c1", "C1", 50.0), CriterionInput("c2", "C2", 50.0)]
    # Missing ("o2", "c2")
    incomplete_ratings = {
        ("o1", "c1"): 7.0, ("o1", "c2"): 8.0,
        ("o2", "c1"): 6.0,
    }

    with pytest.raises(ScoringValidationError, match="Missing rating for alternative"):
        calculate_decision(options, crit, incomplete_ratings)


def test_rating_out_of_bounds_rejected():
    """Ratings strictly below 1 or strictly above 10 must be rejected."""
    options = [OptionInput("o1", "A"), OptionInput("o2", "B")]
    crit = [CriterionInput("c1", "C1", 100.0)]

    # Rating 0 (below min 1)
    with pytest.raises(ScoringValidationError, match="Ratings must be between 1 and 10"):
        calculate_decision(options, crit, {("o1", "c1"): 0.0, ("o2", "c1"): 5.0})

    # Rating 11 (above max 10)
    with pytest.raises(ScoringValidationError, match="Ratings must be between 1 and 10"):
        calculate_decision(options, crit, {("o1", "c1"): 11.0, ("o2", "c1"): 5.0})


def test_invalid_numeric_types_rejected():
    """NaN or Inf values for ratings and weights are rejected."""
    options = [OptionInput("o1", "A"), OptionInput("o2", "B")]

    # NaN weight
    with pytest.raises(ScoringValidationError, match="must be a valid number"):
        calculate_decision(options, [CriterionInput("c1", "C1", float("nan"))], {})

    # Inf rating
    crit = [CriterionInput("c1", "C1", 100.0)]
    with pytest.raises(ScoringValidationError, match="must be a valid number"):
        calculate_decision(options, crit, {("o1", "c1"): float("inf"), ("o2", "c1"): 5.0})


def test_hard_requirements_exclude_ineligible_options():
    """Hard constraints must exclude options and explain failure while ranking eligible options."""
    options = [
        OptionInput(id="laptop_a", name="Laptop A", attributes={"price": 1200, "battery_hours": 12}),
        OptionInput(id="laptop_b", name="Laptop B", attributes={"price": 1800, "battery_hours": 15}),
        OptionInput(id="laptop_c", name="Laptop C", attributes={"price": 900, "battery_hours": 8}),
    ]

    criteria = [
        CriterionInput(id="perf", name="Performance", weight=100.0)
    ]

    ratings = {
        ("laptop_a", "perf"): 8.0,
        ("laptop_b", "perf"): 10.0,
        ("laptop_c", "perf"): 6.0,
    }

    # Hard requirements: Price <= 1500, Battery >= 10
    constraints = [
        ConstraintInput(id="budget", name="Max Budget", attribute_key="price", operator="<=", threshold=1500),
        ConstraintInput(id="battery", name="Min Battery", attribute_key="battery_hours", operator=">=", threshold=10),
    ]

    result = calculate_decision(options, criteria, ratings, constraints)

    # Laptop A: price 1200 (<=1500), battery 12 (>=10) -> Eligible
    # Laptop B: price 1800 (>1500) -> Ineligible
    # Laptop C: battery 8 (<10) -> Ineligible
    assert result.eligible_count == 1
    assert result.ineligible_count == 2

    laptop_a_res = next(o for o in result.options if o.option_id == "laptop_a")
    assert laptop_a_res.is_eligible is True
    assert laptop_a_res.rank == 1

    laptop_b_res = next(o for o in result.options if o.option_id == "laptop_b")
    assert laptop_b_res.is_eligible is False
    assert any("price is 1800" in r for r in laptop_b_res.failed_constraints)

    laptop_c_res = next(o for o in result.options if o.option_id == "laptop_c")
    assert laptop_c_res.is_eligible is False
    assert any("battery_hours is 8" in r for r in laptop_c_res.failed_constraints)


def test_no_qualifying_alternatives_handled_gracefully():
    """When all options fail hard constraints, eligible count is 0 with descriptive message."""
    options = [
        OptionInput(id="o1", name="Alpha", attributes={"budget": 2000}),
        OptionInput(id="o2", name="Beta", attributes={"budget": 2500}),
    ]
    crit = [CriterionInput(id="c1", name="Fit", weight=100.0)]
    ratings = {("o1", "c1"): 8.0, ("o2", "c1"): 7.0}
    constraints = [ConstraintInput(id="b", name="Budget", attribute_key="budget", operator="<=", threshold=1000)]

    result = calculate_decision(options, crit, ratings, constraints)
    assert result.eligible_count == 0
    assert result.ineligible_count == 2
    assert "No alternatives satisfy all current hard requirements" in result.summary_message


def test_floating_point_tolerance():
    """Three criteria with 33.333% + 33.333% + 33.334% sum to 100% within tolerance."""
    criteria = [
        CriterionInput(id="c1", name="Crit 1", weight=33.333),
        CriterionInput(id="c2", name="Crit 2", weight=33.333),
        CriterionInput(id="c3", name="Crit 3", weight=33.334),
    ]
    options = [OptionInput("o1", "Opt 1"), OptionInput("o2", "Opt 2")]
    ratings = {
        ("o1", "c1"): 8.0, ("o1", "c2"): 8.0, ("o1", "c3"): 8.0,
        ("o2", "c1"): 6.0, ("o2", "c2"): 6.0, ("o2", "c3"): 6.0,
    }

    result = calculate_decision(options, criteria, ratings)
    assert math.isclose(result.options[0].score, 8.0, rel_tol=1e-4)


def test_duplicate_and_blank_names_rejected():
    """Engine must reject duplicate option names and blank names."""
    # Blank option name
    with pytest.raises(ScoringValidationError, match="cannot be empty"):
        calculate_decision(
            [OptionInput("o1", ""), OptionInput("o2", "Beta")],
            [CriterionInput("c1", "Crit", 100.0)],
            {("o1", "c1"): 5.0, ("o2", "c1"): 5.0}
        )

    # Duplicate option names
    with pytest.raises(ScoringValidationError, match="Duplicate alternative name"):
        calculate_decision(
            [OptionInput("o1", "SameName"), OptionInput("o2", "samename")],
            [CriterionInput("c1", "Crit", 100.0)],
            {("o1", "c1"): 5.0, ("o2", "c1"): 5.0}
        )

    # Fewer than 2 options
    with pytest.raises(ScoringValidationError, match="At least two alternatives are required"):
        calculate_decision(
            [OptionInput("o1", "Solo")],
            [CriterionInput("c1", "Crit", 100.0)],
            {("o1", "c1"): 5.0}
        )
