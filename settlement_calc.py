import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class SettlementCalculator:
    """
    Settlement calculation engine for immediate and consolidation settlement.
    Based on elastic theory and Terzaghi's consolidation theory.
    """
    
    def __init__(self):
        pass
    
    def calculate_stress_increase(self, load: float, footing_width: float, 
                                 footing_length: float, depth_below_footing: float,
                                 layer_thickness: float) -> float:
        """
        Calculate stress increase at depth using Boussinesq elastic theory.
        Simplified using 2:1 method for rectangular footings.
        
        Parameters:
        - load: Applied load in kN
        - footing_width: Width of footing in m
        - footing_length: Length of footing in m  
        - depth_below_footing: Depth to layer center below footing base (z) in m
        - layer_thickness: Thickness of layer in m
        
        Returns:
        - Average stress increase in the layer (kPa)
        
        Note: Returns 0 for any layer with top above or at footing base.
        Stress only spreads below the footing base.
        """
        # Contact pressure
        q0 = load / (footing_width * footing_length)
        
        # Calculate depths to top and bottom of layer
        depth_to_top = depth_below_footing - layer_thickness / 2
        depth_to_bottom = depth_below_footing + layer_thickness / 2
        
        # If entire layer or any part of layer is above footing base, no stress
        if depth_to_top <= 0:
            return 0.0
        
        # Both top and bottom are below footing base
        # 2:1 distribution method: stress spreads at 2V:1H ratio from footing base
        width_at_top = footing_width + depth_to_top
        length_at_top = footing_length + depth_to_top
        width_at_bottom = footing_width + depth_to_bottom
        length_at_bottom = footing_length + depth_to_bottom
        
        # Stress at top and bottom of layer
        delta_sigma_top = q0 * (footing_width * footing_length) / (width_at_top * length_at_top)
        delta_sigma_bottom = q0 * (footing_width * footing_length) / (width_at_bottom * length_at_bottom)
        
        # Average stress over the layer
        delta_sigma_avg = (delta_sigma_top + delta_sigma_bottom) / 2
        
        return delta_sigma_avg
    
    def calculate_immediate_settlement(self, layers_params: pd.DataFrame, 
                                      load: float, footing_width: float,
                                      footing_length: float,
                                      footing_depth: float = 0.0,
                                      poisson_ratio: float = 0.3) -> Dict:
        """
        Calculate immediate (elastic) settlement.
        
        S_immediate = Σ (Δσ * H * (1 - ν²) / E) for each layer
        
        where:
        - Δσ = stress increase in layer
        - H = layer thickness
        - ν = Poisson's ratio
        - E = Young's modulus
        """
        if len(layers_params) == 0:
            return {'total_settlement': 0, 'layer_settlements': []}
        
        layer_settlements = []
        total_settlement = 0
        
        # Cumulative depth from ground surface
        cumulative_depth = footing_depth
        
        for _, layer in layers_params.iterrows():
            # Depth to center of layer from ground surface
            layer_mid_depth_from_surface = cumulative_depth + layer['thickness'] / 2
            
            # Depth below footing base (measured from footing base, not surface)
            depth_below_footing = layer_mid_depth_from_surface - footing_depth
            
            # Stress increase (using depth below footing)
            delta_sigma = self.calculate_stress_increase(
                load, footing_width, footing_length, 
                depth_below_footing, layer['thickness']
            )
            
            # Young's modulus
            E = layer['youngs_modulus']
            
            # Settlement of this layer (elastic) with Poisson's ratio correction
            # S = Δσ * H * (1 - ν²) / E
            elastic_correction = 1 - poisson_ratio**2
            layer_settlement = (delta_sigma * layer['thickness'] * elastic_correction * 1000) / E  # in mm
            
            layer_settlements.append({
                'layer_number': layer['layer_number'],
                'soil_type': layer['soil_type'],
                'settlement_mm': layer_settlement,
                'stress_increase_kPa': delta_sigma,
                'E_kPa': E
            })
            
            total_settlement += layer_settlement
            cumulative_depth += layer['thickness']
        
        return {
            'total_settlement_mm': total_settlement,
            'layer_settlements': layer_settlements
        }
    
    def calculate_consolidation_settlement(self, layers_params: pd.DataFrame,
                                          load: float, footing_width: float,
                                          footing_length: float,
                                          footing_depth: float = 0.0,
                                          water_table_depth: float = 2.0) -> Dict:
        """
        Calculate consolidation settlement for clay layers.
        
        For normally consolidated (σ'0 + Δσ <= σ'p):
            S_c = (Cr * H / (1 + e0)) * log10(σ'p / σ'0) + 
                  (Cc * H / (1 + e0)) * log10((σ'0 + Δσ) / σ'p)
        
        For overconsolidated (σ'0 + Δσ > σ'p):
            S_c = (Cc * H / (1 + e0)) * log10((σ'0 + Δσ) / σ'0)
        
        where:
        - Cc = compression index
        - Cr = recompression index
        - H = layer thickness
        - e0 = initial void ratio (estimated)
        - σ'0 = initial effective stress
        - σ'p = preconsolidation pressure
        - Δσ = stress increase
        """
        if len(layers_params) == 0:
            return {'total_settlement': 0, 'layer_settlements': []}
        
        layer_settlements = []
        total_settlement = 0
        
        cumulative_depth = footing_depth
        gamma_soil = 18.0  # kN/m³
        gamma_water = 9.81  # kN/m³
        
        for _, layer in layers_params.iterrows():
            # Only calculate for clay-like soils (Ic > 2.6)
            if layer['Ic'] < 2.6:
                layer_settlements.append({
                    'layer_number': layer['layer_number'],
                    'soil_type': layer['soil_type'],
                    'settlement_mm': 0.0,
                    'note': 'Granular soil - no consolidation settlement'
                })
                cumulative_depth += layer['thickness']
                continue
            
            # Depth to center of layer from ground surface
            layer_mid_depth_from_surface = cumulative_depth + layer['thickness'] / 2
            
            # Initial effective stress at mid-depth
            sigma_v0 = gamma_soil * layer_mid_depth_from_surface
            if layer_mid_depth_from_surface > water_table_depth:
                u0 = gamma_water * (layer_mid_depth_from_surface - water_table_depth)
            else:
                u0 = 0
            sigma_v0_prime = sigma_v0 - u0
            
            # Depth below footing base (measured from footing base, not surface)
            depth_below_footing = layer_mid_depth_from_surface - footing_depth
            
            # Stress increase (using depth below footing)
            delta_sigma = self.calculate_stress_increase(
                load, footing_width, footing_length,
                depth_below_footing, layer['thickness']
            )
            
            # Preconsolidation pressure from OCR
            OCR = layer['OCR']
            sigma_p = sigma_v0_prime * OCR
            
            # Compression and recompression indices
            Cc = layer['compression_index']
            Cr = layer['recompression_index']
            
            # Estimate void ratio from Ic and soil type
            # Higher Ic (clay) typically has higher void ratio
            if layer['Ic'] > 3.5:
                e0 = 1.0  # Soft clay
            elif layer['Ic'] > 3.0:
                e0 = 0.8  # Medium clay
            else:
                e0 = 0.6  # Stiff silt/clay
            
            # Calculate settlement based on stress state
            H_meters = layer['thickness']
            
            if sigma_v0_prime + delta_sigma <= sigma_p:
                # Overconsolidated - all in recompression range
                S_c = (Cr * H_meters / (1 + e0)) * np.log10((sigma_v0_prime + delta_sigma) / sigma_v0_prime)
                condition = "Overconsolidated (recompression only)"
            else:
                if sigma_v0_prime < sigma_p:
                    # Starts overconsolidated, becomes normally consolidated
                    S_c_recomp = (Cr * H_meters / (1 + e0)) * np.log10(sigma_p / sigma_v0_prime)
                    S_c_virgin = (Cc * H_meters / (1 + e0)) * np.log10((sigma_v0_prime + delta_sigma) / sigma_p)
                    S_c = S_c_recomp + S_c_virgin
                    condition = "Overconsolidated to normally consolidated"
                else:
                    # Normally consolidated
                    S_c = (Cc * H_meters / (1 + e0)) * np.log10((sigma_v0_prime + delta_sigma) / sigma_v0_prime)
                    condition = "Normally consolidated"
            
            # Convert to mm
            S_c_mm = S_c * 1000
            
            layer_settlements.append({
                'layer_number': layer['layer_number'],
                'soil_type': layer['soil_type'],
                'settlement_mm': S_c_mm,
                'stress_increase_kPa': delta_sigma,
                'initial_stress_kPa': sigma_v0_prime,
                'preconsolidation_kPa': sigma_p,
                'OCR': OCR,
                'Cc': Cc,
                'Cr': Cr,
                'condition': condition
            })
            
            total_settlement += S_c_mm
            cumulative_depth += layer['thickness']
        
        return {
            'total_settlement_mm': total_settlement,
            'layer_settlements': layer_settlements
        }
    
    def calculate_total_settlement(self, layers_params: pd.DataFrame,
                                  load: float, footing_width: float,
                                  footing_length: float,
                                  footing_depth: float = 0.0,
                                  water_table_depth: float = 2.0) -> Dict:
        """
        Calculate total settlement (immediate + consolidation).
        """
        immediate = self.calculate_immediate_settlement(
            layers_params, load, footing_width, footing_length, footing_depth
        )
        
        consolidation = self.calculate_consolidation_settlement(
            layers_params, load, footing_width, footing_length, 
            footing_depth, water_table_depth
        )
        
        total = immediate['total_settlement_mm'] + consolidation['total_settlement_mm']
        
        return {
            'immediate_settlement_mm': immediate['total_settlement_mm'],
            'consolidation_settlement_mm': consolidation['total_settlement_mm'],
            'total_settlement_mm': total,
            'immediate_details': immediate['layer_settlements'],
            'consolidation_details': consolidation['layer_settlements']
        }
    
    def estimate_time_settlement(self, layers_params: pd.DataFrame,
                                load: float, footing_width: float,
                                footing_length: float,
                                time_years: float = 1.0,
                                footing_depth: float = 0.0,
                                water_table_depth: float = 2.0) -> Dict:
        """
        Estimate settlement at a given time using consolidation theory.
        
        Uses average degree of consolidation (U) based on time factor (Tv).
        """
        consolidation = self.calculate_consolidation_settlement(
            layers_params, load, footing_width, footing_length,
            footing_depth, water_table_depth
        )
        
        total_time_settlement = 0
        layer_time_settlements = []
        
        for layer_detail in consolidation['layer_settlements']:
            if 'Cc' not in layer_detail:
                # Granular layer - immediate settlement only
                layer_time_settlements.append({
                    'layer_number': layer_detail['layer_number'],
                    'settlement_mm': 0.0,
                    'degree_consolidation': 1.0
                })
                continue
            
            # Get layer info
            layer_idx = int(layer_detail['layer_number']) - 1
            layer = layers_params.iloc[layer_idx]
            
            # Permeability and thickness
            k = layer['permeability']  # m/s
            H_drainage = layer['thickness'] / 2  # Assume double drainage
            
            # Coefficient of consolidation
            # cv = k / (gamma_w * mv)
            # mv = (1 + e0) / (Cc * sigma_v')  approximation
            gamma_w = 9.81  # kN/m³
            Cc = layer_detail['Cc']
            sigma_v_prime = layer_detail['initial_stress_kPa']
            e0 = 0.8  # Assumed
            
            mv = Cc / ((1 + e0) * sigma_v_prime * np.log(10))  # m²/kN
            cv = k / (gamma_w * mv)  # m²/s
            
            # Time factor
            time_seconds = time_years * 365.25 * 24 * 3600
            Tv = cv * time_seconds / (H_drainage ** 2)
            
            # Degree of consolidation (Terzaghi theory)
            # Correct formula: U = 1 - (8/π²) * exp(-π²*Tv/4)
            if Tv < 0.217:
                U = np.sqrt(4 * Tv / np.pi)
            else:
                U = 1 - (8 / (np.pi ** 2)) * np.exp(-np.pi ** 2 * Tv / 4)
            
            U = min(U, 1.0)
            
            settlement_at_time = layer_detail['settlement_mm'] * U
            total_time_settlement += settlement_at_time
            
            layer_time_settlements.append({
                'layer_number': layer_detail['layer_number'],
                'settlement_mm': settlement_at_time,
                'degree_consolidation': U,
                'time_factor': Tv
            })
        
        return {
            'time_years': time_years,
            'total_settlement_mm': total_time_settlement,
            'layer_settlements': layer_time_settlements
        }
    
    def generate_time_settlement_curve(self, layers_params: pd.DataFrame,
                                      load: float, footing_width: float,
                                      footing_length: float,
                                      max_time_years: float = 50.0,
                                      num_points: int = 100,
                                      footing_depth: float = 0.0,
                                      water_table_depth: float = 2.0,
                                      include_secondary: bool = True,
                                      c_alpha: float = 0.02) -> Dict:
        """
        Generate settlement vs time curve for consolidation analysis.
        
        Parameters:
        - max_time_years: Maximum time to simulate (years)
        - num_points: Number of time points to calculate
        - include_secondary: Whether to include secondary compression (creep)
        - c_alpha: Secondary compression index (C_alpha / Cc ratio, typical 0.02-0.05)
        
        Returns:
        - Dictionary with time arrays and settlement data
        """
        # Get immediate settlement (happens instantaneously)
        immediate = self.calculate_immediate_settlement(
            layers_params, load, footing_width, footing_length, footing_depth
        )
        
        # Get final consolidation settlement
        consolidation = self.calculate_consolidation_settlement(
            layers_params, load, footing_width, footing_length,
            footing_depth, water_table_depth
        )
        
        # Generate time points (logarithmic spacing for better resolution)
        time_points = np.logspace(-3, np.log10(max_time_years), num_points)  # From 0.001 to max_time_years
        
        # Arrays to store results
        settlement_primary = []
        settlement_with_secondary = []
        layer_contributions = {i: [] for i in range(len(layers_params))}
        
        for time_years in time_points:
            # Calculate total settlement at this time (immediate + time-dependent consolidation)
            # Start at 0 and add each layer's contribution once
            total_primary = 0
            
            for idx, layer_detail in enumerate(consolidation['layer_settlements']):
                # Get immediate settlement for this layer
                layer_immediate = 0
                if idx < len(immediate['layer_settlements']):
                    layer_immediate = immediate['layer_settlements'][idx]['settlement_mm']
                
                if 'Cc' not in layer_detail:
                    # Granular layer - only immediate settlement (no consolidation)
                    layer_settlement = layer_immediate
                else:
                    # Clay layer - calculate time-dependent consolidation
                    layer_idx = int(layer_detail['layer_number']) - 1
                    layer = layers_params.iloc[layer_idx]
                    
                    # Permeability and drainage conditions
                    k = layer['permeability']  # m/s
                    H_drainage = layer['thickness'] / 2  # Assume double drainage
                    
                    # Coefficient of consolidation
                    gamma_w = 9.81  # kN/m³
                    Cc = layer_detail['Cc']
                    sigma_v_prime = layer_detail['initial_stress_kPa']
                    e0 = 0.8  # Assumed
                    
                    mv = Cc / ((1 + e0) * sigma_v_prime * np.log(10))  # m²/kN
                    cv = k / (gamma_w * mv)  # m²/s
                    
                    # Time factor
                    time_seconds = time_years * 365.25 * 24 * 3600
                    Tv = cv * time_seconds / (H_drainage ** 2)
                    
                    # Degree of consolidation (Terzaghi theory)
                    # Correct formula: U = 1 - (8/π²) * exp(-π²*Tv/4)
                    if Tv < 0.217:
                        U = np.sqrt(4 * Tv / np.pi)
                    else:
                        U = 1 - (8 / (np.pi ** 2)) * np.exp(-np.pi ** 2 * Tv / 4)
                    U = min(U, 1.0)
                    
                    # Layer settlement = immediate + (consolidation settlement * degree of consolidation)
                    layer_settlement = layer_immediate + layer_detail['settlement_mm'] * U
                
                total_primary += layer_settlement
                layer_contributions[idx].append(layer_settlement)
            
            settlement_primary.append(total_primary)
            
            # Add secondary compression (creep) if requested
            if include_secondary:
                # Secondary compression starts after primary consolidation
                # S_secondary = C_alpha * H * log10(t/t_p)
                # where t_p is time for primary consolidation (typically at U = 90%)
                
                secondary_settlement = 0
                for layer_detail in consolidation['layer_settlements']:
                    if 'Cc' not in layer_detail:
                        continue
                    
                    layer_idx = int(layer_detail['layer_number']) - 1
                    layer = layers_params.iloc[layer_idx]
                    
                    # Estimate time for 90% consolidation
                    k = layer['permeability']
                    H_drainage = layer['thickness'] / 2
                    Cc = layer_detail['Cc']
                    sigma_v_prime = layer_detail['initial_stress_kPa']
                    e0 = 0.8
                    mv = Cc / ((1 + e0) * sigma_v_prime * np.log(10))
                    cv = k / (9.81 * mv)
                    
                    # Tv for 90% consolidation ≈ 0.848
                    t_p_seconds = 0.848 * (H_drainage ** 2) / cv
                    t_p_years = t_p_seconds / (365.25 * 24 * 3600)
                    
                    # Secondary compression only occurs after primary
                    if time_years > t_p_years:
                        C_alpha = c_alpha * Cc  # Secondary compression index
                        H_meters = layer['thickness']
                        S_secondary = (C_alpha * H_meters / (1 + e0)) * np.log10(time_years / t_p_years)
                        secondary_settlement += S_secondary * 1000  # Convert to mm
                
                settlement_with_secondary.append(total_primary + secondary_settlement)
            else:
                settlement_with_secondary.append(total_primary)
        
        return {
            'time_years': time_points.tolist(),
            'settlement_primary_mm': settlement_primary,
            'settlement_total_mm': settlement_with_secondary,
            'immediate_settlement_mm': immediate['total_settlement_mm'],
            'final_consolidation_mm': consolidation['total_settlement_mm'],
            'layer_contributions': layer_contributions,
            'secondary_compression_included': include_secondary,
            'c_alpha': c_alpha if include_secondary else 0
        }
    
    def calculate_consolidation_time(self, layers_params: pd.DataFrame,
                                    target_degree: float = 0.90) -> Dict:
        """
        Calculate time required to achieve a target degree of consolidation.
        
        Parameters:
        - target_degree: Target degree of consolidation (0-1), typically 0.90
        
        Returns:
        - Dictionary with consolidation times for each layer
        """
        # Time factor for different degrees of consolidation
        if target_degree < 0.5:
            Tv_target = (np.pi / 4) * (target_degree ** 2)
        elif target_degree < 0.60:
            Tv_target = 0.197
        elif target_degree < 0.90:
            # Interpolate
            Tv_target = -0.933 * np.log10(1 - target_degree)
        else:
            Tv_target = -0.933 * np.log10(1 - target_degree)
        
        layer_times = []
        
        for _, layer in layers_params.iterrows():
            # Only for clay layers
            if layer['Ic'] < 2.6:
                layer_times.append({
                    'layer_number': layer['layer_number'],
                    'soil_type': layer['soil_type'],
                    'time_years': 0,
                    'note': 'Granular soil - immediate settlement'
                })
                continue
            
            # Drainage conditions
            k = layer['permeability']  # m/s
            H_drainage = layer['thickness'] / 2  # Assume double drainage
            
            # Estimate consolidation parameters
            gamma_w = 9.81  # kN/m³
            # Estimate Cc from Ic
            Ic = layer['Ic']
            Cc = max(0.009 * (Ic - 1.5), 0.05)
            
            # Estimate effective stress
            depth = layer['top_depth'] + layer['thickness'] / 2
            sigma_v_prime = 18.0 * depth - 9.81 * max(0, depth - 2.0)
            
            e0 = 0.8
            mv = Cc / ((1 + e0) * sigma_v_prime * np.log(10))
            cv = k / (gamma_w * mv)  # m²/s
            
            # Time for target consolidation
            time_seconds = Tv_target * (H_drainage ** 2) / cv
            time_years = time_seconds / (365.25 * 24 * 3600)
            
            layer_times.append({
                'layer_number': layer['layer_number'],
                'soil_type': layer['soil_type'],
                'thickness_m': layer['thickness'],
                'permeability_m_s': k,
                'cv_m2_s': cv,
                'time_years': time_years,
                'time_days': time_years * 365.25,
                'target_degree': target_degree
            })
        
        return {
            'target_degree': target_degree,
            'layer_times': layer_times
        }
