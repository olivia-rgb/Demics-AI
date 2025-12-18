import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
import plotly.express as px
import plotly.graph_objects as go

# Configuration
API_URL = "https://demics-ai-5.onrender.com"  # Change to your deployed API URL

st.set_page_config(
    page_title="DemicsTech - Disease Surveillance",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Refined Custom CSS with clean blue theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Alan+Sans:wght@300;400;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #1565C0;
    }
    
    /* Main container */
    .main {
        background: #f5f7fa;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #1565C0;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.1);
        margin: 15px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-left: 4px solid #1565C0;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 16px rgba(21, 101, 192, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1565C0;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    
    .metric-delta {
        font-size: 0.85rem;
        color: #1565C0;
        font-weight: 600;
    }
    
    /* Alert cards */
    .alert-critical {
        background: #d32f2f;
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(211, 47, 47, 0.3);
    }
    
    .alert-high {
        background: #f57c00;
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(245, 124, 0, 0.3);
    }
    
    .alert-normal {
        background: #1565C0;
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
    }
    
    /* Info cards */
    .info-card {
        background: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.1);
        margin: 15px 0;
        border-left: 4px solid #1565C0;
    }
    
    /* Hotspot card */
    .hotspot-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.1);
        margin: 10px 0;
        border-left: 4px solid #d32f2f;
        transition: all 0.3s ease;
    }
    
    .hotspot-card:hover {
        box-shadow: 0 4px 16px rgba(21, 101, 192, 0.2);
        transform: translateX(5px);
    }
    
    /* Form styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 10px;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1565C0;
        box-shadow: 0 0 0 3px rgba(21, 101, 192, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: #1565C0;
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.3);
    }
    
    .stButton > button:hover {
        background: #0d47a1;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(21, 101, 192, 0.4);
    }
    
    /* Header styling */
    .main-header {
        background: white;
        padding: 30px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        color: #1565C0;
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        color: #666;
        font-size: 1.1rem;
    }
    
    /* Data table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.1);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px;
    }
    
    .badge-critical { background: #d32f2f; color: white; }
    .badge-high { background: #f57c00; color: white; }
    .badge-moderate { background: #ffa726; color: white; }
    .badge-low { background: #1565C0; color: white; }
    
    /* Loading spinner */
    .stSpinner > div {
        border-color: #1565C0 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #e3f2fd;
        border-left: 4px solid #1565C0;
        border-radius: 8px;
    }
    
    .stError {
        background-color: #ffebee;
        border-left: 4px solid #d32f2f;
        border-radius: 8px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Custom subheader styling */
    .info-card h2, .info-card h3 {
        color: #1565C0;
        margin-top: 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("""
<div style='text-align: center; padding: 20px;'>
    <h1 style='color: white; margin: 0;'>🏥</h1>
    <h2 style='color: white; margin: 10px 0;'>DemicsTech</h2>
    <p style='color: rgba(255,255,255,0.9); font-size: 0.9rem;'>Disease Surveillance & Outbreak Detection</p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.selectbox(
    "📍 Navigate",
    ["🏠 Dashboard", "➕ Add Test Result", "🏥 Add Hospital", "📋 View Cases", "🔥 Hotspot Analysis", "⚠️ Outbreak Detection"]
)

disease_type = st.sidebar.selectbox(
    "🦠 Select Disease",
    ["Malaria", "Ebola", "Tuberculosis", "COVID-19", "Typhoid", "Cholera", "Other"]
)

if disease_type == "Other":
    disease_type = st.sidebar.text_input("Enter disease name")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; padding: 10px;'>
    <p style='font-size: 0.8rem; color: rgba(255,255,255,0.8);'>Version 1.0</p>
    <p style='font-size: 0.75rem; color: rgba(255,255,255,0.7);'>Real-time Disease Monitoring</p>
</div>
""", unsafe_allow_html=True)


def create_metric_card(label, value, delta=None, icon="📊"):
    """Create a clean metric card"""
    delta_html = f"<div class='metric-delta'>↑ {delta}</div>" if delta else ""
    
    return f"""
    <div class='metric-card'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <div>
                <div class='metric-label'>{icon} {label}</div>
                <div class='metric-value'>{value}</div>
                {delta_html}
            </div>
        </div>
    </div>
    """


def show_dashboard():
    """Clean dashboard with refined visualizations"""
    st.markdown(f"""
    <div class='main-header'>
        <h1>📊 {disease_type} Surveillance Dashboard</h1>
        <p>Real-time monitoring and outbreak detection system</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        with st.spinner("Loading dashboard data..."):
            response = requests.get(f"{API_URL}/api/dashboard", params={"disease_type": disease_type})
        
        if response.status_code == 200:
            data = response.json()['dashboard']
            
            daily = data.get('daily_statistics', {})
            monthly = data.get('monthly_statistics', {})
            outbreak = data.get('outbreak_status', {})
            
            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    create_metric_card("Total Tests Today", daily.get('total_tests', 0), icon="🧪"),
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    create_metric_card("Positive Cases", daily.get('positive_cases', 0), icon="🔴"),
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    create_metric_card("Monthly Total", monthly.get('total_positive', 0), icon="📈"),
                    unsafe_allow_html=True
                )
            
            with col4:
                alert_level = outbreak.get('alert_level', 'Normal')
                icon = "🚨" if alert_level == "High" else "✅"
                st.markdown(
                    create_metric_card("Outbreak Status", alert_level, icon=icon),
                    unsafe_allow_html=True
                )
            
            # Outbreak Alert
            if outbreak.get('is_outbreak'):
                st.markdown(f"""
                <div class="alert-critical">
                    <h3 style='margin: 0; color: white;'>🚨 OUTBREAK ALERT</h3>
                    <p style='margin: 10px 0 0 0; font-size: 1.1rem;'>
                        {disease_type} cases have increased by <strong>{outbreak.get('increase_factor', 0)}x</strong> in the last 7 days.
                    </p>
                    <p style='margin: 5px 0 0 0;'>
                        Current cases: <strong>{outbreak.get('recent_cases', 0)}</strong>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-normal">
                    <h3 style='margin: 0; color: white;'>✅ Normal Status</h3>
                    <p style='margin: 10px 0 0 0;'>No outbreak detected. Situation is under control.</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("<div class='info-card'>", unsafe_allow_html=True)
                st.subheader("📈 Monthly Trend")
                
                if monthly.get('daily_breakdown'):
                    df = pd.DataFrame(monthly['daily_breakdown'])
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['test_date'],
                        y=df['positive_cases'],
                        mode='lines+markers',
                        name='Positive Cases',
                        line=dict(color='#1565C0', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(21, 101, 192, 0.1)'
                    ))
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=0, r=0, t=0, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for monthly trend")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("<div class='info-card'>", unsafe_allow_html=True)
                st.subheader("📍 Cases by Location")
                
                if daily.get('locations'):
                    loc_df = pd.DataFrame(daily['locations'])
                    
                    fig = px.bar(
                        loc_df.head(5),
                        x='positive_count',
                        y='address',
                        orientation='h',
                        color='positive_count',
                        color_continuous_scale=['#e3f2fd', '#1565C0']
                    )
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=0, r=0, t=0, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Hotspots section
            st.markdown("<div class='info-card'>", unsafe_allow_html=True)
            st.subheader("🔥 Active Hotspots")
            
            hotspots = data.get('hotspots', [])
            
            if hotspots:
                for i, hotspot in enumerate(hotspots, 1):
                    risk_color = {
                        'Critical': '🔴',
                        'High': '🟠',
                        'Moderate': '🟡'
                    }.get(hotspot['risk_level'], '🟢')
                    
                    st.markdown(f"""
                    <div class='hotspot-card'>
                        <h4 style='margin: 0; color: #1565C0;'>
                            {risk_color} Hotspot {i}: {hotspot['location']}
                        </h4>
                        <div style='margin-top: 10px; display: flex; gap: 20px;'>
                            <span><strong>Cases:</strong> {hotspot['case_count']}</span>
                            <span><strong>Risk Level:</strong> <span class='badge badge-{hotspot["risk_level"].lower()}'>{hotspot['risk_level']}</span></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("✅ No hotspots detected in the current period.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            st.error("⚠️ Unable to fetch dashboard data. Make sure the API server is running.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Make sure to run: `python api.py` in another terminal")


def add_test_result_form():
    """Form for adding test results"""
    st.markdown("""
    <div class='main-header'>
        <h1>➕ Add New Test Result</h1>
        <p>Submit disease test results to the surveillance system</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Patient Information")
        hospital_id = st.number_input("Hospital ID", min_value=1, value=1)
        patient_id = st.text_input("Patient ID", placeholder="PT001")
        age = st.number_input("Age", min_value=0, max_value=120, value=30)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        address = st.text_input("Address", placeholder="e.g., Wuse 2, Abuja")
        phone = st.text_input("Phone", placeholder="+234...")
    
    with col2:
        st.subheader("🧪 Test Information")
        test_disease = st.text_input("Disease Type", value=disease_type)
        test_result = st.selectbox("Test Result", ["Positive", "Negative", "Pending"])
        test_date = st.date_input("Test Date", value=datetime.now())
        severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe", "Critical"])
        symptoms = st.text_area("Symptoms", placeholder="e.g., Fever, headache, chills")
        notes = st.text_area("Additional Notes")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("✅ Submit Test Result", type="primary"):
        data = {
            "hospital_id": hospital_id,
            "disease_type": test_disease,
            "test_result": test_result,
            "test_date": str(test_date),
            "severity": severity,
            "symptoms": symptoms,
            "notes": notes,
            "patient_data": {
                "hospital_id": hospital_id,
                "external_patient_id": patient_id,
                "age": age,
                "gender": gender,
                "address": address,
                "phone": phone
            }
        }
        
        try:
            with st.spinner("Submitting test result..."):
                response = requests.post(f"{API_URL}/api/test-results", json=data)
            
            if response.status_code == 201:
                st.success("✅ Test result added successfully!")
                st.balloons()
            else:
                st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")


def add_hospital_form():
    """Form for adding hospitals"""
    st.markdown("""
    <div class='main-header'>
        <h1>🏥 Register New Hospital</h1>
        <p>Add a healthcare facility to the surveillance network</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    hospital_name = st.text_input("🏥 Hospital Name", placeholder="e.g., General Hospital Abuja")
    location = st.text_input("📍 Location/Address", placeholder="e.g., Central District, Abuja")
    contact_email = st.text_input("📧 Contact Email", placeholder="contact@hospital.ng")
    api_endpoint = st.text_input("🔗 API Endpoint (optional)", placeholder="https://api.hospital.ng")
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("🌐 Latitude (optional)", format="%.6f")
    with col2:
        longitude = st.number_input("🌐 Longitude (optional)", format="%.6f")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("✅ Register Hospital", type="primary"):
        data = {
            "hospital_name": hospital_name,
            "location": location,
            "contact_email": contact_email,
            "api_endpoint": api_endpoint,
            "latitude": latitude if latitude != 0 else None,
            "longitude": longitude if longitude != 0 else None
        }
        
        try:
            with st.spinner("Registering hospital..."):
                response = requests.post(f"{API_URL}/api/hospitals", json=data)
            
            if response.status_code == 201:
                st.success(f"✅ Hospital registered successfully! ID: {response.json()['hospital_id']}")
                st.balloons()
            else:
                st.error(f"❌ Error: {response.json().get('error')}")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")


def view_cases():
    """Case viewing interface"""
    st.markdown(f"""
    <div class='main-header'>
        <h1>📋 {disease_type} Case Records</h1>
        <p>View and export disease case data</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        month = st.selectbox("📅 Month", range(1, 13), index=datetime.now().month - 1)
    with col2:
        year = st.number_input("📅 Year", min_value=2020, max_value=2030, value=datetime.now().year)
    with col3:
        st.write("")  # Spacing
        load_button = st.button("🔍 Load Cases", type="primary")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if load_button:
        try:
            with st.spinner("Loading cases..."):
                response = requests.get(f"{API_URL}/api/cases", params={
                    "disease_type": disease_type,
                    "month": month,
                    "year": year
                })
            
            if response.status_code == 200:
                cases = response.json()['cases']
                
                if cases:
                    st.success(f"✅ Found {len(cases)} cases")
                    
                    df = pd.DataFrame(cases)
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"{disease_type}_cases_{year}_{month:02d}.csv",
                        "text/csv",
                        key='download-csv'
                    )
                else:
                    st.info("ℹ️ No cases found for this period.")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def hotspot_analysis():
    """Hotspot analysis interface"""
    st.markdown("""
    <div class='main-header'>
        <h1>🔥 Hotspot Analysis</h1>
        <p>Identify disease clustering and high-risk areas</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_back = st.slider("📅 Days to analyze", 7, 90, 30)
    with col2:
        radius_km = st.slider("📏 Cluster radius (km)", 1.0, 20.0, 5.0)
    with col3:
        min_cases = st.slider("🔢 Minimum cases", 2, 10, 3)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🔍 Analyze Hotspots", type="primary"):
        start_date = str(datetime.now().date() - timedelta(days=days_back))
        end_date = str(datetime.now().date())
        
        try:
            with st.spinner("Analyzing hotspots..."):
                response = requests.get(f"{API_URL}/api/hotspots", params={
                    "disease_type": disease_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "radius_km": radius_km,
                    "min_cases": min_cases
                })
            
            if response.status_code == 200:
                hotspots = response.json()['hotspots']
                
                if hotspots:
                    st.success(f"✅ Found {len(hotspots)} hotspots")
                    
                    for i, hotspot in enumerate(hotspots, 1):
                        with st.expander(f"🔥 Hotspot {i}: {hotspot['location']} ({hotspot['case_count']} cases)"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Risk Level", hotspot['risk_level'])
                                st.metric("Case Count", hotspot['case_count'])
                            with col2:
                                st.write(f"**Coordinates:** {hotspot['latitude']:.4f}, {hotspot['longitude']:.4f}")
                                st.write(f"**Cluster Radius:** {hotspot['radius_km']} km")
                else:
                    st.info("✅ No hotspots detected with current parameters.")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


def outbreak_detection():
    """Outbreak detection interface"""
    st.markdown("""
    <div class='main-header'>
        <h1>⚠️ Outbreak Detection</h1>
        <p>Statistical analysis for early outbreak warning</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        days_window = st.slider("📊 Analysis window (days)", 3, 14, 7)
    with col2:
        threshold = st.slider("📈 Threshold multiplier", 1.5, 5.0, 2.0)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🔍 Check for Outbreak", type="primary"):
        try:
            with st.spinner("Analyzing outbreak risk..."):
                response = requests.get(f"{API_URL}/api/outbreak/detect", params={
                    "disease_type": disease_type,
                    "days_window": days_window,
                    "threshold": threshold
                })
            
            if response.status_code == 200:
                result = response.json()['outbreak_analysis']
                
                if result['is_outbreak']:
                    st.markdown(f"""
                    <div class='alert-critical'>
                        <h2 style='margin: 0; color: white;'>🚨 OUTBREAK DETECTED</h2>
                        <div style='margin-top: 20px; font-size: 1.1rem;'>
                            <p><strong>Recent cases ({days_window} days):</strong> {result['recent_cases']}</p>
                            <p><strong>Historical average:</strong> {result['historical_avg']}</p>
                            <p><strong>Increase factor:</strong> {result['increase_factor']}x</p>
                            <p><strong>Alert level:</strong> {result['alert_level']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='alert-normal'>
                        <h2 style='margin: 0; color: white;'>✅ No Outbreak Detected</h2>
                        <div style='margin-top: 20px; font-size: 1.1rem;'>
                            <p><strong>Recent cases ({days_window} days):</strong> {result['recent_cases']}</p>
                            <p><strong>Historical average:</strong> {result['historical_avg']}</p>
                            <p><strong>Status:</strong> Normal - Situation under control</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# Main App Router
if page == "🏠 Dashboard":
    show_dashboard()
elif page == "➕ Add Test Result":
    add_test_result_form()
elif page == "🏥 Add Hospital":
    add_hospital_form()
elif page == "📋 View Cases":
    view_cases()
elif page == "🔥 Hotspot Analysis":
    hotspot_analysis()
elif page == "⚠️ Outbreak Detection":
    outbreak_detection()