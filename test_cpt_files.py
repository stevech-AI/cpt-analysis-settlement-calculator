"""
Test script to process user's CPT text files and verify the application works
"""
import pandas as pd
from io import StringIO
from cpt_processor import CPTProcessor
from soil_classification import SoilLayering
from correlations import CPTCorrelations
from settlement_calc import SettlementCalculator

# Sample data from user's file "21-544_Settle_3D_1761927830944.txt"
# Tab-delimited, no headers, 4 columns: depth, qc, fs, u2
sample_data = """0.082  0.01    0       0
0.164   0.01    0       0
0.246   0.01    0       0
0.328   0.01    0       0
0.41    0.01    0       0
0.492   0.01    0       0
0.574   0.01    0       0
0.656   0.01    0       0
0.738   0.01    0       0
0.82    127.73  0.498   6.461
0.902   168.15  0.568   7.543
0.984   159.32  0.626   2.514
1.066   140.16  0.728   0.658
1.148   125.04  0.703   0.138
1.23    115.38  0.654   0.788
1.312   106.28  0.661   -0.277
1.394   98.65   0.982   0.571
1.476   89.17   0.831   -0.32
1.558   85.22   0.869   0.229
1.64    83.34   0.808   -1.207
1.722   69.25   0.835   2.467
1.804   64.23   0.743   0.29
1.886   55.76   0.623   0.299
1.968   52.27   0.442   -0.004
2.051   42.02   0.411   -0.164
2.133   36.55   0.442   -0.087
2.215   33.71   0.737   -0.061
2.297   30.38   0.536   -0.091
2.379   30.97   0.504   0.108
2.461   30.89   0.511   0.515
2.543   27.5    0.536   2.778
2.625   32.07   0.625   3.272
2.707   35.76   0.539   1.216
2.789   38.2    0.617   -1.644
2.871   37.91   0.78    -3.735
2.953   36.25   0.86    -5.678
3.035   31.86   0.586   -6.284
3.117   28.09   0.534   -6.31
3.199   28.87   0.512   -5.535
3.281   32.53   0.503   -3.994"""

def test_file_processing():
    print("=" * 70)
    print("TESTING CPT FILE PROCESSING")
    print("=" * 70)
    
    # Create a mock file object
    class MockFile:
        def __init__(self, content):
            self.content = content
        
        def read(self):
            return self.content.encode('utf-8')
    
    mock_file = MockFile(sample_data)
    
    # Test 1: Parse the text file
    print("\n1. Testing Text File Parser (no headers, tab-delimited)...")
    processor = CPTProcessor()
    
    try:
        df = processor.parse_text(mock_file)
        print(f"   ✓ Successfully parsed {len(df)} rows")
        print(f"   ✓ Columns: {list(df.columns)}")
        print(f"   ✓ Depth range: {df['depth'].min():.2f}m to {df['depth'].max():.2f}m")
        print(f"   ✓ qc range: {df['qc'].min():.2f} to {df['qc'].max():.2f} kPa")
        print(f"\n   Sample data (first 5 rows):")
        print(df.head().to_string(index=False))
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 2: Calculate normalized parameters
    print("\n2. Testing CPT Data Normalization...")
    try:
        soil_unit_weight = 18.0
        water_table_depth = 2.0
        net_area_ratio = 0.8
        
        processed = processor.calculate_normalized_parameters(
            df, soil_unit_weight, water_table_depth, net_area_ratio
        )
        print(f"   ✓ Successfully calculated normalized parameters")
        print(f"   ✓ Added parameters: Qt, Fr, Bq, Ic")
        print(f"   ✓ Ic range: {processed['Ic'].min():.2f} to {processed['Ic'].max():.2f}")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Apply soil classification
    print("\n3. Applying Soil Classification...")
    try:
        # Add soil_type based on Ic (Robertson 2009 classification)
        processed['soil_type'] = processed['Ic'].apply(processor.identify_soil_type)
        
        soil_types = processed['soil_type'].value_counts()
        print(f"   ✓ Soil types identified in data:")
        for soil, count in soil_types.items():
            print(f"      - {soil}: {count} points")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Layer identification
    print("\n4. Testing Layer Identification...")
    try:
        layering = SoilLayering(min_layer_thickness=0.5)
        layers = layering.identify_layers(processed)
        print(f"   ✓ Successfully identified {len(layers)} layers")
        print(f"\n   Layer Summary:")
        for _, layer in layers.iterrows():
            print(f"      Layer {layer['layer_number']}: {layer['soil_type']}")
            print(f"         Depth: {layer['top_depth']:.2f}m to {layer['bottom_depth']:.2f}m ({layer['thickness']:.2f}m)")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Calculate parameters for all layers
    print("\n5. Testing Parameter Calculations...")
    try:
        correlator = CPTCorrelations()
        parameters = correlator.process_all_layers(layers)
        print(f"   ✓ Successfully calculated parameters for {len(parameters)} layers")
        print(f"\n   Parameter Summary (first 3 layers):")
        cols = ['layer_number', 'youngs_modulus', 'constrained_modulus', 'compression_index', 'OCR']
        if len(parameters) > 0:
            print(parameters[cols].head(3).to_string(index=False))
        else:
            print("      No parameters calculated (may need more layers)")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Settlement calculation
    print("\n6. Testing Settlement Calculation...")
    try:
        calc = SettlementCalculator()
        
        # Test footing parameters
        load_kN = 400.0
        footing_width = 2.0
        footing_length = 2.0
        footing_depth = 1.0
        
        settlement = calc.calculate_total_settlement(
            parameters, load_kN, footing_width, footing_length, 
            footing_depth, water_table_depth
        )
        
        print(f"   ✓ Successfully calculated settlement")
        print(f"   Settlement keys available: {list(settlement.keys())}")
        
        # Print available results
        for key, value in settlement.items():
            if isinstance(value, (int, float)):
                print(f"   - {key}: {value:.2f} mm")
        
        # Show layer breakdown if available
        for key in ['layer_details', 'layer_breakdown', 'layers']:
            if key in settlement and isinstance(settlement[key], (list, pd.DataFrame)):
                print(f"\n   ✓ Settlement details available in '{key}'")
                break
                
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_file_processing()
    if not success:
        print("\n⚠ Some tests failed. Please check the errors above.")
        exit(1)
