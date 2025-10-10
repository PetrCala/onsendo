"""
Interactive map generation for onsen spatial analysis.

Creates rich Folium maps with detailed popups, multiple layers,
and comprehensive onsen statistics.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class InteractiveMapGenerator:
    """
    Generator for interactive onsen maps with rich information displays.

    Creates professional Folium maps with:
    - Detailed onsen popups (ratings, visits, statistics)
    - Multiple toggle layers (ratings, prices, heart rate)
    - Heat maps weighted by various metrics
    - Cluster analysis visualization
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_comprehensive_onsen_map(
        self,
        data: pd.DataFrame,
        map_name: str = "onsen_overview.html",
        center: Optional[Tuple[float, float]] = None,
        zoom_start: int = 12,
    ) -> Path:
        """
        Create comprehensive interactive map with all onsen data.

        Args:
            data: DataFrame with onsen data including latitude, longitude, ratings, etc.
            map_name: Name for the output HTML file
            center: Optional (lat, lon) tuple for map center
            zoom_start: Initial zoom level

        Returns:
            Path to generated HTML map
        """
        import folium
        from folium.plugins import MarkerCluster, HeatMap

        logger.info(f"Creating comprehensive onsen map: {map_name}")

        # Filter for valid coordinates
        map_data = data.dropna(subset=['latitude', 'longitude']).copy()

        if map_data.empty:
            logger.warning("No valid coordinates found")
            return None

        # Calculate center if not provided
        if center is None:
            center = (map_data['latitude'].mean(), map_data['longitude'].mean())

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles='OpenStreetMap',
        )

        # Add different tile layers
        folium.TileLayer('Stamen Terrain', name='Terrain').add_to(m)
        folium.TileLayer('Stamen Toner', name='Toner').add_to(m)
        folium.TileLayer('CartoDB positron', name='Light').add_to(m)

        # Layer 1: Individual markers with detailed popups
        marker_layer = folium.FeatureGroup(name='Onsen Details', show=True)

        for _, row in map_data.iterrows():
            popup_html = self._create_rich_popup(row)

            # Determine marker color based on rating
            if 'personal_rating' in row and pd.notna(row['personal_rating']):
                rating = row['personal_rating']
                if rating >= 9:
                    color = 'darkgreen'
                elif rating >= 7.5:
                    color = 'green'
                elif rating >= 6:
                    color = 'orange'
                else:
                    color = 'red'
            else:
                color = 'gray'

            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=400),
                tooltip=self._create_tooltip(row),
                icon=folium.Icon(color=color, icon='info-sign'),
            ).add_to(marker_layer)

        marker_layer.add_to(m)

        # Layer 2: Heat map by visit count
        if 'visit_count' in map_data.columns:
            heat_data = []
            for _, row in map_data.iterrows():
                if pd.notna(row.get('visit_count', 0)) and row.get('visit_count', 0) > 0:
                    heat_data.append([
                        row['latitude'],
                        row['longitude'],
                        float(row['visit_count'])
                    ])

            if heat_data:
                heat_layer = folium.FeatureGroup(name='Visit Density', show=False)
                HeatMap(heat_data, radius=25, blur=35, max_zoom=13).add_to(heat_layer)
                heat_layer.add_to(m)

        # Layer 3: Rating heat map
        if 'personal_rating' in map_data.columns or 'avg_rating' in map_data.columns:
            rating_col = 'avg_rating' if 'avg_rating' in map_data.columns else 'personal_rating'
            rating_data = []

            for _, row in map_data.iterrows():
                if pd.notna(row.get(rating_col)):
                    rating_data.append([
                        row['latitude'],
                        row['longitude'],
                        float(row[rating_col])
                    ])

            if rating_data:
                rating_layer = folium.FeatureGroup(name='Rating Heat Map', show=False)
                HeatMap(rating_data, radius=20, blur=30, max_zoom=13).add_to(rating_layer)
                rating_layer.add_to(m)

        # Layer 4: Clustered markers (for high density)
        cluster_layer = folium.FeatureGroup(name='Clustered View', show=False)
        marker_cluster = MarkerCluster().add_to(cluster_layer)

        for _, row in map_data.iterrows():
            tooltip = self._create_tooltip(row)

            folium.Marker(
                location=[row['latitude'], row['longitude']],
                tooltip=tooltip,
                popup=self._create_rich_popup(row),
            ).add_to(marker_cluster)

        cluster_layer.add_to(m)

        # Layer 5: Circle markers sized by visit count
        if 'visit_count' in map_data.columns:
            circle_layer = folium.FeatureGroup(name='Visit Count (Sized)', show=False)

            for _, row in map_data.iterrows():
                if pd.notna(row.get('visit_count', 0)):
                    radius = np.log1p(row['visit_count']) * 3 + 5  # Log scale for size

                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=radius,
                        popup=self._create_rich_popup(row),
                        tooltip=self._create_tooltip(row),
                        color='blue',
                        fill=True,
                        fillColor='blue',
                        fillOpacity=0.4,
                    ).add_to(circle_layer)

            circle_layer.add_to(m)

        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)

        # Add custom legend
        legend_html = self._create_legend()
        m.get_root().html.add_child(folium.Element(legend_html))

        # Save map
        map_path = self.output_dir / map_name
        m.save(str(map_path))

        logger.info(f"Map saved to: {map_path}")
        return map_path

    def _create_rich_popup(self, row: pd.Series) -> str:
        """Create detailed HTML popup for an onsen marker."""
        html = ['<div style="font-family: Arial, sans-serif; width: 350px;">']

        # Title
        name = row.get('name', 'Unknown Onsen')
        html.append(f'<h3 style="margin: 0 0 10px 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">{name}</h3>')

        # Location info
        if pd.notna(row.get('region')):
            html.append(f'<p style="margin: 5px 0;"><strong>📍 Region:</strong> {row["region"]}</p>')

        if pd.notna(row.get('address')):
            html.append(f'<p style="margin: 5px 0; font-size: 0.9em; color: #666;">{row["address"]}</p>')

        html.append('<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">')

        # Ratings section
        html.append('<div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; margin: 5px 0;">')

        if pd.notna(row.get('personal_rating')):
            rating = row['personal_rating']
            stars = '★' * int(rating) + '☆' * (10 - int(rating))
            html.append(f'<p style="margin: 3px 0;"><strong>⭐ Personal Rating:</strong> {rating:.1f}/10</p>')
            html.append(f'<p style="margin: 3px 0; color: #f39c12; font-size: 1.2em;">{stars}</p>')

        if pd.notna(row.get('avg_rating')):
            html.append(f'<p style="margin: 3px 0;"><strong>📊 Average Rating:</strong> {row["avg_rating"]:.2f}/10</p>')

        # Individual ratings
        rating_fields = {
            'cleanliness_rating': '🧹 Cleanliness',
            'atmosphere_rating': '🎨 Atmosphere',
            'view_rating': '🌄 View',
            'sauna_rating': '🧖 Sauna',
            'outdoor_bath_rating': '🏞️ Outdoor Bath',
        }

        for field, label in rating_fields.items():
            if pd.notna(row.get(field)):
                html.append(f'<p style="margin: 2px 0; font-size: 0.9em;">{label}: {row[field]:.1f}/10</p>')

        html.append('</div>')

        # Visit statistics
        if pd.notna(row.get('visit_count')) or pd.notna(row.get('onsen_visit_count')):
            visit_count = row.get('visit_count', row.get('onsen_visit_count', 0))
            if visit_count > 0:
                html.append(f'<p style="margin: 5px 0;"><strong>🔄 Visits:</strong> {int(visit_count)} time(s)</p>')

        # Pricing
        if pd.notna(row.get('entry_fee_yen')):
            fee = row['entry_fee_yen']
            html.append(f'<p style="margin: 5px 0;"><strong>💰 Entry Fee:</strong> ¥{int(fee)}</p>')

        if pd.notna(row.get('avg_entry_fee')):
            html.append(f'<p style="margin: 5px 0; font-size: 0.9em;">Average fee: ¥{int(row["avg_entry_fee"])}</p>')

        # Stay duration
        if pd.notna(row.get('avg_stay_length')):
            html.append(f'<p style="margin: 5px 0;"><strong>⏱️ Avg Stay:</strong> {int(row["avg_stay_length"])} min</p>')

        # Heart rate data
        if pd.notna(row.get('average_heart_rate')):
            hr = row['average_heart_rate']
            html.append('<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">')
            html.append('<div style="background-color: #ffe6e6; padding: 8px; border-radius: 4px; margin: 5px 0;">')
            html.append(f'<p style="margin: 3px 0;"><strong>❤️ Avg Heart Rate:</strong> {hr:.0f} bpm</p>')

            if pd.notna(row.get('min_heart_rate')) and pd.notna(row.get('max_heart_rate')):
                html.append(f'<p style="margin: 3px 0; font-size: 0.9em;">Range: {row["min_heart_rate"]:.0f} - {row["max_heart_rate"]:.0f} bpm</p>')

            html.append('</div>')

        # Facilities
        facilities = []
        if row.get('had_sauna'):
            facilities.append('🧖 Sauna')
        if row.get('had_outdoor_bath'):
            facilities.append('🏞️ Outdoor Bath')
        if row.get('had_rest_area'):
            facilities.append('🛋️ Rest Area')
        if row.get('had_food_service'):
            facilities.append('🍜 Food')

        if facilities:
            html.append('<hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">')
            html.append(f'<p style="margin: 5px 0;"><strong>Facilities:</strong> {" • ".join(facilities)}</p>')

        # Spring quality
        if pd.notna(row.get('spring_quality')):
            html.append(f'<p style="margin: 5px 0; font-size: 0.9em;"><strong>Spring Quality:</strong> {row["spring_quality"]}</p>')

        # Last visit
        if pd.notna(row.get('last_visit')):
            html.append(f'<p style="margin: 5px 0; font-size: 0.85em; color: #666;"><em>Last visit: {row["last_visit"]}</em></p>')

        html.append('</div>')

        return ''.join(html)

    def _create_tooltip(self, row: pd.Series) -> str:
        """Create concise tooltip for quick preview."""
        name = row.get('name', 'Unknown')
        rating = row.get('personal_rating', row.get('avg_rating'))

        if pd.notna(rating):
            return f"{name} - ⭐ {rating:.1f}/10"
        else:
            return name

    def _create_legend(self) -> str:
        """Create legend for map."""
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; right: 50px; width: 180px; height: auto;
                    background-color: white; z-index:9999; font-size:14px;
                    border:2px solid grey; border-radius: 5px; padding: 10px;">
            <p style="margin: 0 0 8px 0; font-weight: bold;">Rating Legend</p>
            <p style="margin: 3px 0;"><span style="color: darkgreen;">●</span> Excellent (9+)</p>
            <p style="margin: 3px 0;"><span style="color: green;">●</span> Very Good (7.5-9)</p>
            <p style="margin: 3px 0;"><span style="color: orange;">●</span> Good (6-7.5)</p>
            <p style="margin: 3px 0;"><span style="color: red;">●</span> Below 6</p>
            <p style="margin: 3px 0;"><span style="color: gray;">●</span> No rating</p>
        </div>
        '''
        return legend_html

    def create_rating_heatmap(
        self,
        data: pd.DataFrame,
        map_name: str = "rating_heatmap.html",
    ) -> Path:
        """
        Create heat map specifically for ratings.

        Args:
            data: DataFrame with coordinate and rating data
            map_name: Output filename

        Returns:
            Path to generated map
        """
        import folium
        from folium.plugins import HeatMap

        map_data = data.dropna(subset=['latitude', 'longitude']).copy()

        # Determine rating column
        rating_col = None
        for col in ['personal_rating', 'avg_rating', 'onsen_avg_rating']:
            if col in map_data.columns:
                rating_col = col
                break

        if not rating_col:
            logger.warning("No rating column found")
            return None

        # Create base map
        center = (map_data['latitude'].mean(), map_data['longitude'].mean())
        m = folium.Map(location=center, zoom_start=12)

        # Prepare heat data
        heat_data = []
        for _, row in map_data.iterrows():
            if pd.notna(row[rating_col]):
                heat_data.append([
                    row['latitude'],
                    row['longitude'],
                    float(row[rating_col])
                ])

        if heat_data:
            HeatMap(
                heat_data,
                radius=30,
                blur=40,
                max_zoom=13,
                gradient={
                    0.0: 'blue',
                    0.5: 'yellow',
                    0.7: 'orange',
                    1.0: 'red'
                }
            ).add_to(m)

        # Save
        map_path = self.output_dir / map_name
        m.save(str(map_path))

        logger.info(f"Rating heatmap saved to: {map_path}")
        return map_path

    def create_cluster_visualization(
        self,
        data: pd.DataFrame,
        cluster_labels: np.ndarray,
        map_name: str = "cluster_analysis.html",
    ) -> Path:
        """
        Create map visualizing cluster assignments.

        Args:
            data: DataFrame with coordinates
            cluster_labels: Array of cluster assignments from K-means/DBSCAN
            map_name: Output filename

        Returns:
            Path to generated map
        """
        import folium

        map_data = data.dropna(subset=['latitude', 'longitude']).copy()
        map_data['cluster'] = cluster_labels[:len(map_data)]

        # Color palette for clusters
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
                  'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
                  'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen']

        center = (map_data['latitude'].mean(), map_data['longitude'].mean())
        m = folium.Map(location=center, zoom_start=12)

        # Add markers colored by cluster
        for _, row in map_data.iterrows():
            cluster = int(row['cluster'])
            if cluster == -1:  # DBSCAN noise points
                color = 'gray'
            else:
                color = colors[cluster % len(colors)]

            popup_text = f"<b>{row.get('name', 'Unknown')}</b><br>Cluster: {cluster}"

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                popup=popup_text,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.6,
            ).add_to(m)

        # Save
        map_path = self.output_dir / map_name
        m.save(str(map_path))

        logger.info(f"Cluster visualization saved to: {map_path}")
        return map_path
