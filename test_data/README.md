# Test Data - Sample CPT Files

This folder contains real CPT (Cone Penetration Test) data files for testing the application.

## Files

### `sample_cpt1.txt`
- **Data Points**: 1,096 readings
- **Depth Range**: 0 to 10.95 meters
- **Soil Profile**: 1 layer - Organic clay
- **Settlement**: ~0mm (extremely soft uniform soil)
- **Use Case**: Testing with uniform soft soil conditions

### `sample_cpt2.txt` ⭐ **Recommended for Demo**
- **Data Points**: 1,096 readings
- **Depth Range**: 0 to 10.95 meters
- **Soil Profile**: 5 distinct layers - All organic clay at different depths
- **Settlement**: ~1,930mm total (1,609mm immediate + 321mm consolidation)
- **Use Case**: Best example showing multi-layer analysis and significant settlement

### `sample_cpt3.txt`
- **Data Points**: 555 readings
- **Depth Range**: 0 to 5.54 meters
- **Soil Profile**: 1 layer - Organic clay
- **Settlement**: ~0mm (uniform soft soil)
- **Use Case**: Testing with shorter depth profile

## File Format

All files are tab-delimited text files without headers, following this column order:
```
Column 1: Depth (m)
Column 2: Cone Resistance - qc (kPa)
Column 3: Sleeve Friction - fs (kPa)
Column 4: Pore Pressure - u2 (kPa)
```

## How to Use

1. Run the application: `streamlit run app.py`
2. Navigate to the "📤 Upload CPT Data" tab
3. Upload one or more of these sample files
4. Explore the various analysis tabs

**Tip**: Start with `sample_cpt2.txt` for the most comprehensive demonstration of the app's capabilities!

## Expected Results (using default settings)

For a 1000kN load on a 2m × 2m footing at 1m depth:

| File | Layers | Immediate Settlement | Consolidation | Total Settlement |
|------|--------|---------------------|---------------|------------------|
| sample_cpt1.txt | 1 | 0 mm | 0 mm | **0 mm** |
| sample_cpt2.txt | 5 | 1,609 mm | 321 mm | **1,930 mm** |
| sample_cpt3.txt | 1 | 0 mm | 0 mm | **0 mm** |

## Notes

- These are real field data from ground floor slab and plant room CPT investigations
- The organic clay in sample_cpt2.txt exhibits very high compressibility, leading to significant settlement
- Results demonstrate the importance of proper soil investigation for foundation design
