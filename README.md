# CPT Analysis & Settlement Calculator

A comprehensive geotechnical engineering web application for analyzing Cone Penetration Test (CPT) data and calculating settlement using Settle3 correlations and methodologies.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/stevech-AI/cpt-analysis-settlement-calculator.git
cd cpt-analysis-settlement-calculator

# Install dependencies
pip install .

# Run the application
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

📖 **For detailed installation instructions, see [INSTALL.md](INSTALL.md)**

## Features

### 1. CPT Data Processing
- **Excel file upload** supporting multiple CPT datasets
- Automatic column detection for depth, qc, fs, and u2
- Normalization calculations (Qt, Fr, Bq, Ic) using Robertson methodology
- Support for various data formats and headers

### 2. Soil Classification
- **Robertson (2009)** soil classification charts
- Automated soil behavior type identification
- Interactive Qt-Fr classification plots with Ic contours
- Soil type distribution analysis

### 3. Automated Soil Layering
- Layer identification based on Ic transitions
- User-adjustable minimum layer thickness
- Automatic merging of thin layers
- Visual layer profiles with depth and thickness

### 4. CPT Correlations
Calculate key settlement parameters from CPT data:
- **Young's Modulus (E)** - for immediate settlement
- **Constrained Modulus (M)**
- **Compression Index (Cc)** - for consolidation settlement
- **Recompression Index (Cr)**
- **Over-Consolidation Ratio (OCR)**
- **Friction Angle (φ)** - for sandy soils
- **Undrained Shear Strength (Su)** - for clayey soils
- **Permeability (k)**

### 5. Settlement Analysis
- **Immediate (Elastic) Settlement** calculations
- **Consolidation Settlement** for clay layers
- Total settlement estimation
- Layer-by-layer settlement breakdown
- Support for various loading configurations

### 6. Interactive Visualizations
- CPT profile plots (qc, fs, u2, Qt, Ic)
- Robertson classification charts with data points
- Parameter correlation graphs
- Settlement distribution by layer
- Multi-CPT comparison views

### 7. Export Functionality
- **Excel** exports with complete analysis data
- **PDF** comprehensive reports
- **CSV** layer summaries
- Settlement calculation results

## How to Use

### 1. Upload CPT Data
- Navigate to the "📤 Upload CPT Data" tab
- Upload one or more Excel files containing CPT data
- Files should have columns for: Depth, qc (cone resistance), fs (sleeve friction), and optionally u2 (pore pressure)
- The app will automatically detect column names

### 2. Configure Parameters
Use the sidebar to set:
- **Unit Weight of Soil** (kN/m³)
- **Water Table Depth** (m)
- **Minimum Layer Thickness** (m)
- **Net Area Ratio** for cone

### 3. View CPT Profiles
- Select CPTs to display
- Choose profile type (qc, Rf, u2, Qt, Ic)
- Compare multiple CPTs side-by-side

### 4. Explore Soil Classification
- View Robertson (2009) classification charts
- See soil type distribution
- Analyze Ic contours

### 5. Review Soil Layers
- View automated layer identification
- Export layer data
- Adjust layer thickness parameters if needed

### 6. Analyze Correlations
- Review calculated parameters for each layer
- Compare E, Cc, Cr, OCR across layers
- Export complete analysis to Excel

### 7. Calculate Settlement
- Input loading configuration:
  - Applied load (kN)
  - Footing dimensions (m)
  - Footing depth (m)
- View immediate and consolidation settlement
- Export settlement results and PDF reports

## Sample Data

Sample CPT data files are included:
- `Sample_CPT_01.xlsx` - Typical multi-layer soil profile
- `Sample_CPT_02.xlsx` - Alternative soil profile

## Methodology

### Soil Classification
Based on **Robertson (2009)** normalized CPT methodology:
- Normalized cone resistance: Qt = (qt - σvo) / σ'vo
- Normalized friction ratio: Fr = [fs / (qt - σvo)] × 100%
- Soil behavior type index: Ic = √[(3.47 - log Qt)² + (log Fr + 1.22)²]

### Correlations
Settlement parameters derived from published correlations:
- **E**: α_E × (qt - σvo), where α_E = 0.015 × 10^(0.55×Ic + 1.68)
- **Cc**: Based on plasticity index correlations (Jain et al. 2015)
- **Cr**: GMDH-type neural network (Kordnaeij et al. 2015)
- **OCR**: k × (qt / σ'vo), where k varies with soil type
- **M**: α_M × qt, where α_M varies with Qtn

### Settlement Calculations
- **Immediate Settlement**: S = Σ(Δσ × H / E) for each layer
- **Consolidation Settlement**: Terzaghi's theory with Cc and Cr
- Accounts for over-consolidation and stress history

## Technical Details

### Built With
- **Streamlit** - Web application framework
- **Pandas** - Data processing
- **NumPy** - Numerical calculations
- **Plotly** - Interactive visualizations
- **SciPy** - Scientific computations
- **FPDF** - PDF report generation

### References
- Robertson, P.K. (2009). "Interpretation of cone penetration tests - a unified approach"
- Settle3 CPT Theory Manual (Rocscience)
- Terzaghi's Consolidation Theory

## Notes

- The app performs calculations based on empirical correlations which have limitations
- Results should be verified by qualified geotechnical engineers
- Engineering judgment is required for final design decisions
- Parameters may need adjustment based on local experience and soil conditions

## Support

For questions about geotechnical engineering principles or settlement calculations, consult relevant technical literature and standards.
