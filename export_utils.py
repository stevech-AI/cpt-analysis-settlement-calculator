import pandas as pd
import numpy as np
from fpdf import FPDF
import io
from datetime import datetime

class PDFReport(FPDF):
    """
    Custom PDF report generator for CPT analysis results.
    """
    
    def __init__(self, title="CPT Analysis Report"):
        super().__init__()
        self.title_text = title
        
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self.title_text, 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(2)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()


class ExportManager:
    """
    Manage export functionality for CPT analysis results.
    """
    
    @staticmethod
    def export_to_excel(cpt_data: dict, layers_df: pd.DataFrame, 
                       params_df: pd.DataFrame, filename: str = "cpt_analysis.xlsx") -> io.BytesIO:
        """
        Export all CPT data, layers, and parameters to Excel file.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if 'data' in cpt_data:
                cpt_data['data'].to_excel(writer, sheet_name='CPT_Data', index=False)
            
            if len(layers_df) > 0:
                layers_df.to_excel(writer, sheet_name='Soil_Layers', index=False)
            
            if len(params_df) > 0:
                params_df.to_excel(writer, sheet_name='Parameters', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def export_settlement_results(settlement_results: dict, 
                                 params_df: pd.DataFrame,
                                 load_config: dict) -> io.BytesIO:
        """
        Export settlement calculation results to Excel.
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_data = {
                'Parameter': ['Applied Load (kN)', 'Footing Width (m)', 'Footing Length (m)',
                            'Footing Depth (m)', 'Contact Pressure (kPa)',
                            'Immediate Settlement (mm)', 'Consolidation Settlement (mm)',
                            'Total Settlement (mm)'],
                'Value': [
                    load_config['load'],
                    load_config['width'],
                    load_config['length'],
                    load_config['depth'],
                    load_config['load'] / (load_config['width'] * load_config['length']),
                    settlement_results['immediate_settlement_mm'],
                    settlement_results['consolidation_settlement_mm'],
                    settlement_results['total_settlement_mm']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            if 'immediate_details' in settlement_results:
                imm_df = pd.DataFrame(settlement_results['immediate_details'])
                imm_df.to_excel(writer, sheet_name='Immediate_Settlement', index=False)
            
            if 'consolidation_details' in settlement_results:
                cons_df = pd.DataFrame(settlement_results['consolidation_details'])
                cons_df.to_excel(writer, sheet_name='Consolidation_Settlement', index=False)
            
            if len(params_df) > 0:
                params_df.to_excel(writer, sheet_name='Layer_Parameters', index=False)
        
        output.seek(0)
        return output
    
    @staticmethod
    def generate_pdf_report(cpt_name: str, summary: dict, layers_df: pd.DataFrame,
                           params_df: pd.DataFrame, settlement_results: dict = None,
                           load_config: dict = None) -> io.BytesIO:
        """
        Generate comprehensive PDF report for CPT analysis.
        """
        pdf = PDFReport(f"CPT Analysis Report - {cpt_name}")
        pdf.add_page()
        
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        pdf.ln(5)
        
        pdf.chapter_title("1. CPT Summary")
        summary_text = f"""
CPT Name: {cpt_name}
Depth Range: {summary['depth_range'][0]:.2f} - {summary['depth_range'][1]:.2f} m
Average qc: {summary['avg_qc']:.1f} kPa
Average Ic: {summary['avg_Ic']:.2f}
Predominant Soil Type: {summary['predominant_soil']}
        """
        pdf.chapter_body(summary_text.strip())
        
        pdf.chapter_title("2. Identified Soil Layers")
        if len(layers_df) > 0:
            for idx, layer in layers_df.iterrows():
                layer_text = f"""
Layer {int(layer['layer_number'])}: {layer['soil_type']}
  Depth: {layer['top_depth']:.2f} - {layer['bottom_depth']:.2f} m
  Thickness: {layer['thickness']:.2f} m
  Average Ic: {layer['avg_Ic']:.2f}
  Average qc: {layer['avg_qc']:.1f} kPa
                """
                pdf.chapter_body(layer_text.strip())
        else:
            pdf.chapter_body("No layers identified.")
        
        pdf.add_page()
        pdf.chapter_title("3. Soil Parameters from CPT Correlations")
        if len(params_df) > 0:
            for idx, param in params_df.iterrows():
                param_text = f"""
Layer {int(param['layer_number'])}: {param['soil_type']}
  Young's Modulus (E): {param['youngs_modulus']:.0f} kPa
  Constrained Modulus (M): {param['constrained_modulus']:.0f} kPa
  Compression Index (Cc): {param['compression_index']:.3f}
  Recompression Index (Cr): {param['recompression_index']:.4f}
  OCR: {param['OCR']:.2f}
  Permeability (k): {param['permeability']:.2e} m/s
                """
                if param['friction_angle'] > 0:
                    param_text += f"  Friction Angle: {param['friction_angle']:.1f} degrees\n"
                if param['undrained_shear_strength'] > 0:
                    param_text += f"  Undrained Shear Strength: {param['undrained_shear_strength']:.1f} kPa\n"
                
                pdf.chapter_body(param_text.strip())
        
        if settlement_results is not None and load_config is not None:
            pdf.add_page()
            pdf.chapter_title("4. Settlement Analysis")
            
            loading_text = f"""
Applied Load: {load_config['load']:.1f} kN
Footing Dimensions: {load_config['width']:.2f} m x {load_config['length']:.2f} m
Footing Depth: {load_config['depth']:.2f} m
Contact Pressure: {load_config['load'] / (load_config['width'] * load_config['length']):.1f} kPa
            """
            pdf.chapter_body(loading_text.strip())
            
            pdf.chapter_title("Settlement Results")
            results_text = f"""
Immediate Settlement: {settlement_results['immediate_settlement_mm']:.1f} mm
Consolidation Settlement: {settlement_results['consolidation_settlement_mm']:.1f} mm
Total Settlement: {settlement_results['total_settlement_mm']:.1f} mm
            """
            pdf.chapter_body(results_text.strip())
        
        output = io.BytesIO()
        pdf_output = pdf.output(dest='S')
        # pdf_output is already bytes/bytearray, no need to encode
        if isinstance(pdf_output, str):
            output.write(pdf_output.encode('latin-1'))
        else:
            output.write(pdf_output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_layers_to_csv(layers_df: pd.DataFrame) -> io.BytesIO:
        """
        Export soil layers to CSV format.
        """
        output = io.BytesIO()
        layers_df.to_csv(output, index=False)
        output.seek(0)
        return output
