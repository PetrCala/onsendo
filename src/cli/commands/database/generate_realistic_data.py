"""
Generate comprehensive realistic mock data for testing and analysis.

This command creates analysis-ready datasets with:
- User profile-based behavioral patterns
- Realistic correlations (price-quality, weather effects, etc.)
- Econometric relationships for regression analysis
- Optional heart rate data integration
- Pre-configured scenarios for different analysis types

NOTE: This command is blocked from production database access for safety.
"""

import argparse
from loguru import logger

from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen, HeartRateData
from src.config import get_database_config

from src.testing.mocks.integrated_scenario import (
    create_integrated_dataset,
    create_heart_rate_analysis_dataset,
    create_pricing_analysis_dataset,
    create_spatial_analysis_dataset,
    create_temporal_analysis_dataset,
)
from src.testing.mocks.scenario_builder import (
    create_analysis_ready_dataset,
    create_econometric_test_dataset,
    create_tourist_scenario,
    create_local_regular_scenario,
)
from src.testing.mocks.user_profiles import ALL_PROFILES


def generate_realistic_data(args: argparse.Namespace) -> None:
    """
    Generate realistic mock data based on specified scenario.

    NOTE: This command is blocked from production database access for safety.
    """
    # Get database configuration - BLOCK PRODUCTION ACCESS
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None),
        allow_prod=False  # Mock data should never touch production
    )

    with get_db(url=config.url) as db:
        # Get available onsens
        onsen_count = db.query(Onsen).count()
        if onsen_count == 0:
            logger.error("No onsens found in database! Please add onsens first.")
            print("\nError: Database has no onsens. Please run:")
            print("  onsendo database init-db")
            print("  onsendo database fill-db")
            return

        onsen_ids = [onsen.id for onsen in db.query(Onsen).all()]
        logger.info(f"Found {onsen_count} onsens in database")

        # Generate data based on scenario
        scenario = args.scenario
        num_visits = args.num_visits or 100

        logger.info(f"Generating scenario: {scenario}")
        logger.info(f"Target visits: {num_visits}")

        if scenario == 'comprehensive':
            # Best for all-around testing
            logger.info("Creating comprehensive analysis-ready dataset...")
            visits = create_analysis_ready_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
                days=args.days or 90,
            )
            hr_data = []

        elif scenario == 'econometric':
            # Optimized for regression analysis
            logger.info("Creating econometric test dataset...")
            logger.info("Features: Strong correlations, profile heterogeneity, seasonal effects")
            visits = create_econometric_test_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
            )
            hr_data = []

        elif scenario == 'heart_rate':
            # With heart rate integration
            logger.info("Creating heart rate analysis dataset...")
            logger.info("Features: High HR coverage (85%), health-focused profiles")
            integrated_data = create_heart_rate_analysis_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
            )
            visits = [item.visit for item in integrated_data]
            hr_data = [item.heart_rate_session for item in integrated_data if item.heart_rate_session]

        elif scenario == 'pricing':
            # Pricing/value analysis
            logger.info("Creating pricing analysis dataset...")
            logger.info("Features: Wide price range, quality vs budget seekers")
            visits = create_pricing_analysis_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
            )
            hr_data = []

        elif scenario == 'spatial':
            # Geographic patterns
            logger.info("Creating spatial analysis dataset...")
            logger.info("Features: Explorers, tourists, wide geographic coverage")
            visits = create_spatial_analysis_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
            )
            hr_data = []

        elif scenario == 'temporal':
            # Time-based patterns
            logger.info("Creating temporal analysis dataset...")
            logger.info("Features: 12-month coverage, seasonal effects, learning curves")
            visits = create_temporal_analysis_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
                months=args.months or 12,
            )
            hr_data = []

        elif scenario == 'tourist':
            # Intensive tourist trip
            logger.info("Creating tourist scenario...")
            logger.info(f"Features: {args.trip_days or 7}-day trip, multi-onsen days")
            visits = create_tourist_scenario(
                onsen_ids=onsen_ids,
                trip_days=args.trip_days or 7,
                visits_per_day=args.visits_per_day or 3,
            )
            hr_data = []

        elif scenario == 'local_regular':
            # Long-term local visitor
            logger.info("Creating local regular scenario...")
            logger.info(f"Features: {args.months or 12}-month pattern, loyalty, consistency")
            visits = create_local_regular_scenario(
                onsen_ids=onsen_ids,
                months=args.months or 12,
            )
            hr_data = []

        elif scenario == 'integrated':
            # Visits + HR data with configurable coverage
            logger.info("Creating integrated dataset (visits + heart rate)...")
            hr_coverage = args.hr_coverage or 0.6
            logger.info(f"Heart rate coverage: {hr_coverage*100:.0f}%")
            integrated_data = create_integrated_dataset(
                onsen_ids=onsen_ids,
                num_visits=num_visits,
                days=args.days or 90,
                hr_coverage=hr_coverage,
            )
            visits = [item.visit for item in integrated_data]
            hr_data = [item.heart_rate_session for item in integrated_data if item.heart_rate_session]

        else:
            logger.error(f"Unknown scenario: {scenario}")
            print(f"\nError: Unknown scenario '{scenario}'")
            print("\nAvailable scenarios:")
            print("  comprehensive    - All-around testing (mix of profiles)")
            print("  econometric      - Optimized for regression analysis")
            print("  heart_rate       - With HR data integration (85% coverage)")
            print("  pricing          - Price/quality analysis (wide range)")
            print("  spatial          - Geographic patterns (explorers, tourists)")
            print("  temporal         - Seasonal trends (12-month coverage)")
            print("  tourist          - Intensive trip (multi-onsen days)")
            print("  local_regular    - Long-term local visitor")
            print("  integrated       - Custom HR coverage (specify --hr-coverage)")
            return

        logger.info(f"Generated {len(visits)} visits")

        # Convert to database models
        logger.info("Converting to database models...")
        db_visits = []

        for visit in visits:
            db_visit = OnsenVisit(
                onsen_id=visit.onsen_id,
                entry_fee_yen=visit.entry_fee_yen,
                payment_method=visit.payment_method,
                weather=visit.weather,
                time_of_day=visit.time_of_day,
                temperature_outside_celsius=visit.temperature_outside_celsius,
                visit_time=visit.visit_time,
                stay_length_minutes=visit.stay_length_minutes,
                visited_with=visit.visited_with,
                travel_mode=visit.travel_mode,
                travel_time_minutes=visit.travel_time_minutes,
                accessibility_rating=visit.accessibility_rating,
                exercise_before_onsen=visit.exercise_before_onsen,
                exercise_type=visit.exercise_type,
                exercise_length_minutes=visit.exercise_length_minutes,
                crowd_level=visit.crowd_level,
                view_rating=visit.view_rating,
                navigability_rating=visit.navigability_rating,
                cleanliness_rating=visit.cleanliness_rating,
                main_bath_type=visit.main_bath_type,
                main_bath_temperature=visit.main_bath_temperature,
                main_bath_water_type=visit.main_bath_water_type,
                water_color=visit.water_color,
                smell_intensity_rating=visit.smell_intensity_rating,
                changing_room_cleanliness_rating=visit.changing_room_cleanliness_rating,
                locker_availability_rating=visit.locker_availability_rating,
                had_soap=visit.had_soap,
                had_sauna=visit.had_sauna,
                had_outdoor_bath=visit.had_outdoor_bath,
                had_rest_area=visit.had_rest_area,
                rest_area_used=visit.rest_area_used,
                rest_area_rating=visit.rest_area_rating,
                had_food_service=visit.had_food_service,
                food_service_used=visit.food_service_used,
                food_quality_rating=visit.food_quality_rating,
                massage_chair_available=visit.massage_chair_available,
                sauna_visited=visit.sauna_visited,
                sauna_temperature=visit.sauna_temperature,
                sauna_steam=visit.sauna_steam,
                sauna_duration_minutes=visit.sauna_duration_minutes,
                sauna_rating=visit.sauna_rating,
                outdoor_bath_visited=visit.outdoor_bath_visited,
                outdoor_bath_temperature=visit.outdoor_bath_temperature,
                outdoor_bath_rating=visit.outdoor_bath_rating,
                pre_visit_mood=visit.pre_visit_mood,
                post_visit_mood=visit.post_visit_mood,
                energy_level_change=visit.energy_level_change,
                hydration_level=visit.hydration_level,
                previous_location=visit.previous_location,
                next_location=visit.next_location,
                multi_onsen_day=visit.multi_onsen_day,
                visit_order=visit.visit_order,
                atmosphere_rating=visit.atmosphere_rating,
                personal_rating=visit.personal_rating,
            )
            db_visits.append(db_visit)

        # Insert visits
        logger.info("Inserting visits into database...")
        db.add_all(db_visits)
        db.flush()  # Get IDs without committing

        # Insert heart rate data if available
        if hr_data:
            logger.info(f"Inserting {len(hr_data)} heart rate sessions...")
            db_hr_records = []

            for i, hr_session in enumerate(hr_data):
                # Link to corresponding visit
                db_hr = HeartRateData(
                    visit_id=db_visits[i].id,
                    recording_start=hr_session.start_time,
                    recording_end=hr_session.end_time,
                    average_heart_rate=int(hr_session.average_heart_rate),
                    min_heart_rate=int(hr_session.min_heart_rate),
                    max_heart_rate=int(hr_session.max_heart_rate),
                    total_recording_minutes=hr_session.duration_minutes,
                    data_points_count=hr_session.data_points_count,
                    notes=hr_session.notes,
                )
                db_hr_records.append(db_hr)

            db.add_all(db_hr_records)

        db.commit()

        # Show statistics
        logger.info("\n" + "="*50)
        logger.info("DATA GENERATION COMPLETE")
        logger.info("="*50)
        logger.info(f"Scenario: {scenario}")
        logger.info(f"Total visits: {len(db_visits)}")

        if hr_data:
            hr_coverage_pct = (len(hr_data) / len(db_visits)) * 100
            logger.info(f"Heart rate sessions: {len(hr_data)} ({hr_coverage_pct:.1f}% coverage)")

        # Rating statistics
        avg_rating = sum(v.personal_rating for v in db_visits) / len(db_visits)
        min_rating = min(v.personal_rating for v in db_visits)
        max_rating = max(v.personal_rating for v in db_visits)

        logger.info(f"\nRating statistics:")
        logger.info(f"  Average: {avg_rating:.1f}/10")
        logger.info(f"  Range: {min_rating}-{max_rating}")

        # Price statistics
        fees = [v.entry_fee_yen for v in db_visits]
        avg_fee = sum(fees) / len(fees)
        logger.info(f"\nEntry fee statistics:")
        logger.info(f"  Average: ¥{avg_fee:.0f}")
        logger.info(f"  Range: ¥{min(fees)}-¥{max(fees)}")

        # Date range
        dates = [v.visit_time for v in db_visits]
        logger.info(f"\nDate range:")
        logger.info(f"  From: {min(dates).strftime('%Y-%m-%d')}")
        logger.info(f"  To: {max(dates).strftime('%Y-%m-%d')}")
        logger.info(f"  Span: {(max(dates) - min(dates)).days} days")

        # Multi-onsen days
        multi_count = sum(1 for v in db_visits if v.multi_onsen_day)
        if multi_count > 0:
            logger.info(f"\nMulti-onsen visit days: {multi_count}")

        # Unique onsens visited
        unique_onsens = len(set(v.onsen_id for v in db_visits))
        logger.info(f"\nUnique onsens visited: {unique_onsens}/{onsen_count}")

        logger.info("\n" + "="*50)
        logger.info("Data is ready for analysis!")
        logger.info("="*50)

        if not args.quiet:
            print(f"\n✅ Successfully generated {len(db_visits)} visits")
            if hr_data:
                print(f"   + {len(hr_data)} heart rate sessions")

            print(f"\n📊 Ready to run analysis:")
            print(f"   onsendo analysis scenario overview")

            if scenario in ['econometric', 'comprehensive', 'pricing']:
                print(f"   onsendo analysis scenario enjoyment_drivers")
                print(f"   onsendo analysis scenario pricing_optimization")

            if scenario in ['spatial', 'comprehensive']:
                print(f"   onsendo analysis scenario spatial_analysis")

            if scenario in ['temporal', 'comprehensive']:
                print(f"   onsendo analysis scenario temporal_analysis")


