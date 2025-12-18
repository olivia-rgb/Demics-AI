import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

# Configuration
API_URL = "https://demics-ai-5.onrender.com"

st.set_page_config(
    page_title="DemicsTech - Disease Surveillance System",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-critical {
        background-color: #ff4b4b;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .alert-high {
        background-color: #ffa500;
        color: white;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🏥 DemicsTech")
st.sidebar.markdown("### Disease Surveillance System")

page = st.sidebar.selectbox(
    "Navigate",
    ["Dashboard", "Add Test Result", "Add Hospital", "View Cases", "Hotspot Analysis", "Outbreak Detection"]
)

disease_type = st.sidebar.selectbox(
    "Select Disease",
    ["Malaria", "Ebola", "Tuberculosis", "COVID-19", "Typhoid", "Cholera", "Other"]
)

if disease_type == "Other":
    disease_type = st.sidebar.text_input("Enter disease name")


def add_test_result_form():
    st.header("➕ Add New Test Result")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        hospital_id = st.number_input("Hospital ID", min_value=1, value=1)
        patient_id = st.text_input("Patient ID", placeholder="PT001")
        age = st.number_input("Age", min_value=0, max_value=120, value=30)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        address = st.text_input("Address", placeholder="e.g., Wuse 2, Abuja")
        phone = st.text_input("Phone", placeholder="+234...")
    
    with col2:
        st.subheader("Test Information")
        test_disease = st.text_input("Disease Type", value=disease_type)
        test_result = st.selectbox("Test Result", ["Positive", "Negative", "Pending"])
        test_date = st.date_input("Test Date", value=datetime.now())
        severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe", "Critical"])
        symptoms = st.text_area("Symptoms", placeholder="e.g., Fever, headache, chills")
        notes = st.text_area("Additional Notes")
    
    if st.button("Submit Test Result", type="primary"):
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
            response = requests.post(f"{API_URL}/api/test-results", json=data)
            if response.status_code == 201:
                st.success("✅ Test result added successfully!")
            else:
                st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")


def show_dashboard():
    st.header(f"📊 {disease_type} Surveillance Dashboard")
    
    try:
        response = requests.get(f"{API_URL}/api/dashboard", params={"disease_type": disease_type})
        
        if response.status_code == 200:
            data = response.json()['dashboard']
            
            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            daily = data.get('daily_statistics', {})
            monthly = data.get('monthly_statistics', {})
            outbreak = data.get('outbreak_status', {})
            
            with col1:
                st.metric("Total Cases Today", daily.get('total_tests', 0))
            with col2:
                st.metric("Positive Cases Today", daily.get('positive_cases', 0))
            with col3:
                st.metric("Monthly Total", monthly.get('total_positive', 0))
            with col4:
                alert_level = outbreak.get('alert_level', 'Normal')
                color = "🔴" if alert_level == "High" else "🟢"
                st.metric("Outbreak Status", f"{color} {alert_level}")
            
            # Outbreak Alert
            if outbreak.get('is_outbreak'):
                st.markdown(f"""
                <div class="alert-critical">
                    ⚠️ <b>OUTBREAK ALERT:</b> {disease_type} cases have increased by 
                    {outbreak.get('increase_factor', 0)}x in the last 7 days. 
                    Current cases: {outbreak.get('recent_cases', 0)}
                </div>
                """, unsafe_allow_html=True)
            
            # Monthly Trend
            st.subheader("📈 Monthly Trend")
            if monthly.get('daily_breakdown'):
                df = pd.DataFrame(monthly['daily_breakdown'])
                st.line_chart(df.set_index('test_date')['positive_cases'])
            
            # Hotspots
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
                    **{risk_color} Hotspot {i}:** {hotspot['location']}  
                    Cases: {hotspot['case_count']} | Risk Level: {hotspot['risk_level']}
                    """)
            else:
                st.info("No hotspots detected in the current period.")
            
            # Location Breakdown
            st.subheader("📍 Cases by Location")
            if daily.get('locations'):
                loc_df = pd.DataFrame(daily['locations'])
                st.dataframe(loc_df, use_container_width=True)
        
        else:
            st.error("Unable to fetch dashboard data. Make sure the API server is running.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Make sure to run: `python api.py` in another terminal")


def view_cases():
    st.header(f"📋 {disease_type} Cases")
    
    col1, col2 = st.columns(2)
    with col1:
        month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1)
    with col2:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
    
    if st.button("Load Cases"):
        try:
            response = requests.get(f"{API_URL}/api/cases", params={
                "disease_type": disease_type,
                "month": month,
                "year": year
            })
            
            if response.status_code == 200:
                cases = response.json()['cases']
                
                if cases:
                    st.success(f"Found {len(cases)} cases")
                    df = pd.DataFrame(cases)
                    st.dataframe(df, use_container_width=True)
                    
                    # Download option
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"{disease_type}_cases_{year}_{month:02d}.csv",
                        "text/csv"
                    )
                else:
                    st.info("No cases found for this period.")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")


def add_hospital_form():
    st.header("🏥 Add New Hospital")
    
    hospital_name = st.text_input("Hospital Name")
    location = st.text_input("Location/Address")
    contact_email = st.text_input("Contact Email")
    api_endpoint = st.text_input("API Endpoint (optional)")
    
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.number_input("Latitude (optional)", format="%.6f")
    with col2:
        longitude = st.number_input("Longitude (optional)", format="%.6f")
    
    if st.button("Add Hospital", type="primary"):
        data = {
            "hospital_name": hospital_name,
            "location": location,
            "contact_email": contact_email,
            "api_endpoint": api_endpoint,
            "latitude": latitude if latitude != 0 else None,
            "longitude": longitude if longitude != 0 else None
        }
        
        try:
            response = requests.post(f"{API_URL}/api/hospitals", json=data)
            if response.status_code == 201:
                st.success(f"✅ Hospital added! ID: {response.json()['hospital_id']}")
            else:
                st.error(f"Error: {response.json().get('error')}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")


def hotspot_analysis():
    st.header("🔥 Hotspot Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_back = st.slider("Days to analyze", 7, 90, 30)
    with col2:
        radius_km = st.slider("Cluster radius (km)", 1.0, 20.0, 5.0)
    with col3:
        min_cases = st.slider("Minimum cases", 2, 10, 3)
    
    if st.button("Analyze Hotspots"):
        start_date = str(datetime.now().date() - timedelta(days=days_back))
        end_date = str(datetime.now().date())
        
        try:
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
                    st.success(f"Found {len(hotspots)} hotspots")
                    
                    for i, hotspot in enumerate(hotspots, 1):
                        with st.expander(f"Hotspot {i}: {hotspot['location']} ({hotspot['case_count']} cases)"):
                            st.write(f"**Risk Level:** {hotspot['risk_level']}")
                            st.write(f"**Coordinates:** {hotspot['latitude']:.4f}, {hotspot['longitude']:.4f}")
                            st.write(f"**Cases in cluster:** {hotspot['case_count']}")
                else:
                    st.info("No hotspots detected with current parameters.")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")


def outbreak_detection():
    st.header("⚠️ Outbreak Detection")
    
    col1, col2 = st.columns(2)
    with col1:
        days_window = st.slider("Analysis window (days)", 3, 14, 7)
    with col2:
        threshold = st.slider("Threshold multiplier", 1.5, 5.0, 2.0)
    
    if st.button("Check for Outbreak"):
        try:
            response = requests.get(f"{API_URL}/api/outbreak/detect", params={
                "disease_type": disease_type,
                "days_window": days_window,
                "threshold": threshold
            })
            
            if response.status_code == 200:
                result = response.json()['outbreak_analysis']
                
                if result['is_outbreak']:
                    st.error(f"""
                    🚨 **OUTBREAK DETECTED**
                    
                    - Recent cases ({days_window} days): {result['recent_cases']}
                    - Historical average: {result['historical_avg']}
                    - Increase factor: {result['increase_factor']}x
                    - Alert level: {result['alert_level']}
                    """)
                else:
                    st.success(f"""
                    ✅ **No Outbreak Detected**
                    
                    - Recent cases ({days_window} days): {result['recent_cases']}
                    - Historical average: {result['historical_avg']}
                    - Status: Normal
                    """)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")


# Main App Router
if page == "Dashboard":
    show_dashboard()
elif page == "Add Test Result":
    add_test_result_form()
elif page == "Add Hospital":
    add_hospital_form()
elif page == "View Cases":
    view_cases()
elif page == "Hotspot Analysis":
    hotspot_analysis()
elif page == "Outbreak Detection":
    outbreak_detection()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**DemicsTech v1.0**")
st.sidebar.markdown("Disease Surveillance & Outbreak Detection")