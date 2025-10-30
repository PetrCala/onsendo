"""Interactive map generator for onsen recommendations using Folium."""

import os
from datetime import datetime
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


def _add_location_markers(
    folium_map: folium.Map,
    db_session: Session,
    reference_location_id: int | None = None
) -> None:
    """
    Add location markers to a folium map.

    Queries all locations from the database and adds them as markers.
    Reference location (if specified) is shown in red, all others in pink.
    Modifies folium_map in place.

    Args:
        folium_map: The folium Map object to add markers to
        db_session: Database session for querying locations
        reference_location_id: Optional ID of reference location (shown in red)
    """
    try:
        # Query all locations from database
        locations = db_session.query(Location).all()

        for location in locations:
            # Skip locations without coordinates
            if location.latitude is None or location.longitude is None:
                continue

            # Determine color: red for reference, pink for others
            is_reference = (reference_location_id is not None and
                          location.id == reference_location_id)
            color = "red" if is_reference else "pink"

            # Build popup HTML
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 280px;">
                <h3 style="margin-top: 0; color: #2c3e50;">
                    {location.name}
                </h3>
                <hr style="margin: 10px 0;">

                <p style="margin: 5px 0;">
                    <b>Coordinates:</b> {location.latitude:.6f}, {location.longitude:.6f}
                </p>

                {f'<p style="margin: 5px 0;"><b>Description:</b> {location.description}</p>'
                 if location.description else ''}

                {f'<p style="margin: 10px 0 5px 0; padding: 8px; background-color: #ffe4e4; border-radius: 4px; font-size: 12px;"><b>📍 Reference Location</b></p>'
                 if is_reference else ''}
            </div>
            """

            # Tooltip text (shown on hover)
            tooltip_text = location.name
            if is_reference:
                tooltip_text += " (Reference Location)"

            # Create popup with iframe
            iframe = IFrame(html=popup_html, width=300, height=250)
            popup = folium.Popup(iframe, max_width=300)

            # Add marker to map
            folium.Marker(
                location=[location.latitude, location.longitude],
                popup=popup,
                tooltip=tooltip_text,
                icon=folium.Icon(color=color, icon="home", prefix="fa"),
            ).add_to(folium_map)

    except Exception as e:
        # Log error but don't fail map generation
        logger.warning(f"Failed to add location markers to map: {e}")


def format_single_onsen_for_reminder(
    onsen: Onsen,
    distance: float,
    metadata: dict,
    location_name: str,
    index: int
) -> str:
    """
    Format details for a single onsen for reminder body.

    Args:
        onsen: Onsen object
        distance: Distance in km
        metadata: Metadata dictionary
        location_name: Name of the user's location
        index: Index number (1-based) in the recommendation list

    Returns:
        Formatted string for reminder body
    """
    lines = [f"📍 From: {location_name}", ""]

    # Onsen header
    lines.append(f"{index}. {onsen.name}")

    # BAN number
    if onsen.ban_number:
        lines.append(f"   BAN: {onsen.ban_number}")

    # Distance
    lines.append(f"   Distance: {distance:.1f} km ({metadata['distance_category']})")

    # Address
    if onsen.address:
        lines.append(f"   Address: {onsen.address}")

    # Coordinates
    lines.append(f"   Coordinates: {onsen.latitude}, {onsen.longitude}")

    # Hours
    if onsen.usage_time:
        lines.append(f"   Hours: {onsen.usage_time}")

    # Closed days
    if onsen.closed_days:
        lines.append(f"   Closed: {onsen.closed_days}")

    # Fee
    if onsen.admission_fee:
        lines.append(f"   Fee: {onsen.admission_fee}")

    # Spring quality
    if onsen.spring_quality:
        lines.append(f"   Spring: {onsen.spring_quality}")

    # Parking
    if onsen.parking:
        lines.append(f"   Parking: {onsen.parking}")

    # Status
    if metadata['is_available']:
        lines.append("   Status: ✅ Available")
    else:
        lines.append("   Status: ⚠️ Currently Closed")

    if metadata['has_been_visited']:
        lines.append("   Previously Visited: Yes")

    if metadata['stay_restricted']:
        lines.append("   Stay Restriction: Yes")

    # Google Maps link
    lines.append(f"   Maps: {metadata['google_maps_link']}")

    return "\n".join(lines)


def generate_recommendation_map(
    recommendations: list[tuple[Onsen, float, dict]],
    location: Location,
    db_session: Session,
    output_filename: str | None = None,
    target_time: datetime | None = None,
    show_locations: bool = True,
) -> str:
    """
    Generate an interactive HTML map showing recommended onsens.

    Args:
        recommendations: List of tuples (onsen, distance_km, metadata)
        location: User's location (used as map center and marked as reference)
        db_session: Database session for querying locations
        output_filename: Optional filename for the map (default: timestamped)
        target_time: Optional target time for onsen visit (enables reminder button)
        show_locations: Whether to show location markers on map (default: True)

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

    # Generate individual reminder scripts for each onsen if target_time provided
    reminder_scripts = {}  # onsen_id -> script_path
    if target_time and is_reminders_available():
        base_filename = output_filename.replace('.html', '')
        time_str = target_time.strftime("%H:%M")

        for i, (onsen, distance, metadata) in enumerate(recommendations, 1):
            try:
                # Generate script for this specific onsen
                script_filename = f"{base_filename}_onsen_{i}.command"
                script_path = os.path.join(PATHS.MAPS_DIR, script_filename)

                # Format reminder title and body for this onsen
                reminder_title = f"Onsen: {onsen.name} at {time_str}"
                reminder_body = format_single_onsen_for_reminder(
                    onsen, distance, metadata, location.name, i
                )

                # Generate the .command script
                generate_reminder_script(reminder_title, target_time, script_path, body=reminder_body)

                reminder_scripts[onsen.id] = script_path
            except (OSError, ValueError) as e:
                logger.warning(f"Failed to generate reminder script for onsen {onsen.id}: {e}")

    # Create map centered on user's location
    center_lat = location.latitude or 33.2794  # Default to Beppu
    center_lon = location.longitude or 131.5006

    # Create the map with a nice tile layer
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    # Add location markers (including reference location)
    if show_locations:
        _add_location_markers(m, db_session, reference_location_id=location.id)

    # Add onsen markers
    for i, (onsen, distance, metadata) in enumerate(recommendations, 1):
        if onsen.latitude is None or onsen.longitude is None:
            continue

        # Prepare tooltip text (shown on hover)
        tooltip_text = f"{i}. {onsen.name}"

        # Check if reminder button should be added for this onsen
        reminder_button_html = ""
        if onsen.id in reminder_scripts:
            script_path = reminder_scripts[onsen.id]
            # Escape for JavaScript string
            escaped_script_path = script_path.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
            escaped_onsen_name = onsen.name.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')

            reminder_button_html = f"""
            <hr style="margin: 10px 0;">
            <script>
            function createReminderForThisOnsen() {{
                var scriptPath = '{escaped_script_path}';
                var onsenName = '{escaped_onsen_name}';
                var terminalCommand = 'bash "' + scriptPath + '"';

                // Try to copy to clipboard
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(terminalCommand).then(function() {{
                        alert('Reminder command copied to clipboard!\\n\\n' +
                              'For: ' + onsenName + '\\n\\n' +
                              'Option 1 (Recommended):\\n' +
                              '1. Open Terminal\\n' +
                              '2. Paste (Cmd+V) and press Enter\\n\\n' +
                              'Option 2:\\n' +
                              'Double-click the .command file in:\\n' +
                              scriptPath.substring(0, scriptPath.lastIndexOf('/')));
                    }}).catch(function(err) {{
                        alert('To create reminder for ' + onsenName + ':\\n\\n' +
                              '1. Open Terminal\\n' +
                              '2. Run: ' + terminalCommand);
                    }});
                }} else {{
                    alert('To create reminder for ' + onsenName + ':\\n\\n' +
                          '1. Open Terminal\\n' +
                          '2. Run: ' + terminalCommand);
                }}
            }}
            </script>
            <div style="text-align: center;">
                <button onclick="createReminderForThisOnsen()"
                       style="padding: 10px 15px;
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                              color: white;
                              border: none;
                              border-radius: 6px;
                              font-size: 13px;
                              font-weight: bold;
                              cursor: pointer;
                              box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                              width: 100%;">
                    <i class="fa fa-bell"></i> Create Reminder for this Onsen
                </button>
            </div>
            """

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

            {reminder_button_html}
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
    legend_html = f"""
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
        {'<p style="margin: 5px 0;"><i class="fa fa-home" style="color: red;"></i> Reference Location</p>' if show_locations else ''}
        {'<p style="margin: 5px 0;"><i class="fa fa-home" style="color: pink;"></i> Other Locations</p>' if show_locations else ''}
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

    # Add global reminder button for all onsens if target_time is provided
    if target_time and is_reminders_available():
        try:
            # Generate global script for all onsens
            global_script_filename = output_filename.replace('.html', '_all.command')
            global_script_path = os.path.join(PATHS.MAPS_DIR, global_script_filename)

            # Format reminder title and body for all onsens
            time_str = target_time.strftime("%H:%M")
            global_reminder_title = f"Onsen recommendation {time_str}"
            global_reminder_body = format_onsen_details_for_reminder(
                recommendations=recommendations,
                location_name=location.name
            )

            # Generate the global .command script
            generate_reminder_script(global_reminder_title, target_time, global_script_path, body=global_reminder_body)

            # Escape the path for JavaScript
            escaped_global_script_path = global_script_path.replace('\\', '\\\\').replace("'", "\\'")

            # Add global reminder button with modal
            global_reminder_html = f"""
            <script>
            var globalReminderScriptPath = '{escaped_global_script_path}';

            function createGlobalReminder() {{
                var terminalCommand = 'bash "' + globalReminderScriptPath + '"';

                // Copy terminal command to clipboard
                navigator.clipboard.writeText(terminalCommand).then(function() {{
                    // Show modal with instructions
                    var modal = document.getElementById('globalReminderModal');
                    modal.style.display = 'block';
                }}).catch(function(err) {{
                    // Fallback if clipboard fails
                    alert('To create reminder for all onsens:\\n\\n' +
                          '1. Open Terminal\\n' +
                          '2. Run this command:\\n' +
                          terminalCommand + '\\n\\n' +
                          'Or double-click this file in Finder:\\n' +
                          globalReminderScriptPath);
                }});
            }}

            function closeGlobalModal() {{
                document.getElementById('globalReminderModal').style.display = 'none';
            }}

            function openGlobalInFinder() {{
                // Try to reveal in Finder using file:// protocol
                var dirPath = globalReminderScriptPath.substring(0, globalReminderScriptPath.lastIndexOf('/'));
                window.open('file://' + dirPath);
                closeGlobalModal();
            }}
            </script>

            <!-- Global Reminder Modal -->
            <div id="globalReminderModal" style="display: none;
                                           position: fixed;
                                           z-index: 10000;
                                           left: 0;
                                           top: 0;
                                           width: 100%;
                                           height: 100%;
                                           background-color: rgba(0,0,0,0.5);">
                <div style="background-color: white;
                           margin: 10% auto;
                           padding: 30px;
                           border-radius: 10px;
                           width: 500px;
                           max-width: 90%;
                           box-shadow: 0 8px 16px rgba(0,0,0,0.3);">
                    <h2 style="margin-top: 0; color: #667eea;">Create Reminder for All Onsens</h2>
                    <p style="margin: 20px 0;">This will create a reminder with all {len(recommendations)} recommended onsens.</p>

                    <div style="margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                        <strong>Option 1: Terminal (Recommended)</strong>
                        <p style="margin: 10px 0 5px 0; font-size: 13px;">
                            The terminal command has been copied to your clipboard!
                        </p>
                        <ol style="margin: 10px 0; padding-left: 20px; font-size: 13px;">
                            <li>Open Terminal (⌘+Space, type "Terminal")</li>
                            <li>Paste the command (⌘+V)</li>
                            <li>Press Enter</li>
                        </ol>
                    </div>

                    <div style="margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                        <strong>Option 2: Finder</strong>
                        <ol style="margin: 10px 0; padding-left: 20px; font-size: 13px;">
                            <li>Click "Open Folder" below</li>
                            <li>Double-click the .command file</li>
                        </ol>
                        <button onclick="openGlobalInFinder()"
                               style="margin-top: 10px;
                                      padding: 8px 16px;
                                      background-color: #667eea;
                                      color: white;
                                      border: none;
                                      border-radius: 5px;
                                      cursor: pointer;">
                            Open Folder
                        </button>
                    </div>

                    <button onclick="closeGlobalModal()"
                           style="margin-top: 20px;
                                  padding: 10px 20px;
                                  background-color: #ccc;
                                  border: none;
                                  border-radius: 5px;
                                  cursor: pointer;">
                        Close
                    </button>
                </div>
            </div>

            <div style="position: fixed;
                        top: 80px;
                        right: 10px;
                        z-index: 9999;">
                <button onclick="createGlobalReminder()"
                   style="display: block;
                          padding: 12px 20px;
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                          color: white;
                          text-decoration: none;
                          border: none;
                          border-radius: 8px;
                          font-size: 14px;
                          font-weight: bold;
                          font-family: Arial, sans-serif;
                          box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                          text-align: center;
                          cursor: pointer;
                          transition: all 0.3s ease;">
                    <i class="fa fa-bell" style="margin-right: 8px;"></i>Reminder: All Onsens
                </button>
                <div style="margin-top: 8px;
                           padding: 8px;
                           background-color: white;
                           border: 1px solid #ddd;
                           border-radius: 5px;
                           font-size: 11px;
                           color: #666;
                           text-align: center;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {global_reminder_title}<br>
                    <span style="font-size: 10px; color: #999;">Click for all {len(recommendations)} onsens</span>
                </div>
            </div>
            """
            m.get_root().html.add_child(folium.Element(global_reminder_html))

        except (OSError, ValueError) as e:
            # Log error but don't fail map generation
            logger.warning(f"Failed to generate global reminder script: {e}")

    # Save map
    m.save(output_path)

    return output_path


def generate_all_onsens_map(
    onsens: list[Onsen],
    db_session: Session,
    output_filename: str | None = None,
    show_locations: bool = True,
) -> str:
    """
    Generate an interactive HTML map showing all onsens in the database.

    Args:
        onsens: List of all onsens to display
        db_session: Database session to query visit status and locations
        output_filename: Optional filename for the map (default: timestamped)
        show_locations: Whether to show location markers on map (default: True)

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

    # Add location markers (all in pink, no reference location)
    if show_locations:
        _add_location_markers(m, db_session, reference_location_id=None)

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
        {'<p style="margin: 5px 0;"><i class="fa fa-home" style="color: pink;"></i> User Locations</p>' if show_locations else ''}
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
