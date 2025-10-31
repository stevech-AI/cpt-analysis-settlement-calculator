import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class CPTProcessor:
    """
    Process CPT (Cone Penetration Test) data including normalization and calculations.
    Based on Robertson (2009) methodology.
    """
    
    def __init__(self):
        self.Pa = 100.0  # Atmospheric pressure in kPa
        self.gamma_water = 9.81  # Unit weight of water in kN/m³
    
    def parse_text(self, file) -> pd.DataFrame:
        """
        Parse text file (CSV, tab-delimited, or space-delimited) with flexible column detection.
        Expected columns: Depth, qc (cone resistance), fs (sleeve friction), u2 (pore pressure)
        Handles both files with headers and files without headers (assumes 4 columns: depth, qc, fs, u2)
        """
        # Read the file content
        content = file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # Try different delimiters
        lines = content.strip().split('\n')
        if not lines:
            raise ValueError("Empty text file")
        
        # Detect delimiter by checking the first line
        first_line = lines[0]
        if '\t' in first_line:
            delimiter = '\t'
        elif ',' in first_line:
            delimiter = ','
        elif ';' in first_line:
            delimiter = ';'
        else:
            delimiter = r'\s+'  # Multiple spaces/whitespace
        
        # Check if first line contains text (header) or only numbers (no header)
        from io import StringIO
        first_values = first_line.split('\t' if delimiter == '\t' else ',' if delimiter == ',' else ';' if delimiter == ';' else None)
        
        # Try to determine if file has headers
        has_header = False
        try:
            # If first value can't be converted to float, it's likely a header
            float(first_values[0].strip())
        except (ValueError, AttributeError):
            has_header = True
        
        # Read with or without header
        if has_header:
            df = pd.read_csv(StringIO(content), sep=delimiter, engine='python')
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Define possible column name variations
            depth_keywords = ['depth', 'z', 'elevation', 'elev']
            qc_keywords = ['qc', 'cone', 'resistance', 'tip resistance', 'qt']
            fs_keywords = ['fs', 'sleeve', 'friction', 'sleeve friction']
            u2_keywords = ['u2', 'u', 'pore', 'pore pressure', 'pwp']
            
            # Find matching columns
            column_map = {}
            for col in df.columns:
                col_lower = str(col).lower()
                if any(kw in col_lower for kw in depth_keywords) and 'depth' not in column_map:
                    column_map['depth'] = col
                elif any(kw in col_lower for kw in qc_keywords) and 'qc' not in column_map:
                    column_map['qc'] = col
                elif any(kw in col_lower for kw in fs_keywords) and 'fs' not in column_map:
                    column_map['fs'] = col
                elif any(kw in col_lower for kw in u2_keywords) and 'u2' not in column_map:
                    column_map['u2'] = col
            
            # Check if essential columns are found
            if 'depth' not in column_map or 'qc' not in column_map:
                raise ValueError("Could not find 'depth' and 'qc' columns in the text file")
            
            # Create standardized dataframe
            result = pd.DataFrame()
            result['depth'] = df[column_map['depth']].astype(float)
            result['qc'] = df[column_map['qc']].astype(float)
            
            # Optional columns
            if 'fs' in column_map:
                result['fs'] = df[column_map['fs']].astype(float)
            else:
                result['fs'] = 0.0
            
            if 'u2' in column_map:
                result['u2'] = df[column_map['u2']].astype(float)
            else:
                result['u2'] = 0.0
        else:
            # No header - assume columns are: depth, qc, fs, u2
            df = pd.read_csv(StringIO(content), sep=delimiter, engine='python', header=None)
            
            # Assign default column names based on number of columns
            result = pd.DataFrame()
            if len(df.columns) >= 2:
                result['depth'] = df[0].astype(float)
                result['qc'] = df[1].astype(float)
                result['fs'] = df[2].astype(float) if len(df.columns) > 2 else 0.0
                result['u2'] = df[3].astype(float) if len(df.columns) > 3 else 0.0
            else:
                raise ValueError("Text file must have at least 2 columns (depth and qc)")
        
        # Remove any rows with NaN values
        result = result.dropna()
        
        return result
    
    def parse_excel(self, file, sheet_name: int = 0) -> pd.DataFrame:
        """
        Parse Excel file with flexible column detection for CPT data.
        Expected columns: Depth, qc (cone resistance), fs (sleeve friction), u2 (pore pressure)
        """
        df = pd.read_excel(file, sheet_name=sheet_name)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Define possible column name variations
        depth_keywords = ['depth', 'z', 'elevation', 'elev']
        qc_keywords = ['qc', 'cone', 'resistance', 'tip resistance', 'qt']
        fs_keywords = ['fs', 'sleeve', 'friction', 'sleeve friction']
        u2_keywords = ['u2', 'u', 'pore', 'pore pressure', 'pwp']
        
        # Find matching columns
        column_map = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if any(kw in col_lower for kw in depth_keywords) and 'depth' not in column_map:
                column_map['depth'] = col
            elif any(kw in col_lower for kw in qc_keywords) and 'qc' not in column_map:
                column_map['qc'] = col
            elif any(kw in col_lower for kw in fs_keywords) and 'fs' not in column_map:
                column_map['fs'] = col
            elif any(kw in col_lower for kw in u2_keywords) and 'u2' not in column_map:
                column_map['u2'] = col
        
        # Check if essential columns are found
        if 'depth' not in column_map or 'qc' not in column_map:
            raise ValueError("Could not find 'depth' and 'qc' columns in the Excel file")
        
        # Create standardized dataframe
        result = pd.DataFrame()
        result['depth'] = df[column_map['depth']].astype(float)
        result['qc'] = df[column_map['qc']].astype(float)
        
        # Optional columns
        if 'fs' in column_map:
            result['fs'] = df[column_map['fs']].astype(float)
        else:
            result['fs'] = 0.0  # Default if not provided
        
        if 'u2' in column_map:
            result['u2'] = df[column_map['u2']].astype(float)
        else:
            result['u2'] = 0.0  # Default if not provided
        
        # Remove any rows with NaN values
        result = result.dropna()
        
        return result
    
    def calculate_stresses(self, depth: np.ndarray, gamma_soil: float = 18.0, 
                          water_table_depth: float = 2.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate total and effective overburden stresses.
        
        Parameters:
        - depth: Array of depths in meters
        - gamma_soil: Unit weight of soil in kN/m³ (default 18)
        - water_table_depth: Depth to water table in meters (default 2m)
        
        Returns:
        - sigma_vo: Total overburden stress (kPa)
        - sigma_vo_prime: Effective overburden stress (kPa)
        """
        sigma_vo = gamma_soil * depth
        
        # Calculate pore pressure
        u0 = np.where(depth > water_table_depth, 
                     self.gamma_water * (depth - water_table_depth), 
                     0)
        
        sigma_vo_prime = sigma_vo - u0
        sigma_vo_prime = np.maximum(sigma_vo_prime, 1.0)  # Avoid division by zero
        
        return sigma_vo, sigma_vo_prime
    
    def calculate_normalized_parameters(self, df: pd.DataFrame, 
                                       gamma_soil: float = 18.0,
                                       water_table_depth: float = 2.0,
                                       area_ratio: float = 0.8) -> pd.DataFrame:
        """
        Calculate normalized CPT parameters following Robertson (2009).
        
        Parameters:
        - df: DataFrame with depth, qc, fs, u2
        - gamma_soil: Unit weight of soil (kN/m³)
        - water_table_depth: Depth to water table (m)
        - area_ratio: Net area ratio for cone (typically 0.7-0.9)
        """
        result = df.copy()
        
        # Calculate stresses
        sigma_vo, sigma_vo_prime = self.calculate_stresses(
            result['depth'].values, gamma_soil, water_table_depth
        )
        
        result['sigma_vo'] = sigma_vo
        result['sigma_vo_prime'] = sigma_vo_prime
        
        # Calculate u0 (equilibrium pore pressure)
        result['u0'] = np.where(result['depth'] > water_table_depth,
                               self.gamma_water * (result['depth'] - water_table_depth),
                               0)
        
        # Corrected cone resistance qt
        result['qt'] = result['qc'] + result['u2'] * (1 - area_ratio)
        
        # Net cone resistance
        result['qn'] = result['qt'] - sigma_vo
        
        # Normalized cone resistance (Qt1)
        result['Qt1'] = (result['qt'] - sigma_vo) / sigma_vo_prime
        
        # Friction ratio (Rf in %)
        result['Rf'] = (result['fs'] / result['qn']) * 100
        result['Rf'] = result['Rf'].replace([np.inf, -np.inf], 0)
        
        # Normalized friction ratio (Fr in %)
        result['Fr'] = (result['fs'] / (result['qt'] - sigma_vo)) * 100
        result['Fr'] = result['Fr'].replace([np.inf, -np.inf], 0)
        
        # Pore pressure ratio (Bq)
        result['Bq'] = (result['u2'] - result['u0']) / (result['qt'] - sigma_vo)
        result['Bq'] = result['Bq'].replace([np.inf, -np.inf], 0)
        
        # Iterative calculation of Ic (Soil Behavior Type Index)
        # Initial estimate with n = 1
        n = 1.0
        Qtn = ((result['qt'] - sigma_vo) / self.Pa) * (self.Pa / sigma_vo_prime)**n
        
        # Iterative refinement
        for _ in range(5):  # Usually converges in 3-4 iterations
            Qtn_log = np.log10(Qtn)
            Fr_log = np.log10(result['Fr'] + 0.01)  # Avoid log(0)
            
            result['Ic'] = np.sqrt((3.47 - Qtn_log)**2 + (Fr_log + 1.22)**2)
            
            # Update n based on Ic
            n = np.where(result['Ic'] > 2.6, 1.0, 0.5)
            Qtn = ((result['qt'] - sigma_vo) / self.Pa) * (self.Pa / sigma_vo_prime)**n
        
        result['Qtn'] = Qtn
        result['n_exponent'] = n
        
        return result
    
    def identify_soil_type(self, Ic: float) -> str:
        """
        Identify soil behavior type based on Ic value (Robertson 2009).
        """
        if Ic < 1.31:
            return "Gravelly sand to dense sand"
        elif Ic < 2.05:
            return "Sands: clean sand to silty sand"
        elif Ic < 2.60:
            return "Sand mixtures: silty sand to sandy silt"
        elif Ic < 2.95:
            return "Silt mixtures: clayey silt to silty clay"
        elif Ic < 3.60:
            return "Clays: silty clay to clay"
        else:
            return "Organic soils - clay"
    
    def process_cpt_file(self, file, name: str, 
                        gamma_soil: float = 18.0,
                        water_table_depth: float = 2.0) -> Dict:
        """
        Complete processing of a CPT file.
        
        Returns a dictionary with:
        - name: CPT name
        - data: Processed DataFrame
        - summary: Summary statistics
        """
        # Parse the file based on file extension
        file_name = file.name if hasattr(file, 'name') else name
        if file_name.endswith('.txt') or file_name.endswith('.csv'):
            df = self.parse_text(file)
        else:
            df = self.parse_excel(file)
        
        # Calculate normalized parameters
        df = self.calculate_normalized_parameters(df, gamma_soil, water_table_depth)
        
        # Identify soil types
        df['soil_type'] = df['Ic'].apply(self.identify_soil_type)
        
        # Generate summary
        summary = {
            'depth_range': (df['depth'].min(), df['depth'].max()),
            'qc_range': (df['qc'].min(), df['qc'].max()),
            'avg_qc': df['qc'].mean(),
            'avg_Ic': df['Ic'].mean(),
            'predominant_soil': df['soil_type'].mode()[0] if len(df) > 0 else "Unknown"
        }
        
        return {
            'name': name,
            'data': df,
            'summary': summary
        }
