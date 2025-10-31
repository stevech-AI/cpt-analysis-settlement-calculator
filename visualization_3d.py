"""
3D Visualization module for spatial CPT analysis.
Displays multiple CPT locations with soil layer variations in 3D space.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class CPT3DVisualizer:
    """
    Create 3D visualizations of multiple CPT locations showing spatial soil variations.
    """
    
    def __init__(self):
        """Initialize 3D visualizer with soil type color mapping."""
        self.soil_colors = {
            'Sensitive, fine grained': '#8B4513',
            'Clay - organic soil': '#654321',
            'Clay': '#A0522D',
            'Silt mixtures - clayey silt to silty clay': '#CD853F',
            'Sand mixtures - silty sand to sandy silt': '#DEB887',
            'Sands - clean sand to silty sand': '#F4A460',
            'Dense sand to gravelly sand': '#FFD700',
            'Very stiff sand to clayey sand': '#FFA500',
            'Very stiff, over-consolidated or cemented': '#FF8C00'
        }
        
        # Numeric mapping for interpolation
        self.soil_type_numeric = {
            'Sensitive, fine grained': 1,
            'Clay - organic soil': 2,
            'Clay': 3,
            'Silt mixtures - clayey silt to silty clay': 4,
            'Sand mixtures - silty sand to sandy silt': 5,
            'Sands - clean sand to silty sand': 6,
            'Dense sand to gravelly sand': 7,
            'Very stiff sand to clayey sand': 8,
            'Very stiff, over-consolidated or cemented': 9
        }
    
    def create_3d_soil_profile(self, cpt_locations):
        """
        Create 3D visualization of soil profiles at multiple CPT locations.
        
        Parameters:
        -----------
        cpt_locations : dict
            Dictionary with CPT names as keys and values containing:
            - 'x': X coordinate (m)
            - 'y': Y coordinate (m)
            - 'data': DataFrame with depth and soil_type columns
            - 'layers': Layer information
        
        Returns:
        --------
        fig : plotly figure
            3D visualization figure
        """
        fig = go.Figure()
        
        # Add each CPT as a 3D scatter trace
        for cpt_name, cpt_info in cpt_locations.items():
            x_coord = cpt_info['x']
            y_coord = cpt_info['y']
            data = cpt_info['data']
            
            # Create arrays for 3D plotting
            x_points = np.full(len(data), x_coord)
            y_points = np.full(len(data), y_coord)
            z_points = -data['depth'].values  # Negative for downward depth
            
            # Map soil types to colors
            colors = [self.soil_colors.get(st, '#808080') for st in data['soil_type']]
            
            # Add scatter trace for this CPT
            fig.add_trace(go.Scatter3d(
                x=x_points,
                y=y_points,
                z=z_points,
                mode='markers',
                marker=dict(
                    size=4,
                    color=colors,
                    line=dict(width=0.5, color='white')
                ),
                name=cpt_name,
                text=[f"Depth: {d:.2f}m<br>Soil: {st}" 
                      for d, st in zip(data['depth'], data['soil_type'])],
                hoverinfo='text'
            ))
        
        # Update layout
        fig.update_layout(
            title='3D Spatial CPT Soil Profile Visualization',
            scene=dict(
                xaxis_title='X Coordinate (m)',
                yaxis_title='Y Coordinate (m)',
                zaxis_title='Depth (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            height=700,
            showlegend=True
        )
        
        return fig
    
    def create_layer_surfaces(self, cpt_locations, target_layers=None):
        """
        Create 3D surface visualization showing interpolated layer boundaries.
        
        Parameters:
        -----------
        cpt_locations : dict
            Dictionary with CPT data and coordinates
        target_layers : list, optional
            List of layer indices to visualize (default: all layers)
        
        Returns:
        --------
        fig : plotly figure
            3D surface visualization
        """
        fig = go.Figure()
        
        # Extract coordinates and layer data
        x_coords = []
        y_coords = []
        layer_depths = {}
        
        for cpt_name, cpt_info in cpt_locations.items():
            x_coords.append(cpt_info['x'])
            y_coords.append(cpt_info['y'])
            
            # Get layer top/bottom depths
            layers = cpt_info['layers']
            for i, layer in enumerate(layers):
                layer_key = f"layer_{i}"
                if layer_key not in layer_depths:
                    layer_depths[layer_key] = {
                        'top': [],
                        'bottom': [],
                        'soil_type': layer['soil_type']
                    }
                layer_depths[layer_key]['top'].append(layer['depth_top'])
                layer_depths[layer_key]['bottom'].append(layer['depth_bottom'])
        
        # Convert to arrays
        x_coords = np.array(x_coords)
        y_coords = np.array(y_coords)
        
        # Create grid for interpolation
        if len(x_coords) >= 3:
            xi = np.linspace(x_coords.min(), x_coords.max(), 50)
            yi = np.linspace(y_coords.min(), y_coords.max(), 50)
            xi, yi = np.meshgrid(xi, yi)
            
            # Interpolate layer surfaces
            from scipy.interpolate import griddata
            
            for layer_key, layer_data in layer_depths.items():
                if target_layers and layer_key not in target_layers:
                    continue
                
                # Interpolate top surface
                z_top = griddata(
                    (x_coords, y_coords),
                    -np.array(layer_data['top']),
                    (xi, yi),
                    method='linear'
                )
                
                # Get color for this soil type
                soil_type = layer_data['soil_type']
                color = self.soil_colors.get(soil_type, '#808080')
                
                # Add surface
                fig.add_trace(go.Surface(
                    x=xi,
                    y=yi,
                    z=z_top,
                    colorscale=[[0, color], [1, color]],
                    showscale=False,
                    name=f"{layer_key}: {soil_type}",
                    opacity=0.7,
                    hovertemplate='X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Depth: %{z:.2f}m<extra></extra>'
                ))
        else:
            # Not enough points for surface interpolation, add vertical columns
            for i, (x, y) in enumerate(zip(x_coords, y_coords)):
                cpt_name = list(cpt_locations.keys())[i]
                layers = cpt_locations[cpt_name]['layers']
                
                for j, layer in enumerate(layers):
                    z_vals = [-layer['depth_top'], -layer['depth_bottom']]
                    color = self.soil_colors.get(layer['soil_type'], '#808080')
                    
                    fig.add_trace(go.Scatter3d(
                        x=[x, x],
                        y=[y, y],
                        z=z_vals,
                        mode='lines+markers',
                        line=dict(color=color, width=8),
                        marker=dict(size=6, color=color),
                        name=f"{cpt_name} - {layer['soil_type']}",
                        showlegend=(i == 0 and j == 0)
                    ))
        
        fig.update_layout(
            title='3D Layer Surface Interpolation',
            scene=dict(
                xaxis_title='X Coordinate (m)',
                yaxis_title='Y Coordinate (m)',
                zaxis_title='Depth (m)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2)
                )
            ),
            height=700,
            showlegend=True
        )
        
        return fig
    
    def create_cross_section(self, cpt_locations, start_point, end_point, num_points=100):
        """
        Create a 2D cross-section view between two points.
        
        Parameters:
        -----------
        cpt_locations : dict
            Dictionary with CPT data and coordinates
        start_point : tuple
            (x, y) coordinates of start point
        end_point : tuple
            (x, y) coordinates of end point
        num_points : int
            Number of interpolation points along the cross-section
        
        Returns:
        --------
        fig : plotly figure
            Cross-section visualization
        """
        from scipy.interpolate import griddata
        
        # Create line between points
        x_line = np.linspace(start_point[0], end_point[0], num_points)
        y_line = np.linspace(start_point[1], end_point[1], num_points)
        distance = np.sqrt((x_line - start_point[0])**2 + (y_line - start_point[1])**2)
        
        # Collect all depth data from CPTs
        x_coords = []
        y_coords = []
        depths = []
        soil_types = []
        
        for cpt_name, cpt_info in cpt_locations.items():
            data = cpt_info['data']
            n_points = len(data)
            x_coords.extend([cpt_info['x']] * n_points)
            y_coords.extend([cpt_info['y']] * n_points)
            depths.extend(data['depth'].values)
            soil_types.extend(data['soil_type'].values)
        
        # Convert to numeric soil types for interpolation
        soil_numeric = [self.soil_type_numeric.get(st, 5) for st in soil_types]
        
        # Create depth points for interpolation
        max_depth = max(depths)
        depth_points = np.linspace(0, max_depth, 100)
        
        # Create 2D grid for cross-section
        distance_grid, depth_grid = np.meshgrid(distance, depth_points)
        
        # Interpolate soil types along the cross-section
        soil_values = []
        for d in depth_points:
            depth_array = np.full(num_points, d)
            points_3d = np.column_stack([x_line, y_line, depth_array])
            
            # Interpolate at these points
            interpolated = griddata(
                (x_coords, y_coords, depths),
                soil_numeric,
                (x_line, y_line, depth_array),
                method='nearest'
            )
            soil_values.append(interpolated)
        
        soil_grid = np.array(soil_values)
        
        # Create figure
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            x=distance,
            y=depth_points,
            z=soil_grid,
            colorscale='Earth',
            showscale=True,
            colorbar=dict(title='Soil Type'),
            hovertemplate='Distance: %{x:.1f}m<br>Depth: %{y:.2f}m<extra></extra>'
        ))
        
        # Mark CPT locations on the cross-section
        for cpt_name, cpt_info in cpt_locations.items():
            x_dist = np.sqrt((cpt_info['x'] - start_point[0])**2 + 
                           (cpt_info['y'] - start_point[1])**2)
            
            # Check if CPT is close to the line
            if min(abs(distance - x_dist)) < 1.0:
                fig.add_trace(go.Scatter(
                    x=[x_dist],
                    y=[0],
                    mode='markers+text',
                    marker=dict(size=12, color='red', symbol='triangle-down'),
                    text=[cpt_name],
                    textposition='top center',
                    name=cpt_name,
                    showlegend=False
                ))
        
        fig.update_layout(
            title=f'Cross-Section from ({start_point[0]:.1f}, {start_point[1]:.1f}) to ({end_point[0]:.1f}, {end_point[1]:.1f})',
            xaxis_title='Distance along section (m)',
            yaxis_title='Depth (m)',
            yaxis_autorange='reversed',
            height=600
        )
        
        return fig
    
    def create_plan_view(self, cpt_locations, depth_slice):
        """
        Create a plan view (top-down) showing soil types at a specific depth.
        
        Parameters:
        -----------
        cpt_locations : dict
            Dictionary with CPT data and coordinates
        depth_slice : float
            Depth at which to show the plan view (m)
        
        Returns:
        --------
        fig : plotly figure
            Plan view visualization
        """
        from scipy.interpolate import griddata
        
        x_coords = []
        y_coords = []
        soil_at_depth = []
        
        for cpt_name, cpt_info in cpt_locations.items():
            data = cpt_info['data']
            
            # Find soil type at the specified depth
            idx = (data['depth'] - depth_slice).abs().idxmin()
            soil_type = data.loc[idx, 'soil_type']
            soil_numeric = self.soil_type_numeric.get(soil_type, 5)
            
            x_coords.append(cpt_info['x'])
            y_coords.append(cpt_info['y'])
            soil_at_depth.append(soil_numeric)
        
        x_coords = np.array(x_coords)
        y_coords = np.array(y_coords)
        soil_at_depth = np.array(soil_at_depth)
        
        # Create figure
        fig = go.Figure()
        
        # Determine interpolation method based on number of points
        num_points = len(x_coords)
        
        if num_points >= 4:
            # Use cubic interpolation for 4+ points
            xi = np.linspace(x_coords.min() - 5, x_coords.max() + 5, 100)
            yi = np.linspace(y_coords.min() - 5, y_coords.max() + 5, 100)
            xi, yi = np.meshgrid(xi, yi)
            
            zi = griddata(
                (x_coords, y_coords),
                soil_at_depth,
                (xi, yi),
                method='cubic'
            )
            
            fig.add_trace(go.Contour(
                x=xi[0],
                y=yi[:, 0],
                z=zi,
                colorscale='Earth',
                showscale=True,
                colorbar=dict(title='Soil Type'),
                contours=dict(
                    showlabels=True,
                    labelfont=dict(size=10, color='white')
                )
            ))
        elif num_points == 3:
            # Use linear interpolation for 3 points
            xi = np.linspace(x_coords.min() - 5, x_coords.max() + 5, 100)
            yi = np.linspace(y_coords.min() - 5, y_coords.max() + 5, 100)
            xi, yi = np.meshgrid(xi, yi)
            
            zi = griddata(
                (x_coords, y_coords),
                soil_at_depth,
                (xi, yi),
                method='linear'
            )
            
            fig.add_trace(go.Heatmap(
                x=xi[0],
                y=yi[:, 0],
                z=zi,
                colorscale='Earth',
                showscale=True,
                colorbar=dict(title='Soil Type')
            ))
        else:
            # For 2 or fewer points, create voronoi-like visualization
            # Expand the view around the points
            if num_points == 2:
                # Create a gradient between two points
                x_range = max(abs(x_coords[1] - x_coords[0]), 10)
                y_range = max(abs(y_coords[1] - y_coords[0]), 10)
            else:
                x_range = 10
                y_range = 10
            
            xi = np.linspace(x_coords.min() - x_range/2, x_coords.max() + x_range/2, 100)
            yi = np.linspace(y_coords.min() - y_range/2, y_coords.max() + y_range/2, 100)
            xi, yi = np.meshgrid(xi, yi)
            
            # Use nearest neighbor interpolation for simple visualization
            zi = griddata(
                (x_coords, y_coords),
                soil_at_depth,
                (xi, yi),
                method='nearest'
            )
            
            fig.add_trace(go.Heatmap(
                x=xi[0],
                y=yi[:, 0],
                z=zi,
                colorscale='Earth',
                showscale=True,
                colorbar=dict(title='Soil Type')
            ))
        
        # Add CPT location markers
        cpt_names = list(cpt_locations.keys())
        
        # Create color for markers based on soil type
        marker_colors = [self.soil_colors.get(
            [k for k, v in self.soil_type_numeric.items() if v == st][0] if st in self.soil_type_numeric.values() else 'Unknown',
            '#808080'
        ) for st in soil_at_depth]
        
        fig.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers+text',
            marker=dict(
                size=15,
                color=marker_colors,
                symbol='circle',
                line=dict(width=2, color='white')
            ),
            text=cpt_names,
            textposition='top center',
            name='CPT Locations',
            hovertemplate='<b>%{text}</b><br>X: %{x:.1f}m<br>Y: %{y:.1f}m<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Plan View at Depth = {depth_slice:.2f}m',
            xaxis_title='X Coordinate (m)',
            yaxis_title='Y Coordinate (m)',
            height=600,
            width=700
        )
        
        return fig
