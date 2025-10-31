import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class SoilPropertyDatabase:
    """
    Reference database for typical soil properties based on soil classification.
    Values based on geotechnical engineering literature and standards.
    """
    
    def __init__(self):
        # Database of typical soil properties by soil behavior type
        self.soil_properties = {
            'Sensitive fine grained': {
                'Ic_range': (3.6, 4.0),
                'youngs_modulus_range': (500, 2000),  # kPa
                'compression_index_range': (0.3, 0.6),
                'recompression_index_range': (0.03, 0.08),
                'OCR_range': (1.0, 2.0),
                'friction_angle_range': (0, 0),  # degrees
                'undrained_shear_strength_range': (10, 30),  # kPa
                'permeability_range': (1e-10, 1e-8),  # m/s
                'unit_weight_range': (14, 18),  # kN/m³
                'description': 'Very soft to soft clay, highly compressible'
            },
            'Organic soil': {
                'Ic_range': (3.6, 4.0),
                'youngs_modulus_range': (300, 1500),
                'compression_index_range': (0.4, 0.8),
                'recompression_index_range': (0.04, 0.10),
                'OCR_range': (1.0, 1.5),
                'friction_angle_range': (0, 0),
                'undrained_shear_strength_range': (5, 20),
                'permeability_range': (1e-9, 1e-7),
                'unit_weight_range': (12, 16),
                'description': 'Organic clay and peat, very compressible'
            },
            'Clay': {
                'Ic_range': (2.95, 3.6),
                'youngs_modulus_range': (2000, 8000),
                'compression_index_range': (0.2, 0.5),
                'recompression_index_range': (0.02, 0.06),
                'OCR_range': (1.0, 4.0),
                'friction_angle_range': (20, 28),
                'undrained_shear_strength_range': (20, 80),
                'permeability_range': (1e-10, 1e-8),
                'unit_weight_range': (16, 20),
                'description': 'Soft to stiff clay, moderate compressibility'
            },
            'Silty clay to clay': {
                'Ic_range': (2.95, 3.6),
                'youngs_modulus_range': (3000, 10000),
                'compression_index_range': (0.15, 0.35),
                'recompression_index_range': (0.015, 0.04),
                'OCR_range': (1.0, 6.0),
                'friction_angle_range': (22, 30),
                'undrained_shear_strength_range': (30, 100),
                'permeability_range': (1e-9, 1e-7),
                'unit_weight_range': (17, 21),
                'description': 'Medium stiff clay with silt content'
            },
            'Clayey silt to silty clay': {
                'Ic_range': (2.6, 2.95),
                'youngs_modulus_range': (5000, 15000),
                'compression_index_range': (0.1, 0.25),
                'recompression_index_range': (0.01, 0.03),
                'OCR_range': (1.0, 8.0),
                'friction_angle_range': (24, 32),
                'undrained_shear_strength_range': (40, 120),
                'permeability_range': (1e-8, 1e-6),
                'unit_weight_range': (18, 21),
                'description': 'Stiff silty clay, low to medium compressibility'
            },
            'Sandy silt to clayey silt': {
                'Ic_range': (2.05, 2.6),
                'youngs_modulus_range': (10000, 30000),
                'compression_index_range': (0.05, 0.15),
                'recompression_index_range': (0.005, 0.02),
                'OCR_range': (1.0, 10.0),
                'friction_angle_range': (28, 34),
                'undrained_shear_strength_range': (0, 0),
                'permeability_range': (1e-7, 1e-5),
                'unit_weight_range': (18, 22),
                'description': 'Dense silt mixtures, low compressibility'
            },
            'Silty sand to sandy silt': {
                'Ic_range': (1.8, 2.05),
                'youngs_modulus_range': (15000, 40000),
                'compression_index_range': (0.02, 0.08),
                'recompression_index_range': (0.002, 0.01),
                'OCR_range': (1.0, 15.0),
                'friction_angle_range': (30, 36),
                'undrained_shear_strength_range': (0, 0),
                'permeability_range': (1e-6, 1e-4),
                'unit_weight_range': (19, 22),
                'description': 'Medium to dense silty sand'
            },
            'Sand to silty sand': {
                'Ic_range': (1.31, 1.8),
                'youngs_modulus_range': (20000, 60000),
                'compression_index_range': (0.01, 0.05),
                'recompression_index_range': (0.001, 0.005),
                'OCR_range': (1.0, 20.0),
                'friction_angle_range': (32, 40),
                'undrained_shear_strength_range': (0, 0),
                'permeability_range': (1e-5, 1e-3),
                'unit_weight_range': (19, 23),
                'description': 'Dense sand, very low compressibility'
            },
            'Sand': {
                'Ic_range': (0.0, 1.31),
                'youngs_modulus_range': (30000, 100000),
                'compression_index_range': (0.005, 0.03),
                'recompression_index_range': (0.0005, 0.003),
                'OCR_range': (1.0, 30.0),
                'friction_angle_range': (34, 42),
                'undrained_shear_strength_range': (0, 0),
                'permeability_range': (1e-4, 1e-2),
                'unit_weight_range': (20, 24),
                'description': 'Very dense clean sand, negligible compressibility'
            }
        }
    
    def get_typical_properties(self, soil_type: str) -> Dict:
        """Get typical property ranges for a soil type."""
        return self.soil_properties.get(soil_type, None)
    
    def get_soil_type_from_ic(self, Ic: float) -> str:
        """Determine soil type from Soil Behavior Type Index (Ic)."""
        for soil_type, props in self.soil_properties.items():
            ic_min, ic_max = props['Ic_range']
            if ic_min <= Ic <= ic_max:
                return soil_type
        return "Unknown"
    
    def validate_parameter(self, soil_type: str, parameter_name: str, value: float) -> Tuple[bool, str]:
        """
        Validate if a calculated parameter falls within typical ranges.
        
        Returns:
        - (True, "within range") if value is typical
        - (False, warning_message) if value is outside typical range
        """
        props = self.get_typical_properties(soil_type)
        if props is None:
            return (True, "Unknown soil type")
        
        # Map parameter names to database keys
        param_map = {
            'youngs_modulus': 'youngs_modulus_range',
            'E': 'youngs_modulus_range',
            'compression_index': 'compression_index_range',
            'Cc': 'compression_index_range',
            'recompression_index': 'recompression_index_range',
            'Cr': 'recompression_index_range',
            'OCR': 'OCR_range',
            'friction_angle': 'friction_angle_range',
            'phi': 'friction_angle_range',
            'undrained_shear_strength': 'undrained_shear_strength_range',
            'cu': 'undrained_shear_strength_range',
            'permeability': 'permeability_range',
            'k': 'permeability_range',
            'unit_weight': 'unit_weight_range',
            'gamma': 'unit_weight_range'
        }
        
        range_key = param_map.get(parameter_name)
        if range_key is None or range_key not in props:
            return (True, f"Parameter '{parameter_name}' not in database")
        
        min_val, max_val = props[range_key]
        
        # Allow some tolerance for boundary cases
        tolerance = 0.2  # 20% tolerance
        extended_min = min_val * (1 - tolerance)
        extended_max = max_val * (1 + tolerance)
        
        if min_val <= value <= max_val:
            return (True, "Within typical range")
        elif extended_min <= value <= extended_max:
            return (False, f"⚠️ Near boundary: typical range is {min_val:.2e} to {max_val:.2e}")
        else:
            return (False, f"⚠️ Outside typical range: expected {min_val:.2e} to {max_val:.2e}, got {value:.2e}")
    
    def get_database_summary(self) -> pd.DataFrame:
        """Get a summary dataframe of all soil types and their properties."""
        data = []
        for soil_type, props in self.soil_properties.items():
            data.append({
                'Soil Type': soil_type,
                'Ic Range': f"{props['Ic_range'][0]:.2f} - {props['Ic_range'][1]:.2f}",
                'E (kPa)': f"{props['youngs_modulus_range'][0]:.0f} - {props['youngs_modulus_range'][1]:.0f}",
                'Cc': f"{props['compression_index_range'][0]:.3f} - {props['compression_index_range'][1]:.3f}",
                'φ (°)': f"{props['friction_angle_range'][0]:.0f} - {props['friction_angle_range'][1]:.0f}" if props['friction_angle_range'][0] > 0 else "N/A",
                'Description': props['description']
            })
        
        return pd.DataFrame(data)
    
    def compare_layer_properties(self, layer_params: pd.DataFrame) -> List[Dict]:
        """
        Compare calculated layer properties against typical database ranges.
        
        Returns list of warnings for parameters outside typical ranges.
        """
        warnings = []
        
        for idx, layer in layer_params.iterrows():
            soil_type = layer.get('soil_type', 'Unknown')
            layer_num = layer.get('layer_number', idx + 1)
            
            # Check each parameter
            parameters_to_check = [
                ('youngs_modulus', 'E'),
                ('compression_index', 'Cc'),
                ('recompression_index', 'Cr'),
                ('OCR', 'OCR'),
                ('permeability', 'k')
            ]
            
            if 'friction_angle' in layer and layer['friction_angle'] > 0:
                parameters_to_check.append(('friction_angle', 'φ'))
            if 'undrained_shear_strength' in layer and layer['undrained_shear_strength'] > 0:
                parameters_to_check.append(('undrained_shear_strength', 'cu'))
            
            for param_key, param_display in parameters_to_check:
                if param_key in layer:
                    value = layer[param_key]
                    is_valid, message = self.validate_parameter(soil_type, param_key, value)
                    
                    if not is_valid:
                        warnings.append({
                            'layer_number': layer_num,
                            'soil_type': soil_type,
                            'parameter': param_display,
                            'value': value,
                            'message': message
                        })
        
        return warnings
