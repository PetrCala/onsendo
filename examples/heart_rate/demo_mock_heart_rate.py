#!/usr/bin/env python3
"""
Demonstration of the mock heart rate data system.

This script shows how to generate realistic mock heart rate data
and export it in various formats including Apple Health CSV.
"""

from datetime import datetime, timedelta
from src.testing.mocks.mock_heart_rate_data import (
    create_single_session,
    create_workout_session,
    create_sleep_session,
    create_daily_sessions,
    create_realistic_scenario,
)


def main():
    """Demonstrate the mock heart rate data system."""
    print("🏃‍♂️ Mock Heart Rate Data System Demo")
    print("=" * 50)

    # 1. Create a simple resting session
    print("\n1. Creating a resting session...")
    resting_session = create_single_session("resting", duration_minutes=30)
    print(f"   Duration: {resting_session.duration_minutes} minutes")
    print(f"   Data points: {resting_session.data_points_count}")
    print(
        f"   Heart rate: {resting_session.min_heart_rate}-{resting_session.max_heart_rate} BPM"
    )
    print(f"   Average: {resting_session.average_heart_rate:.1f} BPM")

    # Export to CSV
    csv_file = "examples/heart_rate/resting_session.csv"
    resting_session.export_csv(csv_file)
    print(f"   Exported to: {csv_file}")

    # 2. Create a workout session
    print("\n2. Creating a workout session...")
    workout_session = create_workout_session()
    print(f"   Duration: {workout_session.duration_minutes} minutes")
    print(f"   Data points: {workout_session.data_points_count}")
    print(
        f"   Heart rate: {workout_session.min_heart_rate}-{workout_session.max_heart_rate} BPM"
    )
    print(f"   Average: {workout_session.average_heart_rate:.1f} BPM")

    # Export to Apple Health format
    apple_health_file = "examples/heart_rate/workout_apple_health.csv"
    workout_session.export_apple_health_format(apple_health_file)
    print(f"   Exported to Apple Health format: {apple_health_file}")

    # 3. Create a sleep session
    print("\n3. Creating a sleep session...")
    sleep_session = create_sleep_session()
    print(f"   Duration: {sleep_session.duration_minutes} minutes")
    print(f"   Data points: {sleep_session.data_points_count}")
    print(
        f"   Heart rate: {sleep_session.min_heart_rate}-{sleep_session.max_heart_rate} BPM"
    )
    print(f"   Average: {sleep_session.average_heart_rate:.1f} BPM")

    # Export to JSON
    json_file = "examples/heart_rate/sleep_session.json"
    sleep_session.export_json(json_file)
    print(f"   Exported to: {json_file}")

    # 4. Create daily sessions
    print("\n4. Creating daily sessions...")
    daily_sessions = create_daily_sessions(num_sessions=4)
    print(f"   Created {len(daily_sessions)} sessions for the day")

    for i, session in enumerate(daily_sessions, 1):
        print(
            f"   Session {i}: {session.duration_minutes} min, "
            f"HR {session.min_heart_rate}-{session.max_heart_rate} BPM"
        )

    # Export all daily sessions to text
    text_file = "examples/heart_rate/daily_sessions.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        for i, session in enumerate(daily_sessions, 1):
            f.write(f"=== Session {i} ===\n")
            f.write(f"Duration: {session.duration_minutes} minutes\n")
            f.write(
                f"Heart Rate: {session.min_heart_rate}-{session.max_heart_rate} BPM\n"
            )
            f.write(f"Average: {session.average_heart_rate:.1f} BPM\n")
            f.write(f"Notes: {session.notes}\n\n")

    print(f"   Exported daily summary to: {text_file}")

    # 5. Create realistic scenarios
    print("\n5. Creating realistic scenarios...")

    # Mixed scenario (daily + workout)
    mixed_scenario = create_realistic_scenario("mixed", num_sessions=3)
    print(f"   Mixed scenario: {len(mixed_scenario)} sessions")

    # Export mixed scenario to Apple Health
    mixed_apple_health = "examples/heart_rate/mixed_scenario_apple_health.csv"
    for i, session in enumerate(mixed_scenario):
        if i == 0:  # First session
            session.export_apple_health_format(mixed_apple_health)
        else:
            # Append to the same file
            with open(mixed_apple_health, "a", newline="", encoding="utf-8") as f:
                import csv

                writer = csv.writer(f)
                # Get batches of data points
                batch_size = 10
                for j in range(0, len(session.data_points), batch_size):
                    batch = session.data_points[j : j + batch_size]
                    if not batch:
                        continue

                    batch_start_time = batch[0][0]
                    hr_values = [str(point[1]) for point in batch]
                    hr_data = ";".join(hr_values)

                    writer.writerow(
                        [
                            "HEART_RATE",
                            session.sample_rate_hz,
                            batch_start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                            hr_data,
                        ]
                    )

    print(f"   Exported mixed scenario to: {mixed_apple_health}")

    # 6. Create additional sample files for documentation
    print("\n6. Creating additional sample files...")

    # Create a simple Apple Health sample file
    apple_health_sample = "examples/heart_rate/apple_health_sample.csv"
    with open(apple_health_sample, "w", newline="", encoding="utf-8") as f:
        import csv

        writer = csv.writer(f)
        writer.writerow(["SampleType", "SampleRate", "StartTime", "Data"])

        # Create a simple example with increasing heart rate
        base_time = datetime.now().replace(hour=15, minute=24, second=12, microsecond=0)
        for i in range(5):
            timestamp = base_time + timedelta(minutes=i)
            hr_values = [
                str(70 + i * 2 + j) for j in range(9)
            ]  # Simple increasing pattern
            hr_data = ";".join(hr_values)
            writer.writerow(
                ["HEART_RATE", 1, timestamp.strftime("%Y-%m-%dT%H:%M:%S.000Z"), hr_data]
            )
    print(f"   Created Apple Health sample: {apple_health_sample}")

    # Create a standard CSV sample file
    csv_sample = "examples/heart_rate/heart_rate_sample.csv"
    with open(csv_sample, "w", newline="", encoding="utf-8") as f:
        import csv

        writer = csv.writer(f)
        writer.writerow(["timestamp", "heart_rate", "confidence"])

        # Create a simple example with realistic heart rate data
        base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        for i in range(20):  # 20 data points
            timestamp = base_time + timedelta(minutes=i)
            heart_rate = 70 + int(10 * (i % 3))  # Varying pattern
            confidence = 0.85 + (i % 3) * 0.05
            writer.writerow(
                [
                    timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    heart_rate,
                    f"{confidence:.3f}",
                ]
            )
    print(f"   Created standard CSV sample: {csv_sample}")

    # Create a mock sleep session in Apple Health format
    mock_sleep_apple_health = "examples/heart_rate/mock_sleep_apple_health.csv"
    sleep_session.export_apple_health_format(mock_sleep_apple_health)
    print(f"   Created mock sleep Apple Health: {mock_sleep_apple_health}")

    print("\n📝 Note: The sample files above are for documentation purposes only.")
    print("   For actual import testing, use the main generated files:")
    print("   - resting_session.csv")
    print("   - workout_apple_health.csv")
    print("   - sleep_session.json")
    print("   - daily_sessions.txt")
    print("   - mixed_scenario_apple_health.csv")

    print(
        "\n✅ Demo completed! Check the 'examples/heart_rate/' directory for generated files."
    )
    print("\n📊 Summary of generated data:")
    print(f"   - Resting session: {resting_session.data_points_count} points")
    print(f"   - Workout session: {workout_session.data_points_count} points")
    print(f"   - Sleep session: {sleep_session.data_points_count} points")
    print(
        f"   - Daily sessions: {sum(s.data_points_count for s in daily_sessions)} total points"
    )
    print(
        f"   - Mixed scenario: {sum(s.data_points_count for s in mixed_scenario)} total points"
    )


if __name__ == "__main__":
    main()
