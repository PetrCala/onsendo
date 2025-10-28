"""Interactive map generator for onsen recommendations using Folium."""

import os
from datetime import datetime
from pathlib import Path
import folium
from folium import IFrame
from loguru import logger

from sqlalchemy.orm import Session
from src.db.models import Onsen, Location, OnsenVisit
from src.paths import PATHS
from src.lib.utils import generate_google_maps_link
from src.lib.apple_reminders import (
    generate_reminder_script,
    is_reminders_available,
    format_onsen_details_for_reminder
)


def generate_recommendation_map(
    recommendations: list[tuple[Onsen, float, dict]],
    location: Location,
    output_filename: str | None = None,
    target_time: datetime | None = None,
) -> str:
    """
    Generate an interactive HTML map showing recommended onsens.

    Args:
        recommendations: List of tuples (onsen, distance_km, metadata)
        location: User's location (used as map center)
        output_filename: Optional filename for the map (default: timestamped)
        target_time: Optional target time for onsen visit (enables reminder button)

    Returns:
        Absolute path to the generated HTML file
    """
    # Ensure maps directory exists
    os.makedirs(PATHS.MAPS_DIR, exist_ok=True)

    # Generate filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"onsen_recommendations_{timestamp}.html"

    output_path = os.path.join(PATHS.MAPS_DIR, output_filename)

    # Create map centered on user's location
    center_lat = location.latitude or 33.2794  # Default to Beppu
    center_lon = location.longitude or 131.5006

    # Create the map with a nice tile layer
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    # Add user location marker
    folium.Marker(
        location=[center_lat, center_lon],
        popup=f"<b>{location.name}</b><br>Your Location",
        tooltip=f"{location.name} (Your Location)",
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(m)

    # Add onsen markers
    for i, (onsen, distance, metadata) in enumerate(recommendations, 1):
        if onsen.latitude is None or onsen.longitude is None:
            continue

        # Prepare tooltip text (shown on hover)
        tooltip_text = f"{i}. {onsen.name}"

        # Prepare popup HTML (shown on click) with all onsen details
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 300px;">
            <h3 style="margin-top: 0; color: #2c3e50;">{i}. {onsen.name}</h3>
            <hr style="margin: 10px 0;">

            <p style="margin: 5px 0;">
                <b>Ban Number:</b> {onsen.ban_number or 'N/A'}
            </p>

            <p style="margin: 5px 0;">
                <b>Distance:</b> {distance:.1f} km ({metadata['distance_category']})
            </p>

            <p style="margin: 5px 0;">
                <b>Coordinates:</b> {onsen.latitude:.6f}, {onsen.longitude:.6f}
            </p>

            <p style="margin: 5px 0;">
                <b>Address:</b> {onsen.address or 'N/A'}
            </p>

            {f'<p style="margin: 5px 0;"><b>Hours:</b> {onsen.usage_time}</p>' if onsen.usage_time else ''}

            {f'<p style="margin: 5px 0;"><b>Closed Days:</b> {onsen.closed_days}</p>' if onsen.closed_days else ''}

            {f'<p style="margin: 5px 0;"><b>Admission Fee:</b> {onsen.admission_fee}</p>' if onsen.admission_fee else ''}

            <p style="margin: 5px 0;">
                <b>Available:</b> {'Yes' if metadata['is_available'] else 'No'}
            </p>

            <p style="margin: 5px 0;">
                <b>Visited:</b> {'Yes' if metadata['has_been_visited'] else 'No'}
            </p>

            {'<p style="margin: 5px 0;"><b>Stay Restricted:</b> Yes</p>' if metadata['stay_restricted'] else ''}

            {f'<p style="margin: 5px 0;"><b>Stay Notes:</b><br>{"<br>".join(metadata["stay_restriction_notes"])}</p>' if metadata.get("stay_restriction_notes") else ""}

            {f'<p style="margin: 5px 0;"><b>Remarks:</b> {onsen.remarks}</p>' if onsen.remarks else ''}

            <hr style="margin: 10px 0;">

            <p style="margin: 5px 0;">
                <a href="{metadata['google_maps_link']}" target="_blank" style="color: #3498db;">
                    Open in Google Maps
                </a>
            </p>
        </div>
        """

        # Determine marker color based on visit status and availability
        if metadata["has_been_visited"]:
            color = "green"
            icon = "check"
        elif not metadata["is_available"]:
            color = "orange"
            icon = "clock"
        elif metadata["stay_restricted"]:
            color = "purple"
            icon = "bed"
        else:
            color = "blue"
            icon = "tint"

        # Create popup with iframe for proper rendering
        iframe = IFrame(html=popup_html, width=320, height=400)
        popup = folium.Popup(iframe, max_width=320)

        # Add marker to map
        folium.Marker(
            location=[onsen.latitude, onsen.longitude],
            popup=popup,
            tooltip=tooltip_text,
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(m)

    # Add legend
    legend_html = """
    <div style="position: fixed;
                bottom: 50px;
                right: 50px;
                width: 200px;
                background-color: white;
                border: 2px solid grey;
                z-index: 9999;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin-top: 0;">Legend</h4>
        <p style="margin: 5px 0;">
            <i class="fa fa-home" style="color: red;"></i> Your Location
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-tint" style="color: blue;"></i> Available Onsen
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-check" style="color: green;"></i> Visited Onsen
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-clock" style="color: orange;"></i> Currently Closed
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-bed" style="color: purple;"></i> Stay Restricted
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Generate reminder script and add button if target_time is provided
    reminder_script_path = None
    if target_time and is_reminders_available():
        try:
            # Generate script filename based on map filename
            script_filename = output_filename.replace('.html', '.command')
            reminder_script_path = os.path.join(PATHS.MAPS_DIR, script_filename)

            # Format reminder title
            time_str = target_time.strftime("%H:%M")
            reminder_title = f"Onsen recommendation {time_str}"

            # Format reminder body with onsen details
            reminder_body = format_onsen_details_for_reminder(
                recommendations=recommendations,
                location_name=location.name
            )

            # Generate the .command script with body
            generate_reminder_script(reminder_title, target_time, reminder_script_path, body=reminder_body)

            # Add reminder button to the map
            # Convert to file:// URI for the button link
            script_uri = Path(reminder_script_path).as_uri()

            reminder_button_html = f"""
            <div style="position: fixed;
                        top: 80px;
                        right: 10px;
                        z-index: 9999;">
                <a href="{script_uri}"
                   style="display: block;
                          padding: 12px 20px;
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          text-decoration: none;
                          border-radius: 8px;
                          font-size: 14px;
                          font-weight: bold;
                          font-family: Arial, sans-serif;
                          box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                          text-align: center;
                          transition: all 0.3s ease;">
                    <i class="fa fa-bell" style="margin-right: 8px;"></i>Create Reminder
                </a>
                <div style="margin-top: 8px;
                           padding: 8px;
                           background-color: white;
                           border: 1px solid #ddd;
                           border-radius: 5px;
                           font-size: 11px;
                           color: #666;
                           text-align: center;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {reminder_title}
                </div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(reminder_button_html))

        except (OSError, ValueError) as e:
            # Log error but don't fail map generation
            logger.warning(f"Failed to generate reminder script: {e}")

    # Save map
    m.save(output_path)

    return output_path


def generate_all_onsens_map(
    onsens: list[Onsen],
    db_session: Session,
    output_filename: str | None = None,
) -> str:
    """
    Generate an interactive HTML map showing all onsens in the database.

    Args:
        onsens: List of all onsens to display
        db_session: Database session to query visit status
        output_filename: Optional filename for the map (default: timestamped)

    Returns:
        Absolute path to the generated HTML file
    """
    # Ensure maps directory exists
    os.makedirs(PATHS.MAPS_DIR, exist_ok=True)

    # Generate filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"all_onsens_map_{timestamp}.html"

    output_path = os.path.join(PATHS.MAPS_DIR, output_filename)

    # Get visited onsen IDs
    visited_onsen_ids = set()
    try:
        visited_rows = db_session.query(OnsenVisit.onsen_id).distinct().all()
        visited_onsen_ids = {
            row[0] if isinstance(row, tuple) else row.onsen_id for row in visited_rows
        }
    except Exception:
        # If there's an error querying visits, just continue without visit info
        pass

    # Calculate center point from all onsens with coordinates
    onsens_with_coords = [o for o in onsens if o.latitude and o.longitude]
    if onsens_with_coords:
        avg_lat = sum(o.latitude for o in onsens_with_coords) / len(onsens_with_coords)
        avg_lon = sum(o.longitude for o in onsens_with_coords) / len(onsens_with_coords)
    else:
        # Default to Beppu center
        avg_lat = 33.2794
        avg_lon = 131.5006

    # Create the map
    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    # Add onsen markers
    for i, onsen in enumerate(onsens, 1):
        if onsen.latitude is None or onsen.longitude is None:
            continue

        # Prepare tooltip text (shown on hover)
        tooltip_text = f"{i}. {onsen.name}"

        # Prepare popup HTML (shown on click) with all onsen details
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 300px;">
            <h3 style="margin-top: 0; color: #2c3e50;">{i}. {onsen.name}</h3>
            <hr style="margin: 10px 0;">

            <p style="margin: 5px 0;">
                <b>ID:</b> {onsen.id}
            </p>

            <p style="margin: 5px 0;">
                <b>Ban Number:</b> {onsen.ban_number or 'N/A'}
            </p>

            <p style="margin: 5px 0;">
                <b>Coordinates:</b> {onsen.latitude:.6f}, {onsen.longitude:.6f}
            </p>

            <p style="margin: 5px 0;">
                <b>Address:</b> {onsen.address or 'N/A'}
            </p>

            {f'<p style="margin: 5px 0;"><b>Hours:</b> {onsen.usage_time}</p>' if onsen.usage_time else ''}

            {f'<p style="margin: 5px 0;"><b>Closed Days:</b> {onsen.closed_days}</p>' if onsen.closed_days else ''}

            {f'<p style="margin: 5px 0;"><b>Admission Fee:</b> {onsen.admission_fee}</p>' if onsen.admission_fee else ''}

            {f'<p style="margin: 5px 0;"><b>Spring Quality:</b> {onsen.spring_quality}</p>' if onsen.spring_quality else ''}

            {f'<p style="margin: 5px 0;"><b>Parking:</b> {onsen.parking}</p>' if onsen.parking else ''}

            {f'<p style="margin: 5px 0;"><b>Remarks:</b> {onsen.remarks}</p>' if onsen.remarks else ''}

            <p style="margin: 5px 0;">
                <b>Visited:</b> {'Yes' if onsen.id in visited_onsen_ids else 'No'}
            </p>

            <hr style="margin: 10px 0;">

            <p style="margin: 5px 0;">
                <a href="{generate_google_maps_link(onsen)}" target="_blank" style="color: #3498db;">
                    Open in Google Maps
                </a>
            </p>
        </div>
        """

        # Color code based on visit status
        if onsen.id in visited_onsen_ids:
            color = "green"
            icon = "check"
        else:
            color = "blue"
            icon = "tint"

        # Create popup with iframe for proper rendering
        iframe = IFrame(html=popup_html, width=320, height=450)
        popup = folium.Popup(iframe, max_width=320)

        # Add marker to map
        folium.Marker(
            location=[onsen.latitude, onsen.longitude],
            popup=popup,
            tooltip=tooltip_text,
            icon=folium.Icon(color=color, icon=icon, prefix="fa"),
        ).add_to(m)

    # Add legend with visit status
    visited_count = len([o for o in onsens_with_coords if o.id in visited_onsen_ids])
    unvisited_count = len(onsens_with_coords) - visited_count

    legend_html = f"""
    <div style="position: fixed;
                bottom: 50px;
                right: 50px;
                width: 220px;
                background-color: white;
                border: 2px solid grey;
                z-index: 9999;
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.3);">
        <h4 style="margin-top: 0;">All Onsens Map</h4>
        <p style="margin: 5px 0;">
            <i class="fa fa-tint" style="color: blue;"></i> Unvisited ({unvisited_count})
        </p>
        <p style="margin: 5px 0;">
            <i class="fa fa-check" style="color: green;"></i> Visited ({visited_count})
        </p>
        <p style="margin: 5px 0; font-size: 12px;">
            Total: {len(onsens_with_coords)} onsens
        </p>
        <p style="margin: 5px 0; font-size: 11px; color: #666;">
            Click markers for details<br>
            Hover for name
        </p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    m.save(output_path)

    return output_path
