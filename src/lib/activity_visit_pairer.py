"""
Activity-Visit Pairing System

Automatically pairs Strava activities (flagged as onsen_monitoring) with existing
onsen visits based on name similarity and time proximity.

Pairing Algorithm:
    1. Extract onsen name from activity title (Japanese or romanized)
    2. Find candidate visits within time window (±N hours)
    3. Score candidates using: 0.6 × name_similarity + 0.4 × time_proximity
    4. Auto-link if confidence ≥ threshold, otherwise flag for review

Usage:
    from src.lib.activity_visit_pairer import pair_activities_to_visits, PairingConfig

    config = PairingConfig(auto_link_threshold=0.8, time_window_hours=4)
    results = pair_activities_to_visits(db_session, activity_ids, config)

    # Apply auto-links
    for activity, visit, confidence in results.auto_linked:
        activity_manager.link_to_visit(activity.id, visit.id)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.db.models import Activity, OnsenVisit
from src.types.exercise import ExerciseType


@dataclass
class PairingConfig:
    """Configuration for activity-visit pairing behavior."""

    auto_link_threshold: float = 0.8
    """Auto-link activities with confidence ≥ this value (default: 0.8 = 80%)"""

    review_threshold: float = 0.6
    """Require manual review for confidence in [review, auto) range (default: 0.6)"""

    time_window_hours: int = 4
    """Search for visits within ±N hours of activity start (default: 4)"""

    name_weight: float = 0.6
    """Weight for name similarity in combined score (default: 0.6 = 60%)"""

    time_weight: float = 0.4
    """Weight for time proximity in combined score (default: 0.4 = 40%)"""

    max_candidates: int = 5
    """Maximum number of candidates to return for manual review (default: 5)"""


@dataclass
class ScoredCandidate:
    """A visit candidate with scoring metrics."""

    visit: OnsenVisit
    """The candidate visit"""

    name_similarity: float
    """Name similarity score (0.0-1.0)"""

    time_diff_minutes: float
    """Absolute time difference in minutes"""

    combined_score: float
    """Weighted combined score (0.0-1.0)"""

    @property
    def onsen_name(self) -> str:
        """Get the onsen name for display."""
        return self.visit.onsen.name


@dataclass
class PairingResults:
    """Results of pairing operation, categorized by confidence."""

    auto_linked: list[tuple[Activity, OnsenVisit, float]] = field(default_factory=list)
    """High-confidence matches (≥auto_link_threshold) ready for automatic linking"""

    manual_review: list[tuple[Activity, list[ScoredCandidate]]] = field(default_factory=list)
    """Medium-confidence matches requiring manual review"""

    no_match: list[Activity] = field(default_factory=list)
    """Activities with no suitable candidates found"""

    def total_activities(self) -> int:
        """Total number of activities processed."""
        return len(self.auto_linked) + len(self.manual_review) + len(self.no_match)

    def summary_stats(self) -> dict[str, int]:
        """Get summary statistics."""
        return {
            'auto_linked': len(self.auto_linked),
            'manual_review': len(self.manual_review),
            'no_match': len(self.no_match),
            'total': self.total_activities(),
        }


def extract_onsen_name(activity_name: str) -> Optional[str]:
    """
    Extract onsen name from Strava activity title.

    Tries two strategies:
    1. Japanese name in parentheses at end (preferred)
    2. Romanized name between "-" and "(" or end of string (fallback)

    Args:
        activity_name: Strava activity title (e.g., "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)")

    Returns:
        Extracted onsen name, or None if extraction fails

    Examples:
        >>> extract_onsen_name("Onsendo 9/88 - Ebisuya onsen (湯屋えびす)")
        "湯屋えびす"

        >>> extract_onsen_name("Onsendo 5/88 - Takegawara onsen")
        "Takegawara"

        >>> extract_onsen_name("Random activity name")
        None
    """
    if not activity_name:
        return None

    # Strategy 1: Japanese name in parentheses at end
    match = re.search(r'\(([^)]+)\)$', activity_name.strip())
    if match:
        japanese_name = match.group(1).strip()
        if japanese_name:
            return japanese_name

    # Strategy 2: Romanized name between "-" and "(" or end
    # Pattern: "- {NAME} (optional_japanese)" or "- {NAME}"
    match = re.search(r'-\s*([^(]+?)(?:\s*\(|$)', activity_name)
    if match:
        romanized_name = match.group(1).strip()
        # Remove common "onsen" suffix if present
        romanized_name = re.sub(r'\s+onsen\s*$', '', romanized_name, flags=re.IGNORECASE)
        if romanized_name:
            return romanized_name

    return None


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two onsen names using fuzzy matching.

    Uses difflib.SequenceMatcher for ratio-based similarity after normalization.

    Args:
        name1: First name (from activity)
        name2: Second name (from visit/onsen)

    Returns:
        Similarity score from 0.0 (no match) to 1.0 (exact match)

    Examples:
        >>> calculate_name_similarity("湯屋えびす", "湯屋えびす")
        1.0

        >>> calculate_name_similarity("Takegawara", "竹瓦温泉")
        0.0  # Different scripts, no match

        >>> calculate_name_similarity("Matsubara", "松原温泉")
        0.0  # Romanized vs Japanese
    """
    # Normalize: lowercase, strip whitespace
    name1_norm = name1.lower().strip()
    name2_norm = name2.lower().strip()

    # Calculate similarity ratio
    return SequenceMatcher(None, name1_norm, name2_norm).ratio()


