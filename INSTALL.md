# Installation Guide

## Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

## Quick Start

### Option 1: Install from pyproject.toml (Recommended)
```bash
# Clone the repository
git clone https://github.com/stevech-AI/cpt-analysis-settlement-calculator.git
cd cpt-analysis-settlement-calculator

# Install dependencies
pip install .
```

### Option 2: Manual Installation
```bash
# Clone the repository
git clone https://github.com/stevech-AI/cpt-analysis-settlement-calculator.git
cd cpt-analysis-settlement-calculator

# Install dependencies manually
pip install streamlit>=1.51.0 pandas>=2.3.3 numpy>=2.3.4 plotly>=6.3.1 fpdf2>=2.8.5 openpyxl>=3.1.5 scipy>=1.16.3 seaborn>=0.13.2 matplotlib>=3.10.7 pillow>=12.0.0
```

### Option 3: Using a Virtual Environment (Recommended for Development)
```bash
# Clone the repository
git clone https://github.com/stevech-AI/cpt-analysis-settlement-calculator.git
cd cpt-analysis-settlement-calculator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install .
```

## Running the Application

Once dependencies are installed, run:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

## Required Dependencies

The application requires the following Python packages:
- **streamlit** (>=1.51.0) - Web application framework
- **pandas** (>=2.3.3) - Data manipulation
- **numpy** (>=2.3.4) - Numerical computing
- **plotly** (>=6.3.1) - Interactive visualizations
- **fpdf2** (>=2.8.5) - PDF generation
- **openpyxl** (>=3.1.5) - Excel file handling
- **scipy** (>=1.16.3) - Scientific computing
- **seaborn** (>=0.13.2) - Statistical visualizations
- **matplotlib** (>=3.10.7) - Plotting library
- **pillow** (>=12.0.0) - Image processing

## Troubleshooting

### Port Already in Use
If port 8501 is already in use, you can specify a different port:
```bash
streamlit run app.py --server.port 8502
```

### Missing Dependencies
If you encounter import errors, ensure all dependencies are installed:
```bash
pip list | grep -E 'streamlit|pandas|numpy|plotly|fpdf2|openpyxl|scipy|seaborn|matplotlib|pillow'
```

### Python Version
Check your Python version:
```bash
python --version
```
Make sure it's 3.11 or higher.

## Testing the Installation

After installation, you can test with the included sample data:
1. Run `streamlit run app.py`
2. Navigate to "📤 Upload CPT Data" tab
3. Upload `Sample_CPT_01.xlsx` or `Sample_CPT_02.xlsx`
4. Explore the various analysis tabs

## Additional Configuration

The application uses Streamlit configuration located in `.streamlit/config.toml`. The default configuration is optimized for use, but you can customize:
- Server settings (port, address)
- Theme colors
- File upload limits

For more Streamlit configuration options, see: https://docs.streamlit.io/library/advanced-features/configuration
