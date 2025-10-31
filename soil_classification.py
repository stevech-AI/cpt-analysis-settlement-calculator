import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

class SoilLayering:
    """
    Automated soil layering based on Ic transitions and soil behavior type changes.
    """
    
    def __init__(self, min_layer_thickness: float = 0.5):
        """
        Parameters:
        - min_layer_thickness: Minimum layer thickness in meters (default 0.5m)
        """
        self.min_layer_thickness = min_layer_thickness
    
    def identify_layers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify soil layers based on Ic value transitions.
        
        Uses a moving window approach to detect significant changes in soil behavior.
        """
        if len(df) == 0:
            return pd.DataFrame()
        
        layers = []
        current_layer_start = 0
        current_layer_Ic = df['Ic'].iloc[0]
        current_layer_soil_type = df['soil_type'].iloc[0]
        
        # Define Ic thresholds for layer boundaries
        Ic_threshold = 0.3  # Change of 0.3 in Ic suggests different material
        
        for i in range(1, len(df)):
            Ic_change = abs(df['Ic'].iloc[i] - current_layer_Ic)
            depth_diff = df['depth'].iloc[i] - df['depth'].iloc[current_layer_start]
            
            # Check if we should create a new layer
            if Ic_change > Ic_threshold and depth_diff >= self.min_layer_thickness:
                # Store current layer
                layer = self._create_layer(df, current_layer_start, i)
                layers.append(layer)
                
                # Start new layer
                current_layer_start = i
                current_layer_Ic = df['Ic'].iloc[i]
                current_layer_soil_type = df['soil_type'].iloc[i]
        
        # Add the last layer
        layer = self._create_layer(df, current_layer_start, len(df))
        layers.append(layer)
        
        return pd.DataFrame(layers)
    
    def _create_layer(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> Dict:
        """
        Create a layer dictionary from a DataFrame slice.
        """
        layer_data = df.iloc[start_idx:end_idx]
        
        return {
            'layer_number': None,  # Will be assigned later
            'top_depth': layer_data['depth'].iloc[0],
            'bottom_depth': layer_data['depth'].iloc[-1],
            'thickness': layer_data['depth'].iloc[-1] - layer_data['depth'].iloc[0],
            'avg_qc': layer_data['qc'].mean(),
            'avg_qt': layer_data['qt'].mean(),
            'avg_fs': layer_data['fs'].mean(),
            'avg_Ic': layer_data['Ic'].mean(),
            'avg_Qt': layer_data['Qt1'].mean(),
            'avg_Fr': layer_data['Fr'].mean(),
            'avg_Rf': layer_data['Rf'].mean(),
            'soil_type': layer_data['soil_type'].mode()[0] if len(layer_data) > 0 else "Unknown",
            'avg_sigma_vo_prime': layer_data['sigma_vo_prime'].mean()
        }
    
    def merge_thin_layers(self, layers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge layers thinner than minimum thickness with adjacent layers.
        """
        if len(layers_df) == 0:
            return layers_df
        
        merged = []
        i = 0
        
        while i < len(layers_df):
            current = layers_df.iloc[i].to_dict()
            
            # Check if layer is too thin
            if current['thickness'] < self.min_layer_thickness and i < len(layers_df) - 1:
                # Merge with next layer
                next_layer = layers_df.iloc[i + 1].to_dict()
                merged_layer = self._merge_two_layers(current, next_layer)
                merged.append(merged_layer)
                i += 2  # Skip the next layer as it's been merged
            else:
                merged.append(current)
                i += 1
        
        result = pd.DataFrame(merged)
        
        # Renumber layers
        if len(result) > 0:
            result['layer_number'] = range(1, len(result) + 1)
        
        return result
    
    def _merge_two_layers(self, layer1: Dict, layer2: Dict) -> Dict:
        """
        Merge two adjacent layers by weighted averaging.
        """
        total_thickness = layer1['thickness'] + layer2['thickness']
        w1 = layer1['thickness'] / total_thickness
        w2 = layer2['thickness'] / total_thickness
        
        return {
            'layer_number': layer1['layer_number'],
            'top_depth': layer1['top_depth'],
            'bottom_depth': layer2['bottom_depth'],
            'thickness': total_thickness,
            'avg_qc': w1 * layer1['avg_qc'] + w2 * layer2['avg_qc'],
            'avg_qt': w1 * layer1['avg_qt'] + w2 * layer2['avg_qt'],
            'avg_fs': w1 * layer1['avg_fs'] + w2 * layer2['avg_fs'],
            'avg_Ic': w1 * layer1['avg_Ic'] + w2 * layer2['avg_Ic'],
            'avg_Qt': w1 * layer1['avg_Qt'] + w2 * layer2['avg_Qt'],
            'avg_Fr': w1 * layer1['avg_Fr'] + w2 * layer2['avg_Fr'],
            'avg_Rf': w1 * layer1['avg_Rf'] + w2 * layer2['avg_Rf'],
            'soil_type': layer1['soil_type'],  # Use first layer's type
            'avg_sigma_vo_prime': w1 * layer1['avg_sigma_vo_prime'] + w2 * layer2['avg_sigma_vo_prime']
        }
    
    def process_layering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Complete layering process: identify, merge thin layers, and number.
        """
        layers = self.identify_layers(df)
        layers = self.merge_thin_layers(layers)
        
        if len(layers) > 0:
            layers['layer_number'] = range(1, len(layers) + 1)
        
        return layers


class RobertsonClassification:
    """
    Robertson (2009) soil classification chart implementation.
    """
    
    @staticmethod
    def get_classification_zones() -> Dict[int, Dict]:
        """
        Returns the Robertson (2009) soil behavior type zone definitions.
        """
        return {
            1: {
                'name': 'Sensitive, fine grained',
                'Ic_range': (3.60, 4.0),
                'color': '#8B4513'
            },
            2: {
                'name': 'Organic soils - clay',
                'Ic_range': (3.60, 4.0),
                'color': '#654321'
            },
            3: {
                'name': 'Clays: silty clay to clay',
                'Ic_range': (2.95, 3.60),
                'color': '#A0522D'
            },
            4: {
                'name': 'Silt mixtures: clayey silt to silty clay',
                'Ic_range': (2.60, 2.95),
                'color': '#CD853F'
            },
            5: {
                'name': 'Sand mixtures: silty sand to sandy silt',
                'Ic_range': (2.05, 2.60),
                'color': '#DEB887'
            },
            6: {
                'name': 'Sands: clean sand to silty sand',
                'Ic_range': (1.31, 2.05),
                'color': '#F4A460'
            },
            7: {
                'name': 'Gravelly sand to dense sand',
                'Ic_range': (0.0, 1.31),
                'color': '#FFD700'
            }
        }
    
    @staticmethod
    def get_zone_from_Ic(Ic: float) -> int:
        """
        Get Robertson zone number from Ic value.
        """
        if Ic >= 3.60:
            return 3 if Ic < 4.0 else 2
        elif Ic >= 2.95:
            return 3
        elif Ic >= 2.60:
            return 4
        elif Ic >= 2.05:
            return 5
        elif Ic >= 1.31:
            return 6
        else:
            return 7
    
    @staticmethod
    def calculate_Ic_contours(Qt_range: Tuple[float, float], 
                              num_points: int = 100) -> Dict[float, np.ndarray]:
        """
        Calculate Ic contour lines for plotting on Qt-Fr chart.
        
        Ic = sqrt((3.47 - log10(Qt))^2 + (log10(Fr) + 1.22)^2)
        """
        Ic_values = [1.31, 2.05, 2.60, 2.95, 3.60]
        contours = {}
        
        Qt_array = np.logspace(np.log10(Qt_range[0]), np.log10(Qt_range[1]), num_points)
        
        for Ic in Ic_values:
            # Solve for Fr from Ic equation
            # Fr = 10^(sqrt(Ic^2 - (3.47 - log10(Qt))^2) - 1.22)
            log_Qt = np.log10(Qt_array)
            discriminant = Ic**2 - (3.47 - log_Qt)**2
            
            # Only calculate where discriminant is positive
            valid_idx = discriminant >= 0
            Fr_array = np.full_like(Qt_array, np.nan)
            Fr_array[valid_idx] = 10**(np.sqrt(discriminant[valid_idx]) - 1.22)
            
            contours[Ic] = np.column_stack([Qt_array, Fr_array])
        
        return contours


class Robertson1990Classification:
    """
    Robertson (1990) normalized CPT soil classification chart implementation.
    Uses stress-normalized parameters and 9 soil behavior type zones.
    """
    
    @staticmethod
    def get_classification_zones() -> Dict[int, Dict]:
        """
        Returns the Robertson (1990) soil behavior type zone definitions.
        """
        return {
            1: {
                'name': 'Sensitive fine-grained',
                'Ic_range': (3.60, 5.0),
                'color': '#8B4513'
            },
            2: {
                'name': 'Clay - organic soil',
                'Ic_range': (2.95, 3.60),
                'color': '#654321'
            },
            3: {
                'name': 'Clay to silty clay',
                'Ic_range': (2.60, 2.95),
                'color': '#A0522D'
            },
            4: {
                'name': 'Silt mixtures - clayey silt to silty clay',
                'Ic_range': (2.05, 2.60),
                'color': '#CD853F'
            },
            5: {
                'name': 'Sand mixtures - silty sand to sandy silt',
                'Ic_range': (1.31, 2.05),
                'color': '#DEB887'
            },
            6: {
                'name': 'Sands - clean sand to silty sand',
                'Ic_range': (0.0, 1.31),
                'color': '#F4A460'
            },
            7: {
                'name': 'Dense sand to gravelly sand',
                'Ic_range': (0.0, 1.31),
                'color': '#FFD700',
                'Qt_threshold': 100
            },
            8: {
                'name': 'Stiff sand to clayey sand',
                'Ic_range': (1.31, 2.05),
                'color': '#FFA500',
                'overconsolidated': True
            },
            9: {
                'name': 'Stiff fine-grained',
                'Ic_range': (2.05, 5.0),
                'color': '#FF8C00',
                'overconsolidated': True
            }
        }
    
    @staticmethod
    def classify_soil_type(Qt: float, Fr: float, Ic: float) -> str:
        """
        Classify soil type based on Robertson 1990 normalized parameters.
        """
        if Ic >= 3.60:
            return 'Sensitive fine-grained'
        elif Ic >= 2.95:
            return 'Clay - organic soil'
        elif Ic >= 2.60:
            return 'Clay to silty clay'
        elif Ic >= 2.05:
            if Qt > 50:  # Overconsolidated
                return 'Stiff fine-grained'
            else:
                return 'Silt mixtures - clayey silt to silty clay'
        elif Ic >= 1.31:
            if Qt > 50:  # Dense or overconsolidated
                return 'Stiff sand to clayey sand'
            else:
                return 'Sand mixtures - silty sand to sandy silt'
        else:
            if Qt > 100:
                return 'Dense sand to gravelly sand'
            else:
                return 'Sands - clean sand to silty sand'
    
    @staticmethod
    def calculate_Ic_contours(Qt_range: Tuple[float, float], 
                              num_points: int = 100) -> Dict[float, np.ndarray]:
        """
        Calculate Ic contour lines for Robertson 1990 classification.
        Same formula as Robertson 2009.
        """
        Ic_values = [1.31, 2.05, 2.60, 2.95, 3.60]
        contours = {}
        
        Qt_array = np.logspace(np.log10(Qt_range[0]), np.log10(Qt_range[1]), num_points)
        
        for Ic in Ic_values:
            log_Qt = np.log10(Qt_array)
            discriminant = Ic**2 - (3.47 - log_Qt)**2
            
            valid_idx = discriminant >= 0
            Fr_array = np.full_like(Qt_array, np.nan)
            Fr_array[valid_idx] = 10**(np.sqrt(discriminant[valid_idx]) - 1.22)
            
            contours[Ic] = np.column_stack([Qt_array, Fr_array])
        
        return contours


class Schneider2008Classification:
    """
    Schneider et al. (2008) CPTu soil classification chart implementation.
    Focuses on drainage conditions and uses Q-F and Q-Bq charts.
    """
    
    @staticmethod
    def get_classification_zones() -> Dict[str, Dict]:
        """
        Returns the Schneider (2008) soil behavior type zone definitions.
        """
        return {
            '1a': {
                'name': 'Clays - high friction',
                'description': 'Claylike soils with higher friction ratios',
                'color': '#8B4513',
                'F_min': 2.0
            },
            '1b': {
                'name': 'Clays - standard',
                'description': 'Standard claylike soils',
                'color': '#A0522D',
                'F_range': (1.0, 2.0)
            },
            '1c': {
                'name': 'Sensitive and cemented clays',
                'description': 'Sensitive, structured or cemented clays',
                'color': '#654321',
                'F_max': 1.0
            },
            '2': {
                'name': 'Drained sands',
                'description': 'Essentially drained sands and gravels',
                'color': '#FFD700',
                'Q_min': 20,
                'drainage': 'drained'
            },
            '3': {
                'name': 'Transitional soils',
                'description': 'Partially drained transitional soils (silts)',
                'color': '#DEB887',
                'drainage': 'partial'
            }
        }
    
    @staticmethod
    def classify_soil_type(Q: float, F: float, Bq: Optional[float] = None) -> str:
        """
        Classify soil type based on Schneider 2008 parameters.
        
        Parameters:
        -----------
        Q : float
            Normalized cone resistance Q = (qt - σvo) / σ'vo
        F : float
            Friction ratio F = fs / (qt - σvo) × 100
        Bq : float, optional
            Pore pressure ratio (for refined classification)
        """
        # Zone 2: Drained sands
        if Q > 20 and F < 2.0:
            return 'Drained sands'
        
        # Zone 3: Transitional soils
        elif Q > 10 and F < 4.0:
            return 'Transitional soils'
        
        # Zone 1: Claylike soils
        elif Q < 20:
            if F >= 2.0:
                return 'Clays - high friction'
            elif F >= 1.0:
                return 'Clays - standard'
            else:
                return 'Sensitive and cemented clays'
        
        # Default to transitional
        else:
            return 'Transitional soils'
    
    @staticmethod
    def calculate_zone_boundaries() -> Dict[str, np.ndarray]:
        """
        Calculate zone boundary lines for Schneider 2008 Q-F chart.
        """
        boundaries = {}
        
        # Q range for plotting
        Q_array = np.logspace(0, 3, 100)  # 1 to 1000
        
        # Boundary between zones 1 and 2/3 (Q = 20)
        boundaries['sand_boundary'] = np.array([[20, 0.1], [20, 10]])
        
        # Boundary between zones 2 and 3 (Q = 10, F = 2)
        boundaries['transitional_boundary'] = np.array([[10, 0.1], [10, 4]])
        
        # Zone 1 subdivisions based on F values
        boundaries['zone_1a_1b'] = np.array([[0.1, 2.0], [20, 2.0]])
        boundaries['zone_1b_1c'] = np.array([[0.1, 1.0], [20, 1.0]])
        
        return boundaries


class ClassificationComparator:
    """
    Compare results from different CPT classification methods.
    """
    
    @staticmethod
    def compare_classifications(data: pd.DataFrame, method1: str = 'Robertson2009', 
                               method2: str = 'Robertson1990') -> pd.DataFrame:
        """
        Compare soil classifications from two different methods.
        
        Returns a DataFrame with both classifications and agreement statistics.
        """
        comparison = data.copy()
        
        if method1 == 'Robertson2009':
            comparison['method1_soil_type'] = data['soil_type']
        elif method1 == 'Robertson1990':
            comparison['method1_soil_type'] = data.apply(
                lambda row: Robertson1990Classification.classify_soil_type(
                    row['Qt1'], row['Fr'], row['Ic']
                ), axis=1
            )
        elif method1 == 'Schneider2008':
            comparison['method1_soil_type'] = data.apply(
                lambda row: Schneider2008Classification.classify_soil_type(
                    row['Qt1'], row['Fr']
                ), axis=1
            )
        
        if method2 == 'Robertson2009':
            comparison['method2_soil_type'] = data['soil_type']
        elif method2 == 'Robertson1990':
            comparison['method2_soil_type'] = data.apply(
                lambda row: Robertson1990Classification.classify_soil_type(
                    row['Qt1'], row['Fr'], row['Ic']
                ), axis=1
            )
        elif method2 == 'Schneider2008':
            comparison['method2_soil_type'] = data.apply(
                lambda row: Schneider2008Classification.classify_soil_type(
                    row['Qt1'], row['Fr']
                ), axis=1
            )
        
        # Calculate agreement
        comparison['agreement'] = comparison['method1_soil_type'] == comparison['method2_soil_type']
        
        return comparison
    
    @staticmethod
    def get_agreement_statistics(comparison: pd.DataFrame) -> Dict:
        """
        Calculate statistics on classification agreement.
        """
        total = len(comparison)
        agreed = comparison['agreement'].sum()
        
        return {
            'total_points': total,
            'agreed_points': agreed,
            'disagreed_points': total - agreed,
            'agreement_percentage': (agreed / total * 100) if total > 0 else 0
        }
