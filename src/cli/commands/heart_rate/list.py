"""
List and manage heart rate data records.
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

from src.lib.heart_rate_manager import HeartRateDataManager
from src.db.conn import get_db
from src.db.models import HeartRateData, OnsenVisit
from src.const import CONST


def list_heart_rate_data(
    linked_only: bool = False,
    unlinked_only: bool = False,
    visit_id: Optional[int] = None,
    show_details: bool = False,
) -> int:
    """List heart rate data records."""
    try:
        manager = HeartRateDataManager()

        if visit_id:
            # Show heart rate data for specific visit
            records = manager.get_by_visit(visit_id)
            if not records:
                print(f"❌ No heart rate data found for visit {visit_id}")
                return 0
            print(f"💓 Heart rate data for visit {visit_id}:")
        elif linked_only:
            # Show only linked records
            with get_db(CONST.DATABASE_URL) as db:
                records = (
                    db.query(HeartRateData)
                    .filter(HeartRateData.visit_id.isnot(None))
                    .all()
                )
            print("🔗 Linked heart rate data records:")
        elif unlinked_only:
            # Show only unlinked records
            with get_db(CONST.DATABASE_URL) as db:
                records = (
                    db.query(HeartRateData)
                    .filter(HeartRateData.visit_id.is_(None))
                    .all()
                )
            print("🔓 Unlinked heart rate data records:")
        else:
            # Show all records
            with get_db(CONST.DATABASE_URL) as db:
                records = db.query(HeartRateData).all()
            print("💓 All heart rate data records:")

        if not records:
            print("   No records found.")
            return 0

        # Sort by recording start time (newest first)
        records.sort(key=lambda x: x.recording_start, reverse=True)

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


def list_heart_rate_data_cli(args: argparse.Namespace) -> int:
    """CLI wrapper for list_heart_rate_data that accepts argparse.Namespace."""
    return list_heart_rate_data(
        linked_only=args.linked_only,
        unlinked_only=args.unlinked_only,
        visit_id=args.visit_id,
        show_details=args.details,
    )


def link_heart_rate_to_visit(heart_rate_id: int, visit_id: int) -> int:
    """Link heart rate data to an onsen visit."""
    try:
        manager = HeartRateDataManager()

        print(f"🔗 Linking heart rate data {heart_rate_id} to visit {visit_id}...")

        if manager.link_to_visit(heart_rate_id, visit_id):
            print("✅ Successfully linked heart rate data to visit")
            return 0
        else:
            print("❌ Failed to link heart rate data to visit")
            return 1

    except Exception as e:
        print(f"❌ Error linking heart rate data: {e}")
        return 1


def link_heart_rate_to_visit_cli(args: argparse.Namespace) -> int:
    """CLI wrapper for link_heart_rate_to_visit that accepts argparse.Namespace."""
    return link_heart_rate_to_visit(args.heart_rate_id, args.visit_id_link)


def unlink_heart_rate_from_visit(heart_rate_id: int) -> int:
    """Unlink heart rate data from its visit."""
    try:
        manager = HeartRateDataManager()

        print(f"🔓 Unlinking heart rate data {heart_rate_id} from visit...")

        if manager.unlink_from_visit(heart_rate_id):
            print("✅ Successfully unlinked heart rate data from visit")
            return 0
        else:
            print("❌ Failed to unlink heart rate data from visit")
            return 1

    except Exception as e:
        print(f"❌ Error unlinking heart rate data: {e}")
        return 1


def unlink_heart_rate_from_visit_cli(args: argparse.Namespace) -> int:
    """CLI wrapper for unlink_heart_rate_from_visit that accepts argparse.Namespace."""
    return unlink_heart_rate_from_visit(args.heart_rate_id)


def delete_heart_rate_record(heart_rate_id: int, force: bool = False) -> int:
    """Delete a heart rate record."""
    try:
        manager = HeartRateDataManager()

        # Get record details
        db_session = get_db()
        record = db_session.query(HeartRateData).filter_by(id=heart_rate_id).first()

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

        if manager.delete_record(heart_rate_id):
            print("✅ Successfully deleted heart rate record")
            return 0
        else:
            print("❌ Failed to delete heart rate record")
            return 1

    except Exception as e:
        print(f"❌ Error deleting heart rate record: {e}")
        return 1


def delete_heart_rate_record_cli(args: argparse.Namespace) -> int:
    """CLI wrapper for delete_heart_rate_record that accepts argparse.Namespace."""
    return delete_heart_rate_record(args.heart_rate_id, args.force)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="List and manage heart rate data records",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List heart rate data records")
    list_parser.add_argument(
        "--linked-only",
        "-l",
        action="store_true",
        help="Show only records linked to visits",
    )
    list_parser.add_argument(
        "--unlinked-only",
        "-u",
        action="store_true",
        help="Show only records not linked to visits",
    )
    list_parser.add_argument(
        "--visit-id", "-v", type=int, help="Show heart rate data for specific visit ID"
    )
    list_parser.add_argument(
        "--details",
        "-d",
        action="store_true",
        help="Show detailed information including file integrity",
    )

    # Link command
    link_parser = subparsers.add_parser("link", help="Link heart rate data to a visit")
    link_parser.add_argument("heart_rate_id", type=int, help="Heart rate record ID")
    link_parser.add_argument("visit_id", type=int, help="Visit ID to link to")

    # Unlink command
    unlink_parser = subparsers.add_parser(
        "unlink", help="Unlink heart rate data from its visit"
    )
    unlink_parser.add_argument("heart_rate_id", type=int, help="Heart rate record ID")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a heart rate record")
    delete_parser.add_argument("heart_rate_id", type=int, help="Heart rate record ID")
    delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Force deletion without confirmation"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "list":
        return list_heart_rate_data(
            linked_only=args.linked_only,
            unlinked_only=args.unlinked_only,
            visit_id=args.visit_id,
            show_details=args.details,
        )
    elif args.command == "link":
        return link_heart_rate_to_visit(args.heart_rate_id, args.visit_id)
    elif args.command == "unlink":
        return unlink_heart_rate_from_visit(args.heart_rate_id)
    elif args.command == "delete":
        return delete_heart_rate_record(args.heart_rate_id, args.force)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