def list_user_profiles(args: argparse.Namespace = None) -> None:
    """Display available user profiles."""
    print("\n" + "="*60)
    print("AVAILABLE USER PROFILES")
    print("="*60)

    for profile in ALL_PROFILES:
        print(f"\n{profile.name.upper()}")
        print(f"  {profile.description}")
        print(f"  Visits/month: {profile.visits_per_month:.1f}")
        print(f"  Price sensitivity: {profile.price_sensitivity:.1f}")
        print(f"  Max price: ¥{profile.max_acceptable_price}")
        print(f"  Experience seeking: {profile.experience_seeking:.1f}")
        print(f"  Health focused: {profile.health_focused:.1f}")

    print("\n" + "="*60)


def show_scenario_info(args: argparse.Namespace) -> None:
    """Display detailed information about a scenario."""
    scenario = args.scenario
    scenarios = {
        'comprehensive': {
            'name': 'Comprehensive Analysis-Ready Dataset',
            'description': 'Mix of all user profiles with realistic correlations',
            'features': [
                'Equal mix of all 8 user profiles',
                'Seasonal effects and weather correlations',
                'Price-quality relationships',
                'Learning effects over time',
                '~5% realistic missing data',
            ],
            'ideal_for': ['Overview analysis', 'All-around testing', 'Feature exploration'],
            'default_size': 100,
        },
        'econometric': {
            'name': 'Econometric Test Dataset',
            'description': 'Optimized for regression and causal analysis',
            'features': [
                'Strong price-quality correlations',
                'Clear seasonal patterns',
                'Profile-based heterogeneity',
                'Sufficient variation for regression',
                'Quality Seekers + Budget Travelers dominant',
            ],
            'ideal_for': ['Enjoyment drivers analysis', 'Pricing optimization', 'Causal inference'],
            'default_size': 200,
        },
        'heart_rate': {
            'name': 'Heart Rate Analysis Dataset',
            'description': 'Visits with integrated physiological data',
            'features': [
                '85% heart rate coverage',
                'Health Enthusiast profiles dominant (60%)',
                'Temperature-HR correlations',
                'Sauna effects on HR',
                'Exercise variation',
            ],
            'ideal_for': ['Physiological impact analysis', 'Health benefits research', 'HR-rating correlations'],
            'default_size': 150,
        },
        'pricing': {
            'name': 'Pricing Analysis Dataset',
            'description': 'Price-quality tradeoffs and value optimization',
            'features': [
                'Wide price range (¥100-¥1500)',
                'Quality Seekers vs Budget Travelers',
                'Clear price-quality correlations',
                'Good sample size at each price tier',
            ],
            'ideal_for': ['Price elasticity', 'Value for money analysis', 'Market segmentation'],
            'default_size': 200,
        },
        'spatial': {
            'name': 'Spatial Analysis Dataset',
            'description': 'Geographic patterns and exploration behavior',
            'features': [
                'Explorers and Tourists dominant',
                'Wide geographic coverage',
                'Multi-onsen day patterns',
                'Travel mode variation',
            ],
            'ideal_for': ['Geographic clustering', 'Travel pattern analysis', 'Spatial correlations'],
            'default_size': 150,
        },
        'temporal': {
            'name': 'Temporal Analysis Dataset',
            'description': 'Long-term seasonal and trend patterns',
            'features': [
                '12-month full year coverage',
                'Local Regular profiles (consistent visitors)',
                'Clear seasonal effects',
                'Learning curves (improving ratings)',
                'Day of week patterns',
            ],
            'ideal_for': ['Seasonal analysis', 'Trend detection', 'Time series analysis'],
            'default_size': 250,
        },
        'tourist': {
            'name': 'Tourist Scenario',
            'description': 'Intensive short-term tourist trip',
            'features': [
                '7-day default trip',
                'Multiple onsens per day',
                'Tourist profile behavior',
                'Complete data (no missing values)',
                'High rating variance',
            ],
            'ideal_for': ['Multi-onsen day analysis', 'Tourist behavior', 'Intensive patterns'],
            'default_size': 21,
        },
        'local_regular': {
            'name': 'Local Regular Scenario',
            'description': 'Long-term loyal local visitor',
            'features': [
                '12-month pattern',
                'High visit frequency (~12/month)',
                'Favorite onsen loyalty',
                'Consistent behavior',
                'Gradual learning effects',
            ],
            'ideal_for': ['Loyalty analysis', 'Long-term health tracking', 'Habit formation'],
            'default_size': 144,
        },
        'integrated': {
            'name': 'Integrated Dataset (Custom HR Coverage)',
            'description': 'Flexible visits + heart rate with configurable coverage',
            'features': [
                'Configurable HR coverage (--hr-coverage)',
                'Mix of all profiles',
                'Realistic correlations',
                'Profile-adjusted HR tracking probability',
            ],
            'ideal_for': ['Custom HR analysis', 'Flexible testing', 'Coverage experiments'],
            'default_size': 100,
        },
    }

    if scenario not in scenarios:
        print(f"Unknown scenario: {scenario}")
        return

    info = scenarios[scenario]

    print("\n" + "="*70)
    print(info['name'].upper())
    print("="*70)
    print(f"\n{info['description']}")
    print(f"\nDefault size: {info['default_size']} visits")

    print("\nKey features:")
    for feature in info['features']:
        print(f"  • {feature}")

    print("\nIdeal for:")
    for use_case in info['ideal_for']:
        print(f"  ✓ {use_case}")

    print("\n" + "="*70)
