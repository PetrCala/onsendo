"""Statistics map generator for analysis visualization.

Creates interactive Folium maps showing visited onsens with colored circles
representing statistics from visits. Supports multiple statistics selectable
via dropdown in the browser.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import folium
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.models import Onsen, OnsenVisit
from src.paths import PATHS
from src.lib.map_generator import _add_location_markers
from src.lib.statistics_registry import StatisticsRegistry


class StatisticsMapGenerator:
    """Generator for statistics-based interactive maps."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize generator.

        Args:
            output_dir: Output directory for maps (default: PATHS.MAPS_DIR)
        """
        self.output_dir = Path(output_dir) if output_dir else Path(PATHS.MAPS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = StatisticsRegistry()

    def generate_map(
        self,
        session: Session,
        visit_selection: str = "latest",
        show_locations: bool = True,
        output_filename: str | None = None,
    ) -> Path:
        """Generate interactive statistics map.

        Args:
            session: Database session
            visit_selection: Visit selection strategy ('latest', 'first', or 'nth:N')
            show_locations: Whether to show user location markers
            output_filename: Optional output filename (default: auto-generated)

        Returns:
            Path to generated HTML map file
        """
        # pylint: disable=too-complex,too-many-locals
        # Complexity justified: orchestrates map generation with multiple components

        logger.info("Generating statistics map...")

        # Get all visited onsens with coordinates
        visited_onsens = (
            session.query(Onsen)
            .join(OnsenVisit)
            .filter(Onsen.latitude.isnot(None))
            .filter(Onsen.longitude.isnot(None))
            .distinct()
            .all()
        )

        if not visited_onsens:
            logger.warning("No visited onsens with coordinates found")
            return None

        logger.info(f"Found {len(visited_onsens)} visited onsens")

        # Get all available statistics
        all_statistics = self.registry.get_all_statistics()
        statistic_field_names = [stat["field_name"] for stat in all_statistics]

        # Collect data: onsen -> visit -> statistics
        onsen_data = []
        all_statistic_values = {field: [] for field in statistic_field_names}

        for onsen in visited_onsens:
            visit = self._get_visit_for_onsen(session, onsen.id, visit_selection)
            if not visit:
                continue

            # Extract all statistics from this visit
            statistics = {}
            for field_name in statistic_field_names:
                value = self._get_statistic_value(visit, field_name)
                if value is not None:
                    statistics[field_name] = value
                    all_statistic_values[field_name].append(value)

            if statistics:
                onsen_data.append(
                    {
                        "onsen": onsen,
                        "visit": visit,
                        "statistics": statistics,
                    }
                )

        if not onsen_data:
            logger.warning("No visits with statistics found")
            return None

        # Calculate bins for each statistic (for color coding)
        statistic_bins = {}
        for field_name in statistic_field_names:
            values = all_statistic_values[field_name]
            if values:
                statistic_bins[field_name] = self._calculate_bins(values)

        # Create map
        center_lat = np.mean([d["onsen"].latitude for d in onsen_data])
        center_lon = np.mean([d["onsen"].longitude for d in onsen_data])

        folium_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
        )

        # Add tile layers with proper attribution
        folium.TileLayer(
            tiles="Stamen Terrain",
            name="Terrain",
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        ).add_to(folium_map)
        folium.TileLayer(
            tiles="Stamen Toner",
            name="Toner",
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
        ).add_to(folium_map)
        folium.TileLayer(
            tiles="CartoDB positron",
            name="Light",
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        ).add_to(folium_map)

        # Add location markers
        if show_locations:
            _add_location_markers(folium_map, session, reference_location_id=None)

        # Create feature group for onsen markers
        onsen_layer = folium.FeatureGroup(name="Onsen Statistics", show=True)

        # Default statistic to display (prefer personal_rating, otherwise first available)
        default_statistic = "personal_rating"
        if default_statistic not in statistic_field_names:
            default_statistic = statistic_field_names[0] if statistic_field_names else None

        # Add markers for each onsen
        marker_data = []
        for data in onsen_data:
            onsen = data["onsen"]
            visit = data["visit"]
            statistics = data["statistics"]

            # Get color for default statistic
            color = "gray"
            if default_statistic and default_statistic in statistics:
                color = self._get_color_for_value(
                    statistics[default_statistic],
                    default_statistic,
                    statistic_bins.get(default_statistic, {}),
                )

            # Create popup HTML
            popup_html = self._create_popup_html(onsen, visit, statistics)

            # Create marker
            marker = folium.CircleMarker(
                location=[onsen.latitude, onsen.longitude],
                radius=10,
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=f"{onsen.name}",
                color="black",
                weight=1,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
            )
            marker.add_to(onsen_layer)

            # Store marker data for JavaScript (using coordinates as unique identifier)
            marker_data.append(
                {
                    "onsen_id": onsen.id,
                    "lat": onsen.latitude,
                    "lon": onsen.longitude,
                    "name": onsen.name,
                    "statistics": statistics,
                }
            )

        onsen_layer.add_to(folium_map)

        # Add layer control
        folium.LayerControl(collapsed=False).add_to(folium_map)

        # Add JavaScript for interactive statistic selection
        self._add_statistic_selector(
            folium_map, statistic_field_names, statistic_bins, marker_data, default_statistic
        )

        # Add legend
        if default_statistic:
            legend_html = self._create_legend_html(
                default_statistic, statistic_bins.get(default_statistic, {})
            )
            folium_map.get_root().html.add_child(folium.Element(legend_html))

        # Save map
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"analysis_statistics_map_{timestamp}.html"

        output_path = self.output_dir / output_filename
        folium_map.save(str(output_path))

        logger.success(f"Statistics map saved to: {output_path}")
        return output_path

    def _get_visit_for_onsen(
        self, session: Session, onsen_id: int, strategy: str
    ) -> Optional[OnsenVisit]:
        """Get visit for onsen based on selection strategy.

        Args:
            session: Database session
            onsen_id: Onsen ID
            strategy: Selection strategy ('latest', 'first', or 'nth:N')

        Returns:
            Selected OnsenVisit or None if not found
        """
        query = session.query(OnsenVisit).filter(OnsenVisit.onsen_id == onsen_id)

        if strategy == "latest":
            return query.order_by(OnsenVisit.visit_time.desc()).first()

        if strategy == "first":
            return query.order_by(OnsenVisit.visit_time.asc()).first()

        if strategy.startswith("nth:"):
            try:
                n = int(strategy.split(":")[1])
                if n < 1:
                    logger.warning(f"Invalid nth value: {n}, must be >= 1")
                    return None
                # nth:1 = first, nth:2 = second, etc.
                visits = query.order_by(OnsenVisit.visit_time.asc()).all()
                if n <= len(visits):
                    return visits[n - 1]
                logger.warning(f"Onsen {onsen_id} has only {len(visits)} visits, cannot get nth:{n}")
                return None
            except (ValueError, IndexError):
                logger.warning(f"Invalid nth strategy format: {strategy}")
                return None

        logger.warning(f"Unknown visit selection strategy: {strategy}, using 'latest'")
        return query.order_by(OnsenVisit.visit_time.desc()).first()

    def _get_statistic_value(self, visit: OnsenVisit, field_name: str) -> Optional[float | int]:
        """Extract statistic value from visit.

        Args:
            visit: OnsenVisit object
            field_name: Field name to extract

        Returns:
            Value or None if not available
        """
        value = getattr(visit, field_name, None)
        if value is None:
            return None

        # Convert to numeric if possible
        if isinstance(value, (int, float)):
            return float(value)

        return None

    def _calculate_bins(self, values: list[float | int]) -> dict:
        """Calculate color bins based on data distribution.

        Uses quantiles (25%, 50%, 75%) to create 4 bins.

        Args:
            values: List of numeric values

        Returns:
            Dictionary with bin boundaries (all values converted to float for JSON serialization)
        """
        if not values:
            return {}

        values_array = np.array(values, dtype=float)
        q25, q50, q75 = np.percentile(values_array, [25, 50, 75])

        # Convert all to native Python floats for JSON serialization
        return {
            "min": float(np.min(values_array)),
            "q25": float(q25),
            "q50": float(q50),
            "q75": float(q75),
            "max": float(np.max(values_array)),
        }

    def _get_color_for_value(
        self, value: float | int, statistic: str, bins: dict
    ) -> str:
        """Get color for statistic value based on bins.

        Args:
            value: The statistic value
            statistic: Statistic field name
            bins: Bin boundaries dictionary

        Returns:
            Color name (for Folium)
        """
        if not bins or "min" not in bins:
            return "gray"

        min_val = bins["min"]
        q25 = bins.get("q25", min_val)
        q50 = bins.get("q50", min_val)
        q75 = bins.get("q75", min_val)
        max_val = bins.get("max", min_val)

        # Improved color gradient: blue (low) -> cyan -> green -> yellow -> orange -> red (high)
        # Better represents value distribution
        if value <= q25:
            return "blue"
        if value <= q50:
            return "cyan"
        if value <= q75:
            return "green"
        # Above q75, use yellow/orange/red based on how close to max
        if max_val > q75:
            range_above_q75 = max_val - q75
            if range_above_q75 > 0:
                position = (value - q75) / range_above_q75
                if position < 0.33:
                    return "yellow"
                if position < 0.67:
                    return "orange"
        return "red"  # Highest values are red

    def _create_popup_html(
        self, onsen: Onsen, visit: OnsenVisit, statistics: dict[str, float | int]
    ) -> str:
        """Create HTML popup content.

        Args:
            onsen: Onsen object
            visit: OnsenVisit object
            statistics: Dictionary of statistic values

        Returns:
            HTML string
        """
        html = ['<div style="font-family: Arial, sans-serif; width: 350px;">']

        # Title
        html.append(
            f'<h3 style="margin: 0 0 10px 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">{onsen.name}</h3>'
        )

        # Visit info
        if visit.visit_time:
            html.append(
                f'<p style="margin: 5px 0; font-size: 0.9em; color: #666;"><strong>Visit:</strong> {visit.visit_time.strftime("%Y-%m-%d %H:%M")}</p>'
            )

        html.append('<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">')

        # Statistics section
        html.append(
            '<div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; margin: 5px 0;">'
        )
        html.append('<p style="margin: 3px 0; font-weight: bold;">Statistics:</p>')

        for field_name, value in sorted(statistics.items()):
            display_name = self.registry.get_statistic_display_name(field_name)
            formatted_value = self.registry.format_statistic_value(field_name, value)
            html.append(
                f'<p style="margin: 2px 0; font-size: 0.9em;"><strong>{display_name}:</strong> {formatted_value}</p>'
            )

        html.append("</div>")

        # Additional visit details
        if visit.stay_length_minutes:
            html.append(
                f'<p style="margin: 5px 0;"><strong>Stay Length:</strong> {visit.stay_length_minutes} min</p>'
            )

        if visit.entry_fee_yen:
            html.append(
                f'<p style="margin: 5px 0;"><strong>Entry Fee:</strong> ¥{visit.entry_fee_yen}</p>'
            )

        if visit.notes:
            html.append('<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">')
            html.append(
                f'<p style="margin: 5px 0; font-size: 0.85em; color: #666;"><em>{visit.notes}</em></p>'
            )

        html.append("</div>")
        return "".join(html)

    def _create_legend_html(self, statistic: str, bins: dict) -> str:
        """Create legend HTML for current statistic.

        Args:
            statistic: Current statistic field name
            bins: Bin boundaries

        Returns:
            HTML string for legend
        """
        display_name = self.registry.get_statistic_display_name(statistic)

        if not bins or "min" not in bins:
            return ""

        min_val = bins["min"]
        q25 = bins.get("q25", min_val)
        q50 = bins.get("q50", min_val)
        q75 = bins.get("q75", min_val)
        max_val = bins.get("max", min_val)

        # Format values based on statistic type
        stat_info = self.registry.get_statistic(statistic)
        stat_type = stat_info.get("type", "numeric") if stat_info else "numeric"

        def format_val(val):
            if stat_type == "rating":
                return f"{val:.1f}"
            if stat_type == "duration":
                return f"{int(val)} min"
            if "fee" in statistic.lower() or "yen" in statistic.lower():
                return f"¥{int(val)}"
            if "temperature" in statistic.lower():
                return f"{val:.1f}°C"
            return f"{val:.1f}"

        # Calculate sub-bins for top quartile to match color scheme exactly
        # Colors: blue (<=q25), cyan (<=q50), green (<=q75), yellow (q75 to q75+33%), orange (q75+33% to q75+67%), red (>q75+67%)
        range_above_q75 = max_val - q75
        q33_above = q75 + range_above_q75 * 0.33 if range_above_q75 > 0 else max_val
        q67_above = q75 + range_above_q75 * 0.67 if range_above_q75 > 0 else max_val
        
        legend_html = f'''
        <div id="statistics-legend" style="position: fixed;
                    bottom: 50px; right: 50px; width: 200px; height: auto;
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
            <p style="margin: 0 0 8px 0; font-weight: bold;">{display_name}</p>
            <p style="margin: 3px 0;"><span style="color: blue;">●</span> {format_val(min_val)} - {format_val(q25)}</p>
            <p style="margin: 3px 0;"><span style="color: cyan;">●</span> {format_val(q25)} - {format_val(q50)}</p>
            <p style="margin: 3px 0;"><span style="color: green;">●</span> {format_val(q50)} - {format_val(q75)}</p>
        '''
        
        # Only show top quartile bins if there's a range above q75
        if range_above_q75 > 0:
            legend_html += f'''
            <p style="margin: 3px 0;"><span style="color: yellow;">●</span> {format_val(q75)} - {format_val(q33_above)}</p>
            <p style="margin: 3px 0;"><span style="color: orange;">●</span> {format_val(q33_above)} - {format_val(q67_above)}</p>
            <p style="margin: 3px 0;"><span style="color: red;">●</span> {format_val(q67_above)} - {format_val(max_val)}</p>
            '''
        
        legend_html += '''
        </div>
        '''
        return legend_html

    def _add_statistic_selector(
        self,
        folium_map: folium.Map,
        statistic_field_names: list[str],
        statistic_bins: dict,
        marker_data: list[dict],
        default_statistic: str,
    ) -> None:
        """Add JavaScript for interactive statistic selection.

        Args:
            folium_map: Folium map object
            statistic_field_names: List of available statistic field names
            statistic_bins: Dictionary of bins for each statistic
            marker_data: List of marker data dictionaries
            default_statistic: Default statistic to display
        """
        # Create dropdown HTML - positioned to avoid overlap with Folium layer control
        # Layer control is typically at top-right, so we place this at top-left
        dropdown_html = f'''
        <div id="statistic-selector" style="position: fixed;
                    top: 10px; left: 10px; width: 250px; height: auto;
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
            <label for="statistic-dropdown" style="font-weight: bold; display: block; margin-bottom: 5px;">Select Statistic:</label>
            <select id="statistic-dropdown" style="width: 100%; padding: 5px; font-size: 14px;">
        '''

        for field_name in statistic_field_names:
            display_name = self.registry.get_statistic_display_name(field_name)
            selected = "selected" if field_name == default_statistic else ""
            dropdown_html += f'<option value="{field_name}" {selected}>{display_name}</option>'

        dropdown_html += """
            </select>
        </div>
        """

        # Prepare display names dictionary
        display_names = {
            fn: self.registry.get_statistic_display_name(fn) for fn in statistic_field_names
        }

        # JavaScript to update markers and legend
        js_code = f"""
        <script>
        // Marker data
        const markerData = {json.dumps(marker_data)};
        const statisticBins = {json.dumps(statistic_bins)};
        const displayNames = {json.dumps(display_names)};
        
        function getDisplayName(fieldName) {{
            return displayNames[fieldName] || fieldName;
        }}
        
        function formatValue(fieldName, value) {{
            // Simple formatting (full formatting done server-side in popup)
            if (fieldName.includes('rating')) {{
                return value.toFixed(1) + '/10';
            }}
            if (fieldName.includes('duration') || fieldName.includes('minutes')) {{
                return Math.round(value) + ' min';
            }}
            if (fieldName.includes('fee') || fieldName.includes('yen')) {{
                return '¥' + Math.round(value);
            }}
            if (fieldName.includes('temperature')) {{
                return value.toFixed(1) + '°C';
            }}
            return value.toFixed(1);
        }}

        function getColorForValue(value, bins) {{
            if (!bins || !bins.min) return 'gray';
            const q25 = bins.q25 || bins.min;
            const q50 = bins.q50 || bins.min;
            const q75 = bins.q75 || bins.min;
            const max = bins.max || bins.min;

            if (value <= q25) return 'blue';
            if (value <= q50) return 'cyan';
            if (value <= q75) return 'green';
            if (max > q75) {{
                const range = max - q75;
                if (range > 0) {{
                    const position = (value - q75) / range;
                    if (position < 0.33) return 'yellow';
                    if (position < 0.67) return 'orange';
                }}
            }}
            return 'red';  // Highest values are red
        }}

        function formatLegendValue(value, statistic) {{
            if (statistic.includes('rating')) {{
                return value.toFixed(1);
            }}
            if (statistic.includes('duration') || statistic.includes('minutes')) {{
                return Math.round(value) + ' min';
            }}
            if (statistic.includes('fee') || statistic.includes('yen')) {{
                return '¥' + Math.round(value);
            }}
            if (statistic.includes('temperature')) {{
                return value.toFixed(1) + '°C';
            }}
            return value.toFixed(1);
        }}

        // Store marker references when map loads
        const markerRefs = {{}};
        
        function initializeMarkers() {{
            // Wait for map to be fully loaded
            if (typeof map === 'undefined') {{
                setTimeout(initializeMarkers, 100);
                return;
            }}
            
            // Find all CircleMarkers and store references by coordinates
            // Need to check both map layers and FeatureGroups
            function processLayer(layer) {{
                if (layer instanceof L.CircleMarker) {{
                    const lat = layer.getLatLng().lat;
                    const lon = layer.getLatLng().lng;
                    const key = lat.toFixed(6) + ',' + lon.toFixed(6);
                    markerRefs[key] = layer;
                }} else if (layer instanceof L.FeatureGroup || layer instanceof L.LayerGroup) {{
                    // Recursively process FeatureGroup layers
                    layer.eachLayer(processLayer);
                }}
            }}
            
            map.eachLayer(processLayer);
        }}
        
        function updateMap(selectedStatistic) {{
            const bins = statisticBins[selectedStatistic];
            if (!bins) {{
                console.warn('No bins for statistic:', selectedStatistic);
                return;
            }}

            // Update all markers by matching coordinates
            markerData.forEach(function(data) {{
                const key = data.lat.toFixed(6) + ',' + data.lon.toFixed(6);
                const marker = markerRefs[key];
                
                if (marker && data.statistics[selectedStatistic] !== undefined) {{
                    const value = data.statistics[selectedStatistic];
                    const color = getColorForValue(value, bins);
                    marker.setStyle({{
                        fillColor: color,
                        fillOpacity: 0.7
                    }});
                }} else if (marker) {{
                    // No data for this statistic
                    marker.setStyle({{
                        fillColor: 'gray',
                        fillOpacity: 0.3
                    }});
                }}
            }});
            
            // If markers not initialized yet, try again
            if (Object.keys(markerRefs).length === 0) {{
                initializeMarkers();
                setTimeout(function() {{ updateMap(selectedStatistic); }}, 200);
                return;
            }}

            // Update legend
            const legendDiv = document.getElementById('statistics-legend');
            if (legendDiv && bins) {{
                const displayName = getDisplayName(selectedStatistic);
                const min = bins.min;
                const q25 = bins.q25 || min;
                const q50 = bins.q50 || min;
                const q75 = bins.q75 || min;
                const max = bins.max || min;

                // Create legend with proper color gradient matching the color function exactly
                const rangeAboveQ75 = max - q75;
                let legendHTML = `
                    <p style="margin: 0 0 8px 0; font-weight: bold;">${{displayName}}</p>
                    <p style="margin: 3px 0;"><span style="color: blue;">●</span> ${{formatLegendValue(min, selectedStatistic)}} - ${{formatLegendValue(q25, selectedStatistic)}}</p>
                    <p style="margin: 3px 0;"><span style="color: cyan;">●</span> ${{formatLegendValue(q25, selectedStatistic)}} - ${{formatLegendValue(q50, selectedStatistic)}}</p>
                    <p style="margin: 3px 0;"><span style="color: green;">●</span> ${{formatLegendValue(q50, selectedStatistic)}} - ${{formatLegendValue(q75, selectedStatistic)}}</p>
                `;
                
                // Only show top quartile bins if there's a range above q75
                if (rangeAboveQ75 > 0) {{
                    const q33Above = q75 + rangeAboveQ75 * 0.33;
                    const q67Above = q75 + rangeAboveQ75 * 0.67;
                    legendHTML += `
                    <p style="margin: 3px 0;"><span style="color: yellow;">●</span> ${{formatLegendValue(q75, selectedStatistic)}} - ${{formatLegendValue(q33Above, selectedStatistic)}}</p>
                    <p style="margin: 3px 0;"><span style="color: orange;">●</span> ${{formatLegendValue(q33Above, selectedStatistic)}} - ${{formatLegendValue(q67Above, selectedStatistic)}}</p>
                    <p style="margin: 3px 0;"><span style="color: red;">●</span> ${{formatLegendValue(q67Above, selectedStatistic)}} - ${{formatLegendValue(max, selectedStatistic)}}</p>
                    `;
                }}
                
                legendDiv.innerHTML = legendHTML;
            }}
        }}

        // Initialize markers when page loads
        window.addEventListener('load', function() {{
            initializeMarkers();
        }});
        
        // Also try immediately (in case page already loaded)
        initializeMarkers();

        // Set up dropdown handler
        document.addEventListener('DOMContentLoaded', function() {{
            const dropdown = document.getElementById('statistic-dropdown');
            if (dropdown) {{
                dropdown.addEventListener('change', function(e) {{
                    updateMap(e.target.value);
                }});
            }}
        }});
        </script>
        """

        # Add to map
        folium_map.get_root().html.add_child(folium.Element(dropdown_html))
        folium_map.get_root().html.add_child(folium.Element(js_code))

