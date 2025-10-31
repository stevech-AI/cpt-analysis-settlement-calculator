import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io

from cpt_processor import CPTProcessor
from soil_classification import (SoilLayering, RobertsonClassification, 
                                 Robertson1990Classification, Schneider2008Classification,
                                 ClassificationComparator)
from correlations import CPTCorrelations
from settlement_calc import SettlementCalculator
from export_utils import ExportManager
from visualization_3d import CPT3DVisualizer
from soil_database import SoilPropertyDatabase

st.set_page_config(
    page_title="CPT Analysis & Settlement Calculator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏗️ CPT Analysis & Settlement Calculator")
st.markdown("*Geotechnical analysis tool based on Settle3 correlations*")

if 'cpt_data' not in st.session_state:
    st.session_state.cpt_data = {}
if 'processed_cpts' not in st.session_state:
    st.session_state.processed_cpts = {}
if 'cpt_coordinates' not in st.session_state:
    st.session_state.cpt_coordinates = {}

with st.sidebar:
    st.header("⚙️ Analysis Parameters")
    
    st.subheader("Soil Properties")
    gamma_soil = st.number_input("Unit Weight of Soil (kN/m³)", 
                                 min_value=14.0, max_value=25.0, value=18.0, step=0.5)
    water_table_depth = st.number_input("Water Table Depth (m)", 
                                        min_value=0.0, max_value=50.0, value=2.0, step=0.5)
    
    st.subheader("Soil Layering")
    min_layer_thickness = st.number_input("Minimum Layer Thickness (m)", 
                                         min_value=0.1, max_value=5.0, value=0.5, step=0.1)
    
    st.subheader("CPT Processing")
    area_ratio = st.number_input("Net Area Ratio", 
                                 min_value=0.5, max_value=1.0, value=0.8, step=0.05)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📤 Upload CPT Data", 
    "📊 CPT Profiles", 
    "🗺️ Soil Classification",
    "📏 Soil Layers",
    "📈 Correlations",
    "🏗️ Settlement Analysis",
    "🌐 3D Visualization"
])

with tab1:
    st.header("Upload CPT Data Files")
    st.markdown("""
    Upload Excel or text files containing CPT data. The file should contain columns for:
    - **Depth** (m)
    - **qc** - Cone resistance (kPa or MPa)
    - **fs** - Sleeve friction (kPa)
    - **u2** - Pore pressure (kPa) [optional]
    
    **Supported formats:**
    - Excel files (.xlsx, .xls)
    - Text files (.txt, .csv) with comma, tab, semicolon, or space delimiters
    """)
    
    uploaded_files = st.file_uploader(
        "Choose files", 
        type=['xlsx', 'xls', 'txt', 'csv'],
        accept_multiple_files=True,
        key="cpt_upload"
    )
    
    if uploaded_files:
        processor = CPTProcessor()
        
        for file in uploaded_files:
            file_name = file.name.replace('.xlsx', '').replace('.xls', '').replace('.txt', '').replace('.csv', '')
            
            if file_name not in st.session_state.cpt_data:
                try:
                    with st.spinner(f"Processing {file_name}..."):
                        result = processor.process_cpt_file(
                            file, 
                            file_name, 
                            gamma_soil, 
                            water_table_depth
                        )
                        st.session_state.cpt_data[file_name] = result
                        
                        layering = SoilLayering(min_layer_thickness)
                        layers = layering.process_layering(result['data'])
                        
                        correlator = CPTCorrelations()
                        layer_params = correlator.process_all_layers(layers)
                        
                        st.session_state.processed_cpts[file_name] = {
                            'data': result['data'],
                            'layers': layers,
                            'parameters': layer_params,
                            'summary': result['summary']
                        }
                    
                    st.success(f"✅ Successfully processed: {file_name}")
                except Exception as e:
                    st.error(f"❌ Error processing {file_name}: {str(e)}")
        
        if st.session_state.cpt_data:
            st.subheader("Loaded CPT Files")
            for name, data in st.session_state.cpt_data.items():
                summary = data['summary']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CPT Name", name)
                with col2:
                    st.metric("Depth Range", f"{summary['depth_range'][0]:.1f} - {summary['depth_range'][1]:.1f} m")
                with col3:
                    st.metric("Predominant Soil", summary['predominant_soil'])