def score_visit_candidate(
    activity: Activity,
    visit: OnsenVisit,
    config: PairingConfig,
) -> ScoredCandidate:
    """
    Score a visit candidate against an activity.

    Scoring combines two factors:
    - Name similarity (0.0-1.0) from fuzzy matching
    - Time proximity (0.0-1.0) based on distance within time window

    Combined score = name_weight × name_sim + time_weight × time_proximity

    Args:
        activity: Activity to match
        visit: Candidate visit
        config: Pairing configuration

    Returns:
        ScoredCandidate with all metrics
    """
    # Extract onsen name from activity
    activity_onsen_name = extract_onsen_name(activity.activity_name)
    visit_onsen_name = visit.onsen.name

    # Calculate name similarity
    name_sim = 0.0
    if activity_onsen_name:
        name_sim = calculate_name_similarity(activity_onsen_name, visit_onsen_name)

    # Calculate time proximity
    # Use activity recording_start vs visit_time
    time_diff = abs((visit.visit_time - activity.recording_start).total_seconds() / 60)
    time_diff_minutes = time_diff

    # Convert time diff to score (closer = higher score)
    # Score = 1.0 at 0 minutes, 0.0 at time_window edge
    max_time_diff = config.time_window_hours * 60
    time_score = max(0.0, 1.0 - (time_diff / max_time_diff))

    # Combined weighted score
    combined = (config.name_weight * name_sim) + (config.time_weight * time_score)

    return ScoredCandidate(
        visit=visit,
        name_similarity=name_sim,
        time_diff_minutes=time_diff_minutes,
        combined_score=combined,
    )


def find_visit_candidates(
    db_session: Session,
    activity: Activity,
    config: PairingConfig,
) -> list[ScoredCandidate]:
    """
    Find and score all candidate visits for an activity.

    Filters visits by:
    1. Time window: visit_time within ±N hours of activity start
    2. Name similarity: similarity ≥ review_threshold

    Args:
        db_session: Database session
        activity: Activity to find candidates for
        config: Pairing configuration

    Returns:
        List of scored candidates sorted by combined_score (highest first)
    """
    # Define time window
    time_window = timedelta(hours=config.time_window_hours)
    search_start = activity.recording_start - time_window
    search_end = activity.recording_start + time_window

    # Query visits within time window
    # Join with Onsen to access onsen.name
    nearby_visits = (
        db_session.query(OnsenVisit)
        .join(OnsenVisit.onsen)
        .filter(
            OnsenVisit.visit_time >= search_start,
            OnsenVisit.visit_time <= search_end,
        )
        .all()
    )

    if not nearby_visits:
        logger.debug(
            f"No visits found within {config.time_window_hours}h of activity "
            f"{activity.id} ({activity.activity_name})"
        )
        return []

    # Score all candidates
    scored_candidates = []
    for visit in nearby_visits:
        candidate = score_visit_candidate(activity, visit, config)

        # Only include candidates with name similarity ≥ review_threshold
        if candidate.name_similarity >= config.review_threshold:
            scored_candidates.append(candidate)

    # Sort by combined score (highest first)
    scored_candidates.sort(key=lambda c: c.combined_score, reverse=True)

    # Limit to max_candidates
    return scored_candidates[:config.max_candidates]


