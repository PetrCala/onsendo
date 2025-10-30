"""
Show weight statistics and trends.
"""

import argparse
from datetime import datetime, timedelta

from src.lib.weight_manager import WeightDataManager
from src.db.conn import get_db
from src.config import get_database_config


def show_weight_stats(args: argparse.Namespace) -> int:
    """Show weight statistics for a time period."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    try:
        week = args.week if hasattr(args, "week") else None
        month = args.month if hasattr(args, "month") else None
        year = args.year if hasattr(args, "year") else datetime.now().year
        all_time = args.all_time if hasattr(args, "all_time") else False

        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)

            # Determine date range
            if week:
                # Parse week start date
                week_start = datetime.strptime(week, "%Y-%m-%d")
                week_end = week_start + timedelta(days=7)
                period_name = f"Week of {week}"
            elif month:
                # Month stats
                month_start = datetime(year, month, 1)
                if month == 12:
                    month_end = datetime(year + 1, 1, 1)
                else:
                    month_end = datetime(year, month + 1, 1)
                week_start = month_start
                week_end = month_end
                period_name = f"{month_start.strftime('%B %Y')}"
            elif all_time:
                # All time stats
                week_start = None
                week_end = None
                period_name = "All Time"
            else:
                print("❌ Please specify either --week, --month, or --all-time")
                return 1

            # Get summary
            summary = manager.get_summary(start_date=week_start, end_date=week_end)

            if not summary:
                print(f"❌ No weight measurements found for {period_name}")
                return 0

            # Display statistics
            print(f"📊 Weight Statistics - {period_name}")
            print("=" * 60)
            print(f"\n📈 Total Measurements: {summary.total_measurements}")

            print(f"\n⚖️  Weight Summary:")
            print(f"   Average: {summary.avg_weight_kg} kg")
            print(f"   Minimum: {summary.min_weight_kg} kg")
            print(f"   Maximum: {summary.max_weight_kg} kg")
            print(f"   Range: {summary.max_weight_kg - summary.min_weight_kg:.1f} kg")

            # Weight change
            change_emoji = "📉" if summary.weight_change_kg < 0 else "📈" if summary.weight_change_kg > 0 else "➡️"
            change_sign = "+" if summary.weight_change_kg > 0 else ""
            print(
                f"\n{change_emoji} Weight Change: {change_sign}{summary.weight_change_kg} kg "
                f"({summary.trend})"
            )

            # Moving averages
            if summary.moving_avg_7day:
                print(f"\n📊 7-Day Moving Average: {summary.moving_avg_7day} kg")

            if summary.moving_avg_30day:
                print(f"📊 30-Day Moving Average: {summary.moving_avg_30day} kg")

            # Measurements by source
            if summary.measurements_by_source:
                print(f"\n📋 Measurements by Source:")
                for source, count in sorted(
                    summary.measurements_by_source.items(), key=lambda x: x[1], reverse=True
                ):
                    percentage = (count / summary.total_measurements) * 100
                    print(f"   • {source}: {count} ({percentage:.1f}%)")

            # Trend analysis
            print(f"\n📈 Trend Analysis:")
            print("=" * 60)

            if summary.trend == "losing":
                print("✅ Trend: Losing weight")
                if summary.weight_change_kg < -5:
                    print("   ⚠️  Significant weight loss detected")
                elif summary.weight_change_kg < -2:
                    print("   📉 Moderate weight loss")
                else:
                    print("   📉 Gradual weight loss")
            elif summary.trend == "gaining":
                print("📈 Trend: Gaining weight")
                if summary.weight_change_kg > 5:
                    print("   ⚠️  Significant weight gain detected")
                elif summary.weight_change_kg > 2:
                    print("   📈 Moderate weight gain")
                else:
                    print("   📈 Gradual weight gain")
            else:
                print("➡️  Trend: Stable weight")
                print("   ✅ Weight is relatively stable")

            # Recommendations
            print(f"\n💡 Recommendations:")
            print("=" * 60)

            if summary.total_measurements < 7:
                print(
                    "   📝 Track weight consistently for at least 7 days to see meaningful trends"
                )
            elif summary.total_measurements < 30:
                print(
                    "   📝 Continue tracking for 30 days for more accurate moving averages"
                )

            # Weigh-in frequency
            if week_start and week_end:
                days_in_period = (week_end - week_start).days
                measurements_per_day = summary.total_measurements / days_in_period
                if measurements_per_day < 0.5:
                    print(
                        "   📅 Consider weighing yourself more frequently "
                        "(ideally daily, same time each morning)"
                    )
                elif measurements_per_day > 2:
                    print(
                        "   ⚠️  You're weighing yourself very frequently "
                        "(once daily is sufficient)"
                    )

            # Consistency check
            if summary.measurements_by_source:
                if len(summary.measurements_by_source) > 2:
                    print(
                        "   📊 Multiple measurement sources detected. "
                        "Use the same scale for consistency"
                    )

        return 0

    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
