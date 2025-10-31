# CPT Analysis & Settlement Calculator

## Overview

This is a comprehensive geotechnical engineering web application built with Streamlit for analyzing Cone Penetration Test (CPT) data and calculating settlement predictions. The application implements Settle3 correlations and Robertson (2009) methodologies to process field CPT data, classify soils, identify soil layers, and estimate both immediate and consolidation settlements for foundation design.

The system provides an end-to-end workflow from uploading raw CPT Excel data through automated soil profiling to generating settlement calculations with visual analytics and exportable reports.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Application Framework
- **Frontend & Backend**: Streamlit single-file application (`app.py`) serving as the main UI controller
- **Session State Management**: Uses Streamlit's session state to persist CPT datasets and processed results across user interactions
- **Modular Design**: Functionality separated into domain-specific modules (processing, classification, correlations, settlement, export)

### Core Processing Pipeline

**CPT Data Processing** (`cpt_processor.py`)
- Flexible file parser supporting both Excel (.xlsx, .xls) and text files (.txt, .csv)
- Text parser auto-detects delimiters (comma, tab, semicolon, space)
- Automatic column detection using keyword matching for various naming conventions
- Handles depth, cone resistance (qc), sleeve friction (fs), and pore pressure (u2)
- Implements Robertson (2009) normalization calculations for Qt, Fr, Bq, and Ic parameters
- Uses atmospheric pressure reference (Pa = 100 kPa) and standard water unit weight

**Soil Classification** (`soil_classification.py`)
- Automated soil behavior type identification using Robertson classification charts
- Layer detection algorithm based on Ic value transitions with configurable threshold (0.3 change)
- Moving window approach to identify layer boundaries
- Minimum layer thickness enforcement with layer merging capability
- Creates comprehensive layer profiles with depth ranges and soil type classifications

**Geotechnical Correlations** (`correlations.py`)
- Implements multiple CPT-to-soil parameter correlations following Settle3 methodology
- Young's Modulus (E) calculation: alpha_E = 0.015 * 10^(0.55*Ic + 1.68)
- Constrained Modulus (M) with Qtn-based alpha_M factors (limited to 2-8 range)
- Compression Index (Cc), Recompression Index (Cr), and OCR calculations
- Parameter bounds enforcement to ensure physical validity

**Settlement Calculations** (`settlement_calc.py`)
- Boussinesq elastic theory implementation for stress distribution
- Simplified 2:1 method for rectangular footing stress propagation
- Immediate (elastic) settlement using Young's Modulus
- Consolidation settlement for clay layers using compression indices
- Layer-by-layer breakdown with stress increase validation
- Ensures stress only spreads below footing base level

### Data Visualization
- **Plotly Integration**: Interactive charts using plotly.graph_objects and plotly.express
- Multi-subplot layouts for CPT profile visualization (qc, fs, u2, Qt, Ic)
- Robertson classification charts with data point overlays and Ic contours
- Settlement distribution visualizations by layer
- Multi-CPT comparison capabilities

### Export & Reporting
**Export Manager** (`export_utils.py`)
- Excel export functionality using pandas for structured data output
- Custom PDF report generation using FPDF library
- Includes CPT data, layer definitions, calculated parameters, and settlement results
- Timestamped reports with formatted tables and headers

### Configuration & Parameters
**User-Configurable Settings** (via sidebar)
- Soil unit weight (14-25 kN/m³, default 18.0)
- Water table depth (0-50m, default 2.0m)
- Minimum layer thickness (0.1-5.0m, default 0.5m)
- Net area ratio for CPT corrections (0.5-1.0, default 0.8)

### Data Flow Architecture
1. User uploads CPT data (Excel or text files) → CPTProcessor validates and normalizes
2. Normalized data → RobertsonClassification assigns soil types
3. Classified data → SoilLayering identifies distinct layers
4. Layers + CPT data → CPTCorrelations calculates settlement parameters
5. Parameters + loading conditions → SettlementCalculator computes settlements
6. Results → ExportManager generates reports and downloads

### Testing & Sample Data
- `sample_cpt_data.py` provides synthetic CPT profiles for testing
- Simulates realistic soil profiles with sandy and clayey layer transitions
- Uses seeded random variations to mimic field data variability

## External Dependencies

### Python Libraries
- **streamlit**: Web application framework for UI and session management
- **pandas**: Data manipulation and Excel file I/O
- **numpy**: Numerical computations and array operations
- **plotly**: Interactive visualization library (graph_objects, express, subplots)
- **fpdf**: PDF report generation
- **openpyxl** (implicit): Excel file reading backend for pandas

### Geotechnical Standards
- Robertson (2009) CPT interpretation methodology
- Settle3 settlement calculation correlations
- Boussinesq elastic theory for stress distribution
- Terzaghi's consolidation theory

### File Formats
- **Input**: Excel files (.xlsx, .xls) and text files (.txt, .csv) with flexible column naming and automatic delimiter detection
- **Output**: Excel workbooks with multiple sheets, PDF reports

### Potential Future Integrations
The architecture supports future addition of:
- Database persistence for CPT data storage (currently in-memory session state)
- User authentication for multi-user project management
- Cloud storage integration for file uploads
- Additional correlation methods (Schmertmann, Mayne & Poulos)
- 3D visualization of multiple CPT locations
- Automated report emailing functionality