import numpy as np
import pandas as pd
from typing import Dict

class CPTCorrelations:
    """
    CPT correlations for settlement parameters based on Settle3 methodology.
    Includes correlations for E, Cc, Cr, M, OCR and other parameters.
    """
    
    def __init__(self):
        self.Pa = 100.0  # Atmospheric pressure in kPa
    
    def calculate_youngs_modulus(self, qt: float, sigma_vo: float, Ic: float) -> float:
        """
        Calculate Young's Modulus (E) from CPT data.
        
        Based on Robertson (2009):
        E = alpha_E * (qt - sigma_vo)
        where alpha_E = 0.015 * 10^(0.55*Ic + 1.68)
        
        The modulus is mobilized at about 0.1% strain.
        """
        alpha_E = 0.015 * (10 ** (0.55 * Ic + 1.68))
        E = alpha_E * (qt - sigma_vo)
        return max(E, 100)  # Minimum 100 kPa
    
    def calculate_constrained_modulus(self, qt: float, Qtn: float) -> float:
        """
        Calculate Constrained Modulus (M) from CPT data.
        
        Based on Robertson (2009):
        M = alpha_M * qt
        where alpha_M varies with Qtn, limited to 8
        """
        # Calculate alpha_M based on Qtn
        if Qtn < 14:
            alpha_M = Qtn * 0.5
        else:
            alpha_M = 8.0  # Maximum value limited to 8
        
        alpha_M = min(alpha_M, 8.0)
        alpha_M = max(alpha_M, 2.0)  # Minimum value of 2
        
        M = alpha_M * qt
        return max(M, 100)
    
    def calculate_compression_index(self, Ic: float, sigma_vo_prime: float, 
                                   qt: float, PI: float = None) -> float:
        """
        Calculate Compression Index (Cc) from CPT data.
        
        Based on correlations from plasticity index (Jain et al. 2015)
        For clay-like soils (Ic > 2.6)
        
        If PI not available, estimate from Ic
        """
        if Ic < 2.6:
            # Sandy soils - low compressibility
            Cc = 0.01 + 0.05 * (Ic - 1.5)
            Cc = max(0.01, min(Cc, 0.1))
        else:
            # Clay-like soils
            if PI is None:
                # Estimate PI from Ic
                # Higher Ic suggests higher plasticity
                PI_estimated = (Ic - 2.6) * 15
                PI = min(PI_estimated, 60)
            
            # Correlation: Cc = 0.009 * (LL - 10) or Cc = 0.007 * (PI + 5)
            # Using PI correlation
            Cc = 0.007 * (PI + 5)
            
            # Alternative based on qt for fine-grained soils
            if qt < 1000:  # Soft clay
                Cc_alt = 0.5 - 0.0003 * qt
                Cc = max(Cc, Cc_alt)
        
        return max(Cc, 0.01)
    
    def calculate_recompression_index(self, Cc: float, LL: float = None, 
                                     Ic: float = None) -> float:
        """
        Calculate Recompression Index (Cr) from CPT data.
        
        Based on GMDH-type neural network (Kordnaeij et al. 2015)
        Typical relationship: Cr = Cc / 5 to Cc / 10
        
        For more accurate results, uses LL (liquid limit) if available
        """
        if LL is not None:
            # Correlation with liquid limit
            Cr = 0.002 * (LL + 10)
        elif Ic is not None:
            # Estimate from Ic
            if Ic > 2.95:  # Clay
                Cr = Cc / 6.0
            elif Ic > 2.60:  # Silt
                Cr = Cc / 8.0
            else:  # Sand
                Cr = Cc / 10.0
        else:
            # Default relationship
            Cr = Cc / 7.0
        
        return max(Cr, 0.001)
    
    def calculate_OCR(self, qt: float, sigma_vo: float, sigma_vo_prime: float, Ic: float) -> float:
        """
        Calculate Over-Consolidation Ratio (OCR) from CPT data.
        
        Based on Chen & Mayne (1996) and Mayne (2005):
        OCR = k * (qt - sigma_vo) / sigma_vo_prime
        where k varies with soil type
        """
        if Ic < 2.2:  # Sand
            k = 0.33
        elif Ic < 2.6:  # Silty sand
            k = 0.30
        elif Ic < 3.0:  # Silt
            k = 0.25
        else:  # Clay
            k = 0.20
        
        # Use net cone resistance (qt - sigma_vo)
        qnet = qt - sigma_vo
        OCR = k * (qnet / sigma_vo_prime)
        
        # Reasonable bounds
        OCR = max(1.0, min(OCR, 20.0))
        
        return OCR
    
    def calculate_friction_angle(self, Qtn: float, Ic: float) -> float:
        """
        Calculate friction angle (phi) for sandy soils.
        
        Based on Robertson & Campanella (1983) and Kulhawy & Mayne (1990)
        """
        if Ic > 2.6:
            # Not applicable for clay-like soils
            return 0.0
        
        # Robertson & Campanella correlation
        if Qtn < 300:
            phi = 17.6 + 11.0 * np.log10(Qtn)
        else:
            phi = 17.6 + 11.0 * np.log10(300)  # Cap at Qtn = 300
        
        phi = max(25, min(phi, 45))  # Reasonable bounds
        
        return phi
    
    def calculate_undrained_shear_strength(self, qt: float, sigma_vo: float, 
                                          Ic: float) -> float:
        """
        Calculate undrained shear strength (Su) for clay-like soils.
        
        Based on Robertson (2009):
        Su = (qt - sigma_vo) / Nkt
        where Nkt varies with soil plasticity
        """
        if Ic < 2.6:
            # Not applicable for sandy soils
            return 0.0
        
        # Cone factor Nkt varies typically between 10-20
        # Higher Ic suggests higher plasticity and higher Nkt
        Nkt = 10 + (Ic - 2.6) * 5
        Nkt = min(Nkt, 20)
        
        Su = (qt - sigma_vo) / Nkt
        
        return max(Su, 0)
    
    def calculate_permeability(self, Ic: float, qt: float) -> float:
        """
        Calculate permeability (k) from CPT data.
        
        Based on Robertson (2010):
        log k (m/s) = 0.952 - 3.04 * Ic
        """
        log_k = 0.952 - 3.04 * Ic
        k = 10 ** log_k
        
        # Reasonable bounds
        k = max(1e-10, min(k, 1e-3))
        
        return k
    
    def calculate_unit_weight(self, qt: float, Ic: float) -> float:
        """
        Calculate bulk unit weight (gamma) from CPT data.
        
        Based on Robertson & Cabal (2010)
        """
        if Ic < 2.05:  # Sand
            gamma = 17.0 + 3.0 * np.log10(qt / 100)
        elif Ic < 2.6:  # Silty sand
            gamma = 16.5 + 2.0 * np.log10(qt / 100)
        else:  # Clay
            gamma = 15.0 + 2.5 * np.log10(qt / 100)
        
        gamma = max(14.0, min(gamma, 22.0))  # Reasonable bounds
        
        return gamma
    
    def calculate_all_parameters(self, layer: Dict) -> Dict:
        """
        Calculate all settlement parameters for a soil layer.
        
        Input: layer dictionary from soil layering
        Output: dictionary with all calculated parameters
        """
        qt = layer['avg_qt']
        sigma_vo_prime = layer['avg_sigma_vo_prime']
        Ic = layer['avg_Ic']
        Qtn = layer['avg_Qt']
        
        # Calculate stress at mid-depth of layer
        sigma_vo = sigma_vo_prime * 1.2  # Approximate (assumes some pore pressure)
        
        parameters = {
            'layer_number': layer['layer_number'],
            'soil_type': layer['soil_type'],
            'thickness': layer['thickness'],
            'Ic': Ic,
            
            # Strength parameters
            'friction_angle': self.calculate_friction_angle(Qtn, Ic),
            'undrained_shear_strength': self.calculate_undrained_shear_strength(qt, sigma_vo, Ic),
            
            # Stiffness parameters
            'youngs_modulus': self.calculate_youngs_modulus(qt, sigma_vo, Ic),
            'constrained_modulus': self.calculate_constrained_modulus(qt, Qtn),
            
            # Compressibility parameters
            'compression_index': self.calculate_compression_index(Ic, sigma_vo_prime, qt),
            'recompression_index': None,  # Will be calculated after Cc
            
            # Stress history
            'OCR': self.calculate_OCR(qt, sigma_vo, sigma_vo_prime, Ic),
            
            # Other properties
            'permeability': self.calculate_permeability(Ic, qt),
            'unit_weight': self.calculate_unit_weight(qt, Ic)
        }
        
        # Calculate Cr after Cc is known
        parameters['recompression_index'] = self.calculate_recompression_index(
            parameters['compression_index'], Ic=Ic
        )
        
        return parameters
    
    def process_all_layers(self, layers_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate parameters for all layers in a DataFrame.
        """
        if len(layers_df) == 0:
            return pd.DataFrame()
        
        results = []
        for _, layer in layers_df.iterrows():
            params = self.calculate_all_parameters(layer.to_dict())
            results.append(params)
        
        return pd.DataFrame(results)
