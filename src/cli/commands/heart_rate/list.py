"""
List and manage heart rate data records.
"""

import argparse

from src.lib.heart_rate_manager import HeartRateDataManager
from src.db.conn import get_db
from src.db.models import HeartRateData, OnsenVisit
from src.config import get_database_config


def list_heart_rate_data(args: argparse.Namespace) -> int:
    """List heart rate data records."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    try:
        linked_only = args.linked_only
        unlinked_only = args.unlinked_only
        visit_id = args.visit_id
        show_details = args.details

        with get_db(url=config.url) as db:
            manager = HeartRateDataManager(db)

            if visit_id:
                # Show heart rate data for specific visit
                records = manager.get_by_visit(visit_id)
                if not records:
                    print(f"❌ No heart rate data found for visit {visit_id}")
                    return 0
                print(f"💓 Heart rate data for visit {visit_id}:")
            elif linked_only:
                # Show only linked records
                records = (
                    db.query(HeartRateData)
                    .filter(HeartRateData.visit_id.isnot(None))
                    .all()
                )
                print("🔗 Linked heart rate data records:")
            elif unlinked_only:
                # Show only unlinked records
                records = (
                    db.query(HeartRateData)
                    .filter(HeartRateData.visit_id.is_(None))
                    .all()
                )
                print("🔓 Unlinked heart rate data records:")
            else:
                # Show all records
                records = db.query(HeartRateData).all()
                print("💓 All heart rate data records:")

            if not records:
                print("   No records found.")
                return 0

            # Sort by recording start time (newest first)
            records.sort(key=lambda x: x.recording_start, reverse=True)

            # Apply limit if specified
            if hasattr(args, 'limit') and args.limit is not None:
                records = records[:args.limit]

            for record in records:
                print(f"\n📊 Record ID: {record.id}")
                print(
                    f"   🕐 Recording: {record.recording_start.strftime('%Y-%m-%d %H:%M')} - {record.recording_end.strftime('%H:%M')}"
                )
                print(f"   📈 Duration: {record.total_recording_minutes} minutes")
                print(
                    f"   💓 HR: {record.average_heart_rate:.1f} avg, {record.min_heart_rate:.1f}-{record.max_heart_rate:.1f} range"
                )
                print(f"   📊 Data points: {record.data_points_count}")
                print(f"   📁 Format: {record.data_format}")
                print(f"   📂 File: {record.data_file_path}")

                if record.visit_id:
                    print(f"   🔗 Linked to visit: {record.visit_id}")
                else:
                    print(f"   🔓 Not linked to any visit")

                if record.notes:
                    print(f"   📝 Notes: {record.notes}")

                if show_details:
                    # Validate file integrity
                    is_valid = manager.validate_file_integrity(record.id)
                    status = "✅" if is_valid else "❌"
                    print(f"   🔍 File integrity: {status}")

        return 0

    except Exception as e:
        print(f"❌ Error listing heart rate data: {e}")
        return 1


def link_heart_rate_to_visit(args: argparse.Namespace) -> int:
    """Link heart rate data to an onsen visit."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    try:
        heart_rate_id = args.heart_rate_id
        visit_id = args.visit_id_link

        print(f"🔗 Linking heart rate data {heart_rate_id} to visit {visit_id}...")

        with get_db(url=config.url) as db:
            # Check if heart rate record exists
            heart_rate_record = (
                db.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not heart_rate_record:
                print(f"❌ Heart rate record {heart_rate_id} not found")
                return 1

            # Check if visit exists
            visit_record = db.query(OnsenVisit).filter_by(id=visit_id).first()
            if not visit_record:
                print(f"❌ Visit {visit_id} not found")
                return 1

            # Link them
            heart_rate_record.visit_id = visit_id
            db.commit()
            print("✅ Successfully linked heart rate data to visit")
            return 0

    except Exception as e:
        print(f"❌ Error linking heart rate data: {e}")
        return 1


def unlink_heart_rate_from_visit(args: argparse.Namespace) -> int:
    """Unlink heart rate data from its visit."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    try:
        heart_rate_id = args.heart_rate_id

        print(f"🔓 Unlinking heart rate data {heart_rate_id} from visit...")

        with get_db(url=config.url) as db:
            # Check if heart rate record exists
            heart_rate_record = (
                db.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not heart_rate_record:
                print(f"❌ Heart rate record {heart_rate_id} not found")
                return 1

            if not heart_rate_record.visit_id:
                print(
                    f"❌ Heart rate record {heart_rate_id} is not linked to any visit"
                )
                return 1

            # Unlink it
            heart_rate_record.visit_id = None
            db.commit()
            print("✅ Successfully unlinked heart rate data from visit")
            return 0

    except Exception as e:
        print(f"❌ Error unlinking heart rate data: {e}")
        return 1


def delete_heart_rate_record(args: argparse.Namespace) -> int:
    """Delete a heart rate record."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    try:
        heart_rate_id = args.heart_rate_id
        force = args.force

        # Get record details
        with get_db(url=config.url) as db:
            record = db.query(HeartRateData).filter_by(id=heart_rate_id).first()

        if not record:
            print(f"❌ Heart rate record {heart_rate_id} not found")
            return 1

        print(f"🗑️  Deleting heart rate record {heart_rate_id}:")
        print(
            f"   📊 Recording: {record.recording_start.strftime('%Y-%m-%d %H:%M')} - {record.recording_end.strftime('%H:%M')}"
        )
        print(f"   💓 Average HR: {record.average_heart_rate:.1f} BPM")
        print(f"   📁 File: {record.data_file_path}")

        if record.visit_id:
            print(f"   ⚠️  This record is linked to visit {record.visit_id}")

        if not force:
            response = input(
                "\n❓ Are you sure you want to delete this record? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("❌ Deletion cancelled.")
                return 0

        # Delete the record using the manager
        with get_db(url=config.url) as db:
            manager = HeartRateDataManager(db)
            if manager.delete_record(heart_rate_id):
                print("✅ Successfully deleted heart rate record")
                return 0
            else:
                print("❌ Failed to delete record")
                return 1

    except Exception as e:
        print(f"❌ Error deleting heart rate record: {e}")
        return 1