def pair_activities_to_visits(
    db_session: Session,
    activity_ids: list[int],
    config: Optional[PairingConfig] = None,
) -> PairingResults:
    """
    Pair multiple activities to visits based on name and time proximity.

    This is the main entry point for the pairing system. It processes a list
    of activity IDs and categorizes them into:
    - Auto-linked: High confidence (≥auto_link_threshold), ready for automatic linking
    - Manual review: Medium confidence (≥review_threshold, <auto_link_threshold)
    - No match: No suitable candidates found

    Args:
        db_session: Database session
        activity_ids: List of activity IDs to process
        config: Pairing configuration (uses defaults if None)

    Returns:
        PairingResults with categorized matches

    Example:
        >>> config = PairingConfig(auto_link_threshold=0.8)
        >>> results = pair_activities_to_visits(db, [123, 124, 125], config)
        >>> print(f"Auto-linked: {len(results.auto_linked)}")
        >>> print(f"Need review: {len(results.manual_review)}")
    """
    if config is None:
        config = PairingConfig()

    results = PairingResults()

    # Fetch activities
    activities = (
        db_session.query(Activity)
        .filter(Activity.id.in_(activity_ids))
        .all()
    )

    logger.info(f"Pairing {len(activities)} activities to visits")

    for activity in activities:
        # Verify activity is onsen_monitoring type
        if activity.activity_type != ExerciseType.ONSEN_MONITORING.value:
            logger.warning(
                f"Activity {activity.id} is not onsen_monitoring type "
                f"(type: {activity.activity_type}), skipping pairing"
            )
            continue

        # Skip already linked activities
        if activity.visit_id is not None:
            logger.debug(f"Activity {activity.id} already linked to visit {activity.visit_id}")
            continue

        # Extract onsen name
        onsen_name = extract_onsen_name(activity.activity_name)
        if not onsen_name:
            logger.warning(
                f"Could not extract onsen name from activity {activity.id}: "
                f"'{activity.activity_name}'"
            )
            results.no_match.append(activity)
            continue

        # Find candidates
        candidates = find_visit_candidates(db_session, activity, config)

        if not candidates:
            logger.debug(
                f"No matching visits found for activity {activity.id} "
                f"(name: {onsen_name})"
            )
            results.no_match.append(activity)
            continue

        # Categorize based on confidence
        best_candidate = candidates[0]

        if best_candidate.combined_score >= config.auto_link_threshold:
            # High confidence - auto-link
            logger.info(
                f"Auto-link candidate found for activity {activity.id}: "
                f"{best_candidate.onsen_name} (confidence: {best_candidate.combined_score:.2%})"
            )
            results.auto_linked.append((activity, best_candidate.visit, best_candidate.combined_score))
        else:
            # Medium confidence - needs review
            logger.info(
                f"Manual review needed for activity {activity.id}: "
                f"best match {best_candidate.onsen_name} "
                f"(confidence: {best_candidate.combined_score:.2%})"
            )
            results.manual_review.append((activity, candidates))

    logger.info(
        f"Pairing complete: {len(results.auto_linked)} auto-linked, "
        f"{len(results.manual_review)} need review, "
        f"{len(results.no_match)} no match"
    )

    return results
