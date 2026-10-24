"""
Decisions API Routes for DecisionDeck
Provides CRUD, calculation, simulation, and CSV export with verified user isolation.
"""

import io
import csv
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Decision, Option, Criterion, Rating, Constraint
from app.schemas import (
    DecisionCreate,
    DecisionUpdate,
    DecisionSummaryResponse,
    DecisionDetailResponse,
    DecisionEvaluationResponse,
    OptionScoreSchema,
    ConstraintEvaluationSchema,
    SimulateWeightsRequest,
)
from app.auth import get_current_user
from app.scoring import (
    CriterionInput,
    OptionInput,
    ConstraintInput,
    calculate_decision,
    ScoringValidationError,
)

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


def get_user_decision(decision_id: str, current_user: User, db: Session) -> Decision:
    """
    Helper to verify ownership of a decision.
    Returns 404 if not found or if owned by another user (preventing ID enumeration).
    """
    decision = db.query(Decision).filter(
        Decision.id == decision_id,
        Decision.user_id == current_user.id
    ).first()
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found."
        )
    return decision


@router.post("", response_model=DecisionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_decision(
    decision_in: DecisionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new decision with options, criteria, ratings, and optional hard constraints.
    All records are strictly linked to the authenticated user.
    """
    decision = Decision(
        user_id=current_user.id,
        title=decision_in.title.strip(),
        description=decision_in.description.strip() if decision_in.description else None
    )
    db.add(decision)
    db.flush()  # Populates decision.id

    # Create Options
    option_map = {}  # temporary client id/name -> created Option
    for idx, opt_data in enumerate(decision_in.options):
        opt = Option(
            decision_id=decision.id,
            name=opt_data.name.strip(),
            description=opt_data.description.strip() if opt_data.description else None,
            display_order=opt_data.display_order if opt_data.display_order else idx,
            attributes=opt_data.attributes
        )
        db.add(opt)
        db.flush()
        # Key by provided id or fallback to name
        if opt_data.id:
            option_map[opt_data.id] = opt
        option_map[opt.name] = opt
        option_map[str(idx)] = opt

    # Create Criteria
    crit_map = {}  # temporary client id/name -> created Criterion
    for idx, crit_data in enumerate(decision_in.criteria):
        crit = Criterion(
            decision_id=decision.id,
            name=crit_data.name.strip(),
            weight=crit_data.weight,
            display_order=crit_data.display_order if crit_data.display_order else idx
        )
        db.add(crit)
        db.flush()
        if crit_data.id:
            crit_map[crit_data.id] = crit
        crit_map[crit.name] = crit
        crit_map[str(idx)] = crit

    # Create Constraints
    for c_data in decision_in.constraints:
        constraint = Constraint(
            decision_id=decision.id,
            name=c_data.name.strip(),
            attribute_key=c_data.attribute_key.strip(),
            operator=c_data.operator,
            threshold=c_data.threshold
        )
        db.add(constraint)

    # Create Ratings
    for r_data in decision_in.ratings:
        # Match option
        target_opt = option_map.get(r_data.option_id)
        target_crit = crit_map.get(r_data.criterion_id)

        if not target_opt:
            # Maybe r_data.option_id was already the DB id
            target_opt = db.query(Option).filter(Option.id == r_data.option_id, Option.decision_id == decision.id).first()
        if not target_crit:
            target_crit = db.query(Criterion).filter(Criterion.id == r_data.criterion_id, Criterion.decision_id == decision.id).first()

        if target_opt and target_crit:
            rating_rec = Rating(
                option_id=target_opt.id,
                criterion_id=target_crit.id,
                rating=r_data.rating
            )
            db.add(rating_rec)

    db.commit()
    db.refresh(decision)
    return decision


@router.get("", response_model=List[DecisionSummaryResponse])
def list_decisions(
    q: Optional[str] = Query(None, description="Search term for title or description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a summary list of all decisions owned by the current user.
    Supports title / description searching.
    """
    query = db.query(Decision).filter(Decision.user_id == current_user.id)
    if q and q.strip():
        search_filter = f"%{q.strip()}%"
        query = query.filter(
            (Decision.title.ilike(search_filter)) | (Decision.description.ilike(search_filter))
        )
    decisions = query.order_by(Decision.updated_at.desc()).all()

    # Format summaries with count fields
    summaries = []
    for d in decisions:
        summaries.append(DecisionSummaryResponse(
            id=d.id,
            title=d.title,
            description=d.description,
            created_at=d.created_at,
            updated_at=d.updated_at,
            options_count=len(d.options),
            criteria_count=len(d.criteria)
        ))
    return summaries


@router.get("/{decision_id}", response_model=DecisionDetailResponse)
def get_decision(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves full details of a specific decision, including options, criteria, ratings, and constraints.
    Enforces user isolation.
    """
    return get_user_decision(decision_id, current_user, db)


@router.put("/{decision_id}", response_model=DecisionDetailResponse)
def update_decision(
    decision_id: str,
    decision_update: DecisionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing decision. If options, criteria, ratings, or constraints are provided,
    they are safely updated to reflect the new state.
    """
    decision = get_user_decision(decision_id, current_user, db)

    if decision_update.title is not None:
        decision.title = decision_update.title.strip()
    if decision_update.description is not None:
        decision.description = decision_update.description.strip() if decision_update.description else None

    # Replace options if provided
    if decision_update.options is not None:
        # Delete existing ratings and options
        db.query(Rating).filter(Rating.option_id.in_([o.id for o in decision.options])).delete(synchronize_session=False)
        db.query(Option).filter(Option.decision_id == decision.id).delete(synchronize_session=False)

        option_map = {}
        for idx, opt_data in enumerate(decision_update.options):
            new_opt = Option(
                decision_id=decision.id,
                name=opt_data.name.strip(),
                description=opt_data.description.strip() if opt_data.description else None,
                display_order=idx,
                attributes=opt_data.attributes
            )
            db.add(new_opt)
            db.flush()
            if opt_data.id:
                option_map[opt_data.id] = new_opt
            option_map[new_opt.name] = new_opt
            option_map[str(idx)] = new_opt

    # Replace criteria if provided
    if decision_update.criteria is not None:
        # Delete criteria (and orphan ratings if any remain)
        db.query(Rating).filter(Rating.criterion_id.in_([c.id for c in decision.criteria])).delete(synchronize_session=False)
        db.query(Criterion).filter(Criterion.decision_id == decision.id).delete(synchronize_session=False)

        crit_map = {}
        for idx, crit_data in enumerate(decision_update.criteria):
            new_crit = Criterion(
                decision_id=decision.id,
                name=crit_data.name.strip(),
                weight=crit_data.weight,
                display_order=idx
            )
            db.add(new_crit)
            db.flush()
            if crit_data.id:
                crit_map[crit_data.id] = new_crit
            crit_map[new_crit.name] = new_crit
            crit_map[str(idx)] = new_crit

    # Replace constraints if provided
    if decision_update.constraints is not None:
        db.query(Constraint).filter(Constraint.decision_id == decision.id).delete(synchronize_session=False)
        for c_data in decision_update.constraints:
            db.add(Constraint(
                decision_id=decision.id,
                name=c_data.name.strip(),
                attribute_key=c_data.attribute_key.strip(),
                operator=c_data.operator,
                threshold=c_data.threshold
            ))

    # Replace ratings if provided
    if decision_update.ratings is not None:
        # Fetch current options and criteria for ID resolution
        current_options = {o.id: o for o in decision.options}
        current_criteria = {c.id: c for c in decision.criteria}

        # Clear existing ratings
        db.query(Rating).filter(
            Rating.option_id.in_([o.id for o in decision.options])
        ).delete(synchronize_session=False)

        for r_data in decision_update.ratings:
            opt = current_options.get(r_data.option_id)
            crit = current_criteria.get(r_data.criterion_id)
            if opt and crit:
                db.add(Rating(
                    option_id=opt.id,
                    criterion_id=crit.id,
                    rating=r_data.rating
                ))

    decision.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(decision)
    return decision


@router.delete("/{decision_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_decision(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a decision and all child items.
    Enforces user isolation.
    """
    decision = get_user_decision(decision_id, current_user, db)
    db.delete(decision)
    db.commit()
    return None


@router.post("/{decision_id}/calculate", response_model=DecisionEvaluationResponse)
def calculate_decision_scores(
    decision_id: str,
    simulation: Optional[SimulateWeightsRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates the decision using the scoring engine:
    - Calculates weighted scores
    - Evaluates hard constraints
    - Ranks alternatives with tie handling
    Supports 'What-if Simulation': if temporary weights are provided, they are evaluated
    without altering the persistent database records.
    """
    decision = get_user_decision(decision_id, current_user, db)

    # Convert database models to scoring engine inputs
    opts = [
        OptionInput(
            id=o.id,
            name=o.name,
            description=o.description,
            attributes=o.attributes or {}
        )
        for o in decision.options
    ]

    # Handle temporary simulation weights vs saved weights
    crit_inputs = []
    for c in decision.criteria:
        weight = c.weight
        if simulation and simulation.temporary_weights and c.id in simulation.temporary_weights:
            weight = simulation.temporary_weights[c.id]
        crit_inputs.append(CriterionInput(id=c.id, name=c.name, weight=weight))

    constraints_inputs = [
        ConstraintInput(
            id=con.id,
            name=con.name,
            attribute_key=con.attribute_key,
            operator=con.operator,
            threshold=con.threshold
        )
        for con in decision.constraints
    ]

    ratings_map = {
        (r.option_id, r.criterion_id): r.rating
        for r in db.query(Rating).filter(Rating.option_id.in_([o.id for o in decision.options])).all()
    }

    try:
        output = calculate_decision(opts, crit_inputs, ratings_map, constraints_inputs)
    except ScoringValidationError as err:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(err))

    # Format response
    option_responses = [
        OptionScoreSchema(
            option_id=o.option_id,
            option_name=o.option_name,
            score=o.score,
            display_score=o.display_score,
            rank=o.rank,
            is_tied=o.is_tied,
            is_eligible=o.is_eligible,
            failed_constraints=o.failed_constraints,
            constraint_results=[
                ConstraintEvaluationSchema(
                    constraint_id=cr.constraint_id,
                    constraint_name=cr.constraint_name,
                    satisfied=cr.satisfied,
                    reason=cr.reason
                )
                for cr in o.constraint_results
            ],
            criteria_contributions=o.criteria_contributions,
            criteria_ratings=o.criteria_ratings
        )
        for o in output.options
    ]

    return DecisionEvaluationResponse(
        options=option_responses,
        total_options_evaluated=output.total_options_evaluated,
        eligible_count=output.eligible_count,
        ineligible_count=output.ineligible_count,
        weights_total=output.weights_total,
        all_requirements_satisfied=output.all_requirements_satisfied,
        summary_message=output.summary_message
    )


@router.get("/{decision_id}/export")
def export_decision_csv(
    decision_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports decision details, criteria weights, individual ratings, calculated scores,
    and eligibility status as a RFC 4180-compliant CSV.
    Enforces user isolation.
    """
    decision = get_user_decision(decision_id, current_user, db)

    # Evaluate decision to get current scores and ranks
    opts = [
        OptionInput(id=o.id, name=o.name, description=o.description, attributes=o.attributes or {})
        for o in decision.options
    ]
    crit_inputs = [CriterionInput(id=c.id, name=c.name, weight=c.weight) for c in decision.criteria]
    constraints_inputs = [
        ConstraintInput(id=con.id, name=con.name, attribute_key=con.attribute_key, operator=con.operator, threshold=con.threshold)
        for con in decision.constraints
    ]
    ratings_map = {
        (r.option_id, r.criterion_id): r.rating
        for r in db.query(Rating).filter(Rating.option_id.in_([o.id for o in decision.options])).all()
    }

    try:
        eval_output = calculate_decision(opts, crit_inputs, ratings_map, constraints_inputs)
        scores_by_id = {o.option_id: o for o in eval_output.options}
    except ScoringValidationError:
        scores_by_id = {}

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Metadata Header
    writer.writerow(["DecisionDeck Decision Export"])
    writer.writerow(["Title", decision.title])
    writer.writerow(["Description", decision.description or ""])
    writer.writerow(["Exported At (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])

    # Criteria Summary
    writer.writerow(["--- Criteria & Importance Weights ---"])
    writer.writerow(["Criterion Name", "Weight (%)"])
    for c in decision.criteria:
        writer.writerow([c.name, f"{c.weight}%"])
    writer.writerow([])

    # Results Matrix Table
    writer.writerow(["--- Decision Results & Ratings Matrix ---"])
    header_row = ["Rank", "Alternative", "Eligible?", "Calculated Score"]
    for c in decision.criteria:
        header_row.append(f"{c.name} ({c.weight}%)")
    header_row.append("Constraint Notes")
    writer.writerow(header_row)

    # Rows
    for o in decision.options:
        score_info = scores_by_id.get(o.id)
        rank_str = str(score_info.rank) if score_info else "N/A"
        if score_info and score_info.is_tied:
            rank_str += " (Tied)"
        score_str = f"{score_info.display_score:.2f}" if score_info else "N/A"
        eligible_str = "Yes" if (score_info and score_info.is_eligible) else "No"
        notes = "; ".join(score_info.failed_constraints) if (score_info and score_info.failed_constraints) else "All requirements met"

        row = [rank_str, o.name, eligible_str, score_str]
        for c in decision.criteria:
            r_val = ratings_map.get((o.id, c.id), "N/A")
            row.append(r_val)
        row.append(notes)
        writer.writerow(row)

    output.seek(0)

    # Safe filename
    clean_title = "".join(c if c.isalnum() else "_" for c in decision.title)[:30]
    filename = f"decisiondeck_{clean_title}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