with tab2:
    st.header("CPT Profiles")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    else:
        selected_cpts = st.multiselect(
            "Select CPTs to display",
            options=list(st.session_state.processed_cpts.keys()),
            default=list(st.session_state.processed_cpts.keys())
        )
        
        if selected_cpts:
            profile_type = st.selectbox(
                "Select Profile Type",
                ["Cone Resistance (qc)", "Friction Ratio (Rf)", "Pore Pressure (u2)", 
                 "Normalized Parameters (Qt, Fr)", "Soil Behavior Index (Ic)"]
            )
            
            fig = make_subplots(
                rows=1, cols=1,
                subplot_titles=[profile_type]
            )
            
            for cpt_name in selected_cpts:
                data = st.session_state.processed_cpts[cpt_name]['data']
                
                if "Cone Resistance" in profile_type:
                    fig.add_trace(go.Scatter(
                        x=data['qc'], y=data['depth'],
                        mode='lines', name=f"{cpt_name} - qc",
                        line=dict(width=2)
                    ))
                    fig.update_xaxes(title_text="Cone Resistance qc (kPa)")
                
                elif "Friction Ratio" in profile_type:
                    fig.add_trace(go.Scatter(
                        x=data['Rf'], y=data['depth'],
                        mode='lines', name=f"{cpt_name} - Rf",
                        line=dict(width=2)
                    ))
                    fig.update_xaxes(title_text="Friction Ratio Rf (%)")
                
                elif "Pore Pressure" in profile_type:
                    fig.add_trace(go.Scatter(
                        x=data['u2'], y=data['depth'],
                        mode='lines', name=f"{cpt_name} - u2",
                        line=dict(width=2)
                    ))
                    fig.update_xaxes(title_text="Pore Pressure u2 (kPa)")
                
                elif "Normalized" in profile_type:
                    fig.add_trace(go.Scatter(
                        x=data['Qt1'], y=data['depth'],
                        mode='lines', name=f"{cpt_name} - Qt",
                        line=dict(width=2)
                    ))
                    fig.update_xaxes(title_text="Normalized Cone Resistance Qt", type='log')
                
                elif "Soil Behavior" in profile_type:
                    fig.add_trace(go.Scatter(
                        x=data['Ic'], y=data['depth'],
                        mode='lines', name=f"{cpt_name} - Ic",
                        line=dict(width=2)
                    ))
                    fig.update_xaxes(title_text="Soil Behavior Type Index Ic")
            
            fig.update_yaxes(title_text="Depth (m)", autorange="reversed")
            fig.update_layout(height=600, hovermode='closest')
            
            st.plotly_chart(fig, use_container_width=True)
            
            if len(st.session_state.processed_cpts) > 1:
                st.markdown("---")
                st.subheader("📊 Multi-CPT Comparison & Batch Export")
                
                comparison_data = []
                for cpt_name, cpt_info in st.session_state.processed_cpts.items():
                    summary = cpt_info['summary']
                    layers = cpt_info['layers']
                    params = cpt_info['parameters']
                    
                    comparison_data.append({
                        'CPT Name': cpt_name,
                        'Max Depth (m)': summary['depth_range'][1],
                        'Avg qc (kPa)': summary['avg_qc'],
                        'Avg Ic': summary['avg_Ic'],
                        'Number of Layers': len(layers),
                        'Dominant Soil': summary['predominant_soil'],
                        'Avg E (kPa)': params['youngs_modulus'].mean() if len(params) > 0 else 0,
                        'Avg OCR': params['OCR'].mean() if len(params) > 0 else 0
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df.round(2), hide_index=True, use_container_width=True)
                
                col_batch1, col_batch2 = st.columns(2)
                
                with col_batch1:
                    st.markdown("**Batch Export Options**")
                    if st.button("📦 Generate Batch Report", key="batch_report"):
                        with st.spinner("Generating batch report for all CPTs..."):
                            # Create a combined Excel workbook with all CPTs
                            exporter = ExportManager()
                            output = io.BytesIO()
                            
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                # Summary sheet
                                comparison_df.to_excel(writer, sheet_name='Summary', index=False)
                                
                                # Individual CPT sheets
                                for cpt_name, cpt_info in st.session_state.processed_cpts.items():
                                    # Truncate sheet name to 31 chars (Excel limit)
                                    sheet_name = cpt_name[:28] + "..." if len(cpt_name) > 31 else cpt_name
                                    
                                    layers = cpt_info['layers']
                                    params = cpt_info['parameters']
                                    
                                    # Combine layers and params
                                    combined = pd.merge(
                                        layers[['layer_number', 'soil_type', 'top_depth', 'bottom_depth', 'thickness']],
                                        params[['layer_number', 'youngs_modulus', 'compression_index', 'OCR']],
                                        on='layer_number',
                                        how='left'
                                    )
                                    
                                    combined.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            output.seek(0)
                            st.session_state['batch_report'] = output.getvalue()
                            st.success("✅ Batch report generated!")
                
                with col_batch2:
                    if 'batch_report' in st.session_state and isinstance(st.session_state['batch_report'], bytes):
                        st.markdown("**Download Batch Report**")
                        st.download_button(
                            label="📥 Download All CPTs (Excel)",
                            data=st.session_state['batch_report'],
                            file_name="batch_cpt_analysis.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_batch"
                        )
                        st.info(f"📊 Report includes {len(st.session_state.processed_cpts)} CPT datasets")

with tab3:
    st.header("CPT Soil Classification Methods")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_cpt = st.selectbox(
                "Select CPT for classification",
                options=list(st.session_state.processed_cpts.keys())
            )
        
        with col2:
            classification_method = st.selectbox(
                "Classification Method",
                options=["Robertson 2009", "Robertson 1990", "Schneider 2008", "Method Comparison"]
            )
        
        if selected_cpt:
            data = st.session_state.processed_cpts[selected_cpt]['data']
            
            if classification_method == "Robertson 2009":
                st.subheader("Robertson (2009) Classification Chart")
                st.markdown("*Latest CPT soil behavior type classification*")
                
                fig = go.Figure()
                
                Qt_range = (1, 1000)
                classification = RobertsonClassification()
                contours = classification.calculate_Ic_contours(Qt_range)
                
                for Ic_value, contour_data in contours.items():
                    fig.add_trace(go.Scatter(
                        x=contour_data[:, 0],
                        y=contour_data[:, 1],
                        mode='lines',
                        name=f'Ic = {Ic_value}',
                        line=dict(color='gray', dash='dash', width=1),
                        showlegend=True
                    ))
                
                fig.add_trace(go.Scatter(
                    x=data['Qt1'],
                    y=data['Fr'],
                    mode='markers',
                    name=selected_cpt,
                    marker=dict(
                        size=6,
                        color=data['Ic'],
                        colorscale='RdYlBu_r',
                        showscale=True,
                        colorbar=dict(title="Ic"),
                        line=dict(width=0.5, color='white')
                    ),
                    text=data['depth'],
                    hovertemplate='<b>Depth: %{text:.1f} m</b><br>Qt: %{x:.1f}<br>Fr: %{y:.2f}%<extra></extra>'
                ))
                
                fig.update_xaxes(title_text="Normalized Cone Resistance Qt", type='log', range=[0, 3])
                fig.update_yaxes(title_text="Normalized Friction Ratio Fr (%)", type='log', range=[-1, 1])
                fig.update_layout(
                    height=600,
                    title=f"Robertson (2009) Classification Chart - {selected_cpt}",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Soil Type Distribution")
                soil_type_counts = data['soil_type'].value_counts()
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=soil_type_counts.index,
                    values=soil_type_counts.values,
                    hole=0.3
                )])
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            elif classification_method == "Robertson 1990":
                st.subheader("Robertson (1990) Classification Chart")
                st.markdown("*Normalized CPT soil behavior type with 9 zones*")
                
                # Calculate Robertson 1990 classifications
                data_r1990 = data.copy()
                data_r1990['soil_type_r1990'] = data_r1990.apply(
                    lambda row: Robertson1990Classification.classify_soil_type(
                        row['Qt1'], row['Fr'], row['Ic']
                    ), axis=1
                )
                
                fig = go.Figure()
                
                Qt_range = (1, 1000)
                contours = Robertson1990Classification.calculate_Ic_contours(Qt_range)
                
                for Ic_value, contour_data in contours.items():
                    fig.add_trace(go.Scatter(
                        x=contour_data[:, 0],
                        y=contour_data[:, 1],
                        mode='lines',
                        name=f'Ic = {Ic_value}',
                        line=dict(color='gray', dash='dash', width=1),
                        showlegend=True
                    ))
                
                fig.add_trace(go.Scatter(
                    x=data_r1990['Qt1'],
                    y=data_r1990['Fr'],
                    mode='markers',
                    name=selected_cpt,
                    marker=dict(
                        size=6,
                        color=data_r1990['Ic'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Ic"),
                        line=dict(width=0.5, color='white')
                    ),
                    text=data_r1990['depth'],
                    hovertemplate='<b>Depth: %{text:.1f} m</b><br>Qt: %{x:.1f}<br>Fr: %{y:.2f}%<extra></extra>'
                ))
                
                fig.update_xaxes(title_text="Normalized Cone Resistance Qt", type='log', range=[0, 3])
                fig.update_yaxes(title_text="Normalized Friction Ratio Fr (%)", type='log', range=[-1, 1])
                fig.update_layout(
                    height=600,
                    title=f"Robertson (1990) Classification Chart - {selected_cpt}",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Soil Type Distribution")
                soil_type_counts = data_r1990['soil_type_r1990'].value_counts()
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=soil_type_counts.index,
                    values=soil_type_counts.values,
                    hole=0.3
                )])
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            elif classification_method == "Schneider 2008":
                st.subheader("Schneider et al. (2008) Classification Chart")
                st.markdown("*Piezocone classification focusing on drainage conditions*")
                
                # Calculate Schneider 2008 classifications
                data_s2008 = data.copy()
                data_s2008['soil_type_s2008'] = data_s2008.apply(
                    lambda row: Schneider2008Classification.classify_soil_type(
                        row['Qt1'], row['Fr']
                    ), axis=1
                )
                
                fig = go.Figure()
                
                # Add zone boundaries
                boundaries = Schneider2008Classification.calculate_zone_boundaries()
                
                for boundary_name, boundary_data in boundaries.items():
                    fig.add_trace(go.Scatter(
                        x=boundary_data[:, 0],
                        y=boundary_data[:, 1],
                        mode='lines',
                        name=boundary_name.replace('_', ' ').title(),
                        line=dict(color='black', dash='dash', width=2),
                        showlegend=True
                    ))
                
                # Add data points
                fig.add_trace(go.Scatter(
                    x=data_s2008['Qt1'],
                    y=data_s2008['Fr'],
                    mode='markers',
                    name=selected_cpt,
                    marker=dict(
                        size=6,
                        color=data_s2008['Ic'],
                        colorscale='Plasma',
                        showscale=True,
                        colorbar=dict(title="Ic"),
                        line=dict(width=0.5, color='white')
                    ),
                    text=data_s2008['depth'],
                    hovertemplate='<b>Depth: %{text:.1f} m</b><br>Q: %{x:.1f}<br>F: %{y:.2f}%<extra></extra>'
                ))
                
                fig.update_xaxes(title_text="Normalized Cone Resistance Q", type='log', range=[0, 3])
                fig.update_yaxes(title_text="Friction Ratio F (%)", type='log', range=[-1, 1])
                fig.update_layout(
                    height=600,
                    title=f"Schneider (2008) Q-F Classification Chart - {selected_cpt}",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Soil Type Distribution")
                soil_type_counts = data_s2008['soil_type_s2008'].value_counts()
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=soil_type_counts.index,
                    values=soil_type_counts.values,
                    hole=0.3
                )])
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            elif classification_method == "Method Comparison":
                st.subheader("Classification Method Comparison")
                st.markdown("*Compare soil classifications from different methods*")
                
                col_comp1, col_comp2 = st.columns(2)
                
                with col_comp1:
                    method1 = st.selectbox(
                        "Method 1",
                        options=["Robertson2009", "Robertson1990", "Schneider2008"],
                        key="method1_select"
                    )
                
                with col_comp2:
                    method2 = st.selectbox(
                        "Method 2",
                        options=["Robertson2009", "Robertson1990", "Schneider2008"],
                        key="method2_select",
                        index=1
                    )
                
                # Perform comparison
                comparator = ClassificationComparator()
                comparison_data = comparator.compare_classifications(data, method1, method2)
                stats = comparator.get_agreement_statistics(comparison_data)
                
                # Display statistics
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    st.metric("Total Points", stats['total_points'])
                with col_stat2:
                    st.metric("Agreed Points", stats['agreed_points'])
                with col_stat3:
                    st.metric("Agreement %", f"{stats['agreement_percentage']:.1f}%")
                
                # Visualization
                fig_comp = go.Figure()
                
                # Color code by agreement
                colors = ['green' if agree else 'red' for agree in comparison_data['agreement']]
                
                fig_comp.add_trace(go.Scatter(
                    x=comparison_data['Qt1'],
                    y=comparison_data['Fr'],
                    mode='markers',
                    marker=dict(
                        size=6,
                        color=colors,
                        line=dict(width=0.5, color='white')
                    ),
                    text=[f"Depth: {d:.1f}m<br>{method1}: {s1}<br>{method2}: {s2}" 
                          for d, s1, s2 in zip(comparison_data['depth'], 
                                               comparison_data['method1_soil_type'],
                                               comparison_data['method2_soil_type'])],
                    hovertemplate='%{text}<extra></extra>',
                    name='CPT Data'
                ))
                
                fig_comp.update_xaxes(title_text="Normalized Cone Resistance Qt", type='log', range=[0, 3])
                fig_comp.update_yaxes(title_text="Normalized Friction Ratio Fr (%)", type='log', range=[-1, 1])
                fig_comp.update_layout(
                    height=600,
                    title=f"Comparison: {method1} vs {method2}<br>Green=Agree, Red=Disagree",
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # Disagreement table
                st.subheader("Points of Disagreement")
                disagreed = comparison_data[~comparison_data['agreement']][['depth', 'Qt1', 'Fr', 'Ic', 
                                                                             'method1_soil_type', 'method2_soil_type']].copy()
                disagreed = disagreed.rename(columns={
                    'depth': 'Depth (m)',
                    'Qt1': 'Qt',
                    'Fr': 'Fr (%)',
                    'Ic': 'Ic',
                    'method1_soil_type': method1,
                    'method2_soil_type': method2
                })
                
                if len(disagreed) > 0:
                    st.dataframe(disagreed.round(2), hide_index=True, use_container_width=True)
                else:
                    st.success("✅ All classifications agree between the two methods!")

with tab4:
    st.header("Identified Soil Layers")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    else:
        selected_cpt = st.selectbox(
            "Select CPT for layer profile",
            options=list(st.session_state.processed_cpts.keys()),
            key="layer_select"
        )
        
        if selected_cpt:
            layers = st.session_state.processed_cpts[selected_cpt]['layers']
            
            if len(layers) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = go.Figure()
                    
                    for _, layer in layers.iterrows():
                        mid_depth = (layer['top_depth'] + layer['bottom_depth']) / 2
                        
                        fig.add_trace(go.Bar(
                            x=[layer['thickness']],
                            y=[f"Layer {layer['layer_number']}"],
                            orientation='h',
                            name=layer['soil_type'],
                            text=f"{layer['soil_type']}<br>{layer['thickness']:.2f}m",
                            textposition='inside',
                            hovertemplate=f"<b>Layer {layer['layer_number']}</b><br>" +
                                        f"Depth: {layer['top_depth']:.2f} - {layer['bottom_depth']:.2f} m<br>" +
                                        f"Thickness: {layer['thickness']:.2f} m<br>" +
                                        f"Soil: {layer['soil_type']}<br>" +
                                        f"Ic: {layer['avg_Ic']:.2f}<extra></extra>"
                        ))
                    
                    fig.update_xaxes(title_text="Thickness (m)")
                    fig.update_yaxes(title_text="Layer")
                    fig.update_layout(
                        height=max(400, len(layers) * 50),
                        showlegend=False,
                        title=f"Soil Layer Profile - {selected_cpt}"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Layer Summary")
                    st.dataframe(
                        layers[['layer_number', 'top_depth', 'bottom_depth', 
                               'thickness', 'soil_type', 'avg_Ic']].round(2),
                        hide_index=True,
                        height=400
                    )
                    
                    st.subheader("Export Layers")
                    exporter = ExportManager()
                    csv_data = exporter.export_layers_to_csv(layers)
                    st.download_button(
                        label="📥 Download Layers (CSV)",
                        data=csv_data,
                        file_name=f"{selected_cpt}_layers.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No layers identified for this CPT.")

with tab5:
    st.header("CPT Correlations for Settlement Parameters")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    else:
        selected_cpt = st.selectbox(
            "Select CPT for correlations",
            options=list(st.session_state.processed_cpts.keys()),
            key="corr_select"
        )
        
        if selected_cpt:
            params = st.session_state.processed_cpts[selected_cpt]['parameters']
            
            if len(params) > 0:
                st.subheader("Settlement Parameters by Layer")
                
                display_params = params[[
                    'layer_number', 'soil_type', 'thickness', 'Ic',
                    'youngs_modulus', 'constrained_modulus',
                    'compression_index', 'recompression_index',
                    'OCR', 'friction_angle', 'undrained_shear_strength'
                ]].copy()
                
                display_params.columns = [
                    'Layer', 'Soil Type', 'H (m)', 'Ic',
                    'E (kPa)', 'M (kPa)', 'Cc', 'Cr',
                    'OCR', 'φ (°)', 'Su (kPa)'
                ]
                
                st.dataframe(display_params.round(2), hide_index=True, use_container_width=True)
                
                st.subheader("Parameter Visualizations")
                
                param_cols = st.columns(2)
                
                with param_cols[0]:
                    fig_e = go.Figure()
                    fig_e.add_trace(go.Bar(
                        x=params['layer_number'],
                        y=params['youngs_modulus'],
                        name="Young's Modulus",
                        marker_color='lightblue'
                    ))
                    fig_e.update_layout(
                        title="Young's Modulus (E) by Layer",
                        xaxis_title="Layer Number",
                        yaxis_title="E (kPa)",
                        height=300
                    )
                    st.plotly_chart(fig_e, use_container_width=True)
                
                with param_cols[1]:
                    fig_cc = go.Figure()
                    clay_layers = params[params['Ic'] > 2.6]
                    if len(clay_layers) > 0:
                        fig_cc.add_trace(go.Bar(
                            x=clay_layers['layer_number'],
                            y=clay_layers['compression_index'],
                            name="Cc",
                            marker_color='coral'
                        ))
                        fig_cc.add_trace(go.Bar(
                            x=clay_layers['layer_number'],
                            y=clay_layers['recompression_index'],
                            name="Cr",
                            marker_color='lightcoral'
                        ))
                    fig_cc.update_layout(
                        title="Compression Indices (Cc, Cr) for Clay Layers",
                        xaxis_title="Layer Number",
                        yaxis_title="Index",
                        height=300
                    )
                    st.plotly_chart(fig_cc, use_container_width=True)
                
                param_cols2 = st.columns(2)
                
                with param_cols2[0]:
                    fig_ocr = go.Figure()
                    fig_ocr.add_trace(go.Bar(
                        x=params['layer_number'],
                        y=params['OCR'],
                        name="OCR",
                        marker_color='lightgreen'
                    ))
                    fig_ocr.update_layout(
                        title="Over-Consolidation Ratio (OCR) by Layer",
                        xaxis_title="Layer Number",
                        yaxis_title="OCR",
                        height=300
                    )
                    st.plotly_chart(fig_ocr, use_container_width=True)
                
                with param_cols2[1]:
                    fig_perm = go.Figure()
                    fig_perm.add_trace(go.Bar(
                        x=params['layer_number'],
                        y=params['permeability'],
                        name="Permeability",
                        marker_color='purple'
                    ))
                    fig_perm.update_layout(
                        title="Permeability (k) by Layer",
                        xaxis_title="Layer Number",
                        yaxis_title="k (m/s)",
                        yaxis_type="log",
                        height=300
                    )
                    st.plotly_chart(fig_perm, use_container_width=True)
                
                st.subheader("Export Data")
                exporter = ExportManager()
                layers = st.session_state.processed_cpts[selected_cpt]['layers']
                excel_data = exporter.export_to_excel(
                    st.session_state.processed_cpts[selected_cpt],
                    layers,
                    params,
                    f"{selected_cpt}_analysis.xlsx"
                )
                st.download_button(
                    label="📥 Download Complete Analysis (Excel)",
                    data=excel_data,
                    file_name=f"{selected_cpt}_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.markdown("---")
                
                st.subheader("📚 Soil Property Database & Validation")
                
                soil_db = SoilPropertyDatabase()
                
                tab_db1, tab_db2 = st.tabs(["Parameter Validation", "Reference Database"])
                
                with tab_db1:
                    st.markdown("*Compare calculated parameters against typical ranges for soil types*")
                    
                    warnings = soil_db.compare_layer_properties(params)
                    
                    if len(warnings) > 0:
                        st.warning(f"⚠️ Found {len(warnings)} parameter(s) outside typical ranges:")
                        
                        warning_df = pd.DataFrame(warnings)
                        warning_df.columns = ['Layer', 'Soil Type', 'Parameter', 'Value', 'Message']
                        st.dataframe(warning_df, hide_index=True, use_container_width=True)
                        
                        st.info("💡 These warnings indicate parameters that fall outside typical literature ranges. Review correlations and site conditions.")
                    else:
                        st.success("✅ All calculated parameters are within typical ranges for their soil types!")
                
                with tab_db2:
                    st.markdown("*Reference ranges for typical soil types from geotechnical literature*")
                    
                    db_summary = soil_db.get_database_summary()
                    st.dataframe(db_summary, hide_index=True, use_container_width=True)
                    
                    st.info("💡 Reference ranges based on geotechnical engineering standards and literature. Actual site conditions may vary.")
            else:
                st.warning("No parameters calculated for this CPT.")

with tab6:
    st.header("Settlement Analysis")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    else:
        st.subheader("Loading Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            load_kN = st.number_input("Applied Load (kN)", min_value=0.0, value=1000.0, step=100.0)
            footing_width = st.number_input("Footing Width (m)", min_value=0.1, value=2.0, step=0.1)
        
        with col2:
            footing_length = st.number_input("Footing Length (m)", min_value=0.1, value=2.0, step=0.1)
            footing_depth = st.number_input("Footing Depth (m)", min_value=0.0, value=1.0, step=0.1)
        
        with col3:
            st.metric("Contact Pressure", f"{load_kN / (footing_width * footing_length):.1f} kPa")
            st.metric("Water Table Depth", f"{water_table_depth:.1f} m")
        
        selected_cpt_settle = st.selectbox(
            "Select CPT for settlement analysis",
            options=list(st.session_state.processed_cpts.keys()),
            key="settle_select"
        )
        
        if selected_cpt_settle and st.button("Calculate Settlement", type="primary"):
            params = st.session_state.processed_cpts[selected_cpt_settle]['parameters']
            
            calculator = SettlementCalculator()
            
            settlement_results = calculator.calculate_total_settlement(
                params, load_kN, footing_width, footing_length,
                footing_depth, water_table_depth
            )
            
            # Store in session state
            st.session_state['settlement_results'] = settlement_results
            st.session_state['settlement_params'] = {
                'load': load_kN,
                'width': footing_width,
                'length': footing_length,
                'depth': footing_depth,
                'water_table': water_table_depth,
                'cpt_name': selected_cpt_settle
            }
            st.session_state['settlement_calculator'] = calculator
            
            st.success("✅ Settlement calculation complete!")
        
        # Display results if they exist in session state
        if 'settlement_results' in st.session_state:
            settlement_results = st.session_state['settlement_results']
            settlement_params_stored = st.session_state.get('settlement_params', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Immediate Settlement", f"{settlement_results['immediate_settlement_mm']:.1f} mm")
            with col2:
                st.metric("Consolidation Settlement", f"{settlement_results['consolidation_settlement_mm']:.1f} mm")
            with col3:
                st.metric("Total Settlement", f"{settlement_results['total_settlement_mm']:.1f} mm", 
                         delta=f"{settlement_results['total_settlement_mm']:.1f} mm")
            
            st.subheader("Settlement by Layer")
            
            immediate_df = pd.DataFrame(settlement_results['immediate_details'])
            consolidation_df = pd.DataFrame(settlement_results['consolidation_details'])
            
            tabs_settle = st.tabs(["Immediate Settlement", "Consolidation Settlement"])
            
            with tabs_settle[0]:
                st.dataframe(immediate_df.round(2), hide_index=True, use_container_width=True)
                
                fig_imm = go.Figure()
                fig_imm.add_trace(go.Bar(
                    x=immediate_df['layer_number'],
                    y=immediate_df['settlement_mm'],
                    marker_color='skyblue',
                    text=immediate_df['settlement_mm'].round(1),
                    textposition='outside'
                ))
                fig_imm.update_layout(
                    title="Immediate Settlement by Layer",
                    xaxis_title="Layer Number",
                    yaxis_title="Settlement (mm)",
                    height=400
                )
                st.plotly_chart(fig_imm, use_container_width=True)
            
            with tabs_settle[1]:
                st.dataframe(consolidation_df.round(2), hide_index=True, use_container_width=True)
                
                fig_cons = go.Figure()
                fig_cons.add_trace(go.Bar(
                    x=consolidation_df['layer_number'],
                    y=consolidation_df['settlement_mm'],
                    marker_color='coral',
                    text=consolidation_df['settlement_mm'].round(1),
                    textposition='outside'
                ))
                fig_cons.update_layout(
                    title="Consolidation Settlement by Layer",
                    xaxis_title="Layer Number",
                    yaxis_title="Settlement (mm)",
                    height=400
                )
                st.plotly_chart(fig_cons, use_container_width=True)
            
            st.markdown("---")
            
            st.subheader("⏱️ Time-Consolidation Analysis")
            st.markdown("*Analyze settlement progression over time including secondary compression (creep)*")
            
            col_time1, col_time2, col_time3 = st.columns(3)
            
            with col_time1:
                max_time = st.number_input(
                    "Maximum Time (years)",
                    min_value=1.0,
                    max_value=100.0,
                    value=50.0,
                    step=5.0,
                    help="Time period for consolidation analysis"
                )
            
            with col_time2:
                include_secondary = st.checkbox(
                    "Include Secondary Compression",
                    value=True,
                    help="Add long-term creep effects"
                )
            
            with col_time3:
                c_alpha_ratio = st.number_input(
                    "C_α/Cc Ratio",
                    min_value=0.01,
                    max_value=0.10,
                    value=0.02,
                    step=0.01,
                    help="Secondary compression index ratio (typical 0.02-0.05)"
                )
            
            if st.button("Generate Time-Settlement Curve", key="time_curve_btn"):
                with st.spinner("Calculating time-dependent settlement..."):
                    # Get stored calculator and params
                    calculator_stored = st.session_state.get('settlement_calculator', SettlementCalculator())
                    cpt_name_stored = settlement_params_stored.get('cpt_name', selected_cpt_settle)
                    params_stored = st.session_state.processed_cpts[cpt_name_stored]['parameters']
                    
                    time_curve_data = calculator_stored.generate_time_settlement_curve(
                        params_stored, 
                        settlement_params_stored.get('load', load_kN), 
                        settlement_params_stored.get('width', footing_width), 
                        settlement_params_stored.get('length', footing_length),
                        max_time_years=max_time,
                        num_points=100,
                        footing_depth=settlement_params_stored.get('depth', footing_depth),
                        water_table_depth=settlement_params_stored.get('water_table', water_table_depth),
                        include_secondary=include_secondary,
                        c_alpha=c_alpha_ratio
                    )
                    
                    # Store in session state for persistence
                    st.session_state['time_curve_data'] = time_curve_data
                    st.success("✅ Time-consolidation curve generated!")
            
            if 'time_curve_data' in st.session_state:
                time_curve_data = st.session_state['time_curve_data']
                
                # Main time-settlement curve
                fig_time = go.Figure()
                
                # Primary consolidation curve
                fig_time.add_trace(go.Scatter(
                    x=time_curve_data['time_years'],
                    y=time_curve_data['settlement_primary_mm'],
                    mode='lines',
                    name='Primary Consolidation',
                    line=dict(color='blue', width=2),
                    hovertemplate='Time: %{x:.2f} years<br>Settlement: %{y:.1f} mm<extra></extra>'
                ))
                
                # Total settlement (with secondary compression if included)
                if time_curve_data['secondary_compression_included']:
                    fig_time.add_trace(go.Scatter(
                        x=time_curve_data['time_years'],
                        y=time_curve_data['settlement_total_mm'],
                        mode='lines',
                        name='Total (Primary + Secondary)',
                        line=dict(color='red', width=2, dash='dash'),
                        hovertemplate='Time: %{x:.2f} years<br>Settlement: %{y:.1f} mm<extra></extra>'
                    ))
                
                # Add horizontal line for immediate settlement
                fig_time.add_hline(
                    y=time_curve_data['immediate_settlement_mm'],
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"Immediate: {time_curve_data['immediate_settlement_mm']:.1f} mm"
                )
                
                fig_time.update_xaxes(
                    title="Time (years)",
                    type='log',
                    showgrid=True
                )
                fig_time.update_yaxes(
                    title="Settlement (mm)",
                    showgrid=True
                )
                fig_time.update_layout(
                    title="Settlement vs Time",
                    height=500,
                    hovermode='x unified',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99
                    )
                )
                
                st.plotly_chart(fig_time, use_container_width=True)
                
                # Settlement milestones
                st.subheader("Settlement Milestones")
                
                milestones_time = [0.1, 0.5, 1.0, 5.0, 10.0, 25.0, 50.0]
                milestone_data = []
                
                for t in milestones_time:
                    if t <= max_time:
                        idx = min(range(len(time_curve_data['time_years'])), 
                                 key=lambda i: abs(time_curve_data['time_years'][i] - t))
                        primary_settlement = time_curve_data['settlement_primary_mm'][idx]
                        total_settlement = time_curve_data['settlement_total_mm'][idx]
                        
                        percent_complete = (primary_settlement / 
                                          (time_curve_data['immediate_settlement_mm'] + 
                                           time_curve_data['final_consolidation_mm'])) * 100 if time_curve_data['final_consolidation_mm'] > 0 else 100
                        
                        milestone_data.append({
                            'Time (years)': t,
                            'Primary (mm)': round(primary_settlement, 2),
                            'Total (mm)': round(total_settlement, 2),
                            '% Complete': round(percent_complete, 1)
                        })
                
                milestone_df = pd.DataFrame(milestone_data)
                st.dataframe(milestone_df, hide_index=True, use_container_width=True)
                
                # Consolidation time analysis
                st.subheader("Consolidation Time by Layer")
                
                col_time_a, col_time_b = st.columns(2)
                
                with col_time_a:
                    target_degree = st.slider(
                        "Target Degree of Consolidation",
                        min_value=50,
                        max_value=99,
                        value=90,
                        step=5,
                        help="Percentage of consolidation to calculate time for"
                    ) / 100.0
                
                with col_time_b:
                    if st.button("Calculate Layer Times", key="layer_time_btn"):
                        # Get stored calculator and params
                        calculator_stored = st.session_state.get('settlement_calculator', SettlementCalculator())
                        cpt_name_stored = settlement_params_stored.get('cpt_name', selected_cpt_settle)
                        params_stored = st.session_state.processed_cpts[cpt_name_stored]['parameters']
                        
                        layer_times = calculator_stored.calculate_consolidation_time(
                            params_stored,
                            target_degree=target_degree
                        )
                        st.session_state['layer_times'] = layer_times
                
                if 'layer_times' in st.session_state:
                    layer_times = st.session_state['layer_times']
                    layer_times_df = pd.DataFrame(layer_times['layer_times'])
                    
                    if len(layer_times_df) > 0:
                        display_cols = ['layer_number', 'soil_type', 'thickness_m', 'time_days', 'time_years']
                        available_cols = [col for col in display_cols if col in layer_times_df.columns]
                        
                        if available_cols:
                            layer_times_display = layer_times_df[available_cols].copy()
                            layer_times_display.columns = ['Layer', 'Soil Type', 'Thickness (m)', 'Time (days)', 'Time (years)']
                            st.dataframe(layer_times_display.round(2), hide_index=True, use_container_width=True)
                        else:
                            st.dataframe(layer_times_df, hide_index=True, use_container_width=True)
                        
                        st.info(f"💡 Time required for {int(target_degree*100)}% consolidation varies by layer based on drainage properties and permeability.")
            
            st.markdown("---")
            
            st.subheader("Export Settlement Results")
            exporter = ExportManager()
            load_config = {
                'load': settlement_params_stored.get('load', load_kN),
                'width': settlement_params_stored.get('width', footing_width),
                'length': settlement_params_stored.get('length', footing_length),
                'depth': settlement_params_stored.get('depth', footing_depth)
            }
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                excel_settle = exporter.export_settlement_results(
                    settlement_results,
                    params,
                    load_config
                )
                st.download_button(
                    label="📥 Download Settlement Results (Excel)",
                    data=excel_settle,
                    file_name=f"{selected_cpt_settle}_settlement.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            with col_export2:
                pdf_report = exporter.generate_pdf_report(
                    selected_cpt_settle,
                    st.session_state.processed_cpts[selected_cpt_settle]['summary'],
                    st.session_state.processed_cpts[selected_cpt_settle]['layers'],
                    params,
                    settlement_results,
                    load_config
                )
                st.download_button(
                    label="📄 Download Full Report (PDF)",
                    data=pdf_report,
                    file_name=f"{selected_cpt_settle}_report.pdf",
                    mime="application/pdf"
                )

with tab7:
    st.header("3D Spatial Visualization")
    
    if not st.session_state.processed_cpts:
        st.info("📌 Please upload CPT data files in the 'Upload CPT Data' tab first.")
    elif len(st.session_state.processed_cpts) < 2:
        st.warning("⚠️ 3D visualization requires at least 2 CPT datasets. Please upload more CPT files.")
    else:
        st.markdown("""
        Visualize multiple CPT locations in 3D space to understand spatial soil variations.
        Set the X and Y coordinates for each CPT location below.
        """)
        
        st.subheader("📍 CPT Location Setup")
        
        with st.expander("Set CPT Coordinates", expanded=True):
            coord_cols = st.columns(min(3, len(st.session_state.processed_cpts)))
            
            for idx, cpt_name in enumerate(st.session_state.processed_cpts.keys()):
                col = coord_cols[idx % len(coord_cols)]
                
                with col:
                    st.markdown(f"**{cpt_name}**")
                    
                    if cpt_name not in st.session_state.cpt_coordinates:
                        st.session_state.cpt_coordinates[cpt_name] = {'x': idx * 10.0, 'y': 0.0}
                    
                    x_coord = st.number_input(
                        f"X (m)",
                        key=f"x_{cpt_name}",
                        value=st.session_state.cpt_coordinates[cpt_name]['x'],
                        step=1.0
                    )
                    y_coord = st.number_input(
                        f"Y (m)",
                        key=f"y_{cpt_name}",
                        value=st.session_state.cpt_coordinates[cpt_name]['y'],
                        step=1.0
                    )
                    
                    st.session_state.cpt_coordinates[cpt_name] = {'x': x_coord, 'y': y_coord}
        
        st.markdown("---")
        
        viz_type = st.selectbox(
            "Select Visualization Type",
            [
                "3D Soil Profile Scatter",
                "3D Layer Surface Interpolation",
                "2D Cross-Section",
                "Plan View at Depth"
            ]
        )
        
        visualizer = CPT3DVisualizer()
        
        cpt_locations = {}
        for cpt_name, cpt_info in st.session_state.processed_cpts.items():
            coords = st.session_state.cpt_coordinates.get(cpt_name, {'x': 0, 'y': 0})
            cpt_locations[cpt_name] = {
                'x': coords['x'],
                'y': coords['y'],
                'data': cpt_info['data'],
                'layers': cpt_info['layers'].to_dict('records') if hasattr(cpt_info['layers'], 'to_dict') else cpt_info['layers']
            }
        
        if viz_type == "3D Soil Profile Scatter":
            st.subheader("3D Soil Profile Scatter Plot")
            st.markdown("Each CPT location is shown as a vertical scatter of soil types colored by classification.")
            
            try:
                fig = visualizer.create_3d_soil_profile(cpt_locations)
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 Tip: Use your mouse to rotate, zoom, and pan the 3D view.")
            except Exception as e:
                st.error(f"Error creating 3D visualization: {str(e)}")
        
        elif viz_type == "3D Layer Surface Interpolation":
            st.subheader("3D Layer Surface Interpolation")
            st.markdown("Interpolated surfaces showing how soil layers vary across space.")
            
            if len(cpt_locations) >= 3:
                try:
                    fig = visualizer.create_layer_surfaces(cpt_locations)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("💡 Tip: Surface interpolation requires at least 3 CPT locations for accurate results.")
                except Exception as e:
                    st.error(f"Error creating surface visualization: {str(e)}")
            else:
                st.warning("⚠️ Surface interpolation requires at least 3 CPT locations. Currently showing vertical columns instead.")
                try:
                    fig = visualizer.create_layer_surfaces(cpt_locations)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating visualization: {str(e)}")
        
        elif viz_type == "2D Cross-Section":
            st.subheader("2D Cross-Section View")
            st.markdown("View a vertical slice through the soil profile between two points.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Start Point**")
                start_x = st.number_input("Start X (m)", value=0.0, step=1.0, key="cross_start_x")
                start_y = st.number_input("Start Y (m)", value=0.0, step=1.0, key="cross_start_y")
            
            with col2:
                st.markdown("**End Point**")
                end_x = st.number_input("End X (m)", value=20.0, step=1.0, key="cross_end_x")
                end_y = st.number_input("End Y (m)", value=0.0, step=1.0, key="cross_end_y")
            
            try:
                fig = visualizer.create_cross_section(
                    cpt_locations,
                    (start_x, start_y),
                    (end_x, end_y)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 Tip: CPT locations within 1m of the cross-section line are marked with triangles.")
            except Exception as e:
                st.error(f"Error creating cross-section: {str(e)}")
        
        elif viz_type == "Plan View at Depth":
            st.subheader("Plan View at Specific Depth")
            st.markdown("Top-down view showing how soil types vary horizontally at a given depth.")
            
            max_depth = max([cpt_info['data']['depth'].max() for cpt_info in st.session_state.processed_cpts.values()])
            depth_slice = st.slider(
                "Select Depth (m)",
                min_value=0.0,
                max_value=float(max_depth),
                value=5.0,
                step=0.5,
                key="plan_depth"
            )
            
            try:
                fig = visualizer.create_plan_view(cpt_locations, depth_slice)
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 Tip: Use the slider to explore soil variations at different depths.")
            except Exception as e:
                st.error(f"Error creating plan view: {str(e)}")
        
        st.markdown("---")
        st.subheader("📊 Spatial Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Number of CPTs", len(cpt_locations))
        with col2:
            x_coords = [loc['x'] for loc in cpt_locations.values()]
            y_coords = [loc['y'] for loc in cpt_locations.values()]
            area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
            st.metric("Survey Area", f"{area:.1f} m²")
        with col3:
            avg_depth = np.mean([cpt_info['data']['depth'].max() for cpt_info in st.session_state.processed_cpts.values()])
            st.metric("Average CPT Depth", f"{avg_depth:.1f} m")

st.sidebar.markdown("---")
st.sidebar.markdown("**📚 Based on:**")
st.sidebar.markdown("- Robertson (2009) CPT Classification")
st.sidebar.markdown("- Settle3 Correlations")
st.sidebar.markdown("- Terzaghi Consolidation Theory")
