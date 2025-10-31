import pandas as pd
import numpy as np

def create_sample_cpt_data():
    """
    Create sample CPT data for testing the application.
    Simulates a typical soil profile with sandy and clayey layers.
    """
    
    np.random.seed(42)
    
    depths = np.arange(0, 20.5, 0.5)
    n_points = len(depths)
    
    qc = np.zeros(n_points)
    fs = np.zeros(n_points)
    u2 = np.zeros(n_points)
    
    for i, depth in enumerate(depths):
        if depth < 3:
            qc[i] = 1500 + np.random.normal(0, 200)
            fs[i] = 20 + np.random.normal(0, 3)
            u2[i] = 50 + depth * 10 + np.random.normal(0, 10)
        
        elif depth < 7:
            qc[i] = 800 + np.random.normal(0, 100)
            fs[i] = 30 + np.random.normal(0, 5)
            u2[i] = 100 + depth * 10 + np.random.normal(0, 15)
        
        elif depth < 12:
            qc[i] = 3000 + np.random.normal(0, 300)
            fs[i] = 40 + np.random.normal(0, 5)
            u2[i] = 150 + depth * 10 + np.random.normal(0, 20)
        
        elif depth < 16:
            qc[i] = 1200 + np.random.normal(0, 150)
            fs[i] = 35 + np.random.normal(0, 5)
            u2[i] = 200 + depth * 10 + np.random.normal(0, 15)
        
        else:
            qc[i] = 5000 + np.random.normal(0, 500)
            fs[i] = 60 + np.random.normal(0, 8)
            u2[i] = 250 + depth * 10 + np.random.normal(0, 25)
    
    qc = np.maximum(qc, 100)
    fs = np.maximum(fs, 5)
    u2 = np.maximum(u2, 0)
    
    df = pd.DataFrame({
        'Depth (m)': depths,
        'Cone Resistance qc (kPa)': qc,
        'Sleeve Friction fs (kPa)': fs,
        'Pore Pressure u2 (kPa)': u2
    })
    
    return df

if __name__ == "__main__":
    df1 = create_sample_cpt_data()
    df1.to_excel('Sample_CPT_01.xlsx', index=False)
    print("Sample CPT data file created: Sample_CPT_01.xlsx")
    
    np.random.seed(123)
    df2 = create_sample_cpt_data()
    df2.to_excel('Sample_CPT_02.xlsx', index=False)
    print("Sample CPT data file created: Sample_CPT_02.xlsx")
