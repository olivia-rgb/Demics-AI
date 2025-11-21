from data_ingestion import DataIngestion
from datetime import datetime, timedelta
import random

ingestion = DataIngestion()

# Sample locations in Abuja
locations = [
    "Wuse 2, Abuja",
    "Garki, Abuja",
    "Maitama, Abuja",
    "Asokoro, Abuja",
    "Gwarinpa, Abuja",
    "Kubwa, Abuja",
    "Karu, Abuja"
]

diseases = ["Malaria", "Typhoid", "Tuberculosis"]

print("Adding sample test results...")

# Add 50 sample cases
for i in range(50):
    test_date = datetime.now().date() - timedelta(days=random.randint(0, 30))
    
    test_data = {
        'hospital_id': 1,
        'disease_type': random.choice(diseases),
        'test_result': random.choice(['Positive', 'Positive', 'Negative']),
        'test_date': str(test_date),
        'severity': random.choice(['Mild', 'Moderate', 'Severe']),
        'symptoms': 'Fever, headache',
        'patient_data': {
            'hospital_id': 1,
            'external_patient_id': f'PT{i+1:03d}',
            'age': random.randint(1, 80),
            'gender': random.choice(['Male', 'Female']),
            'address': random.choice(locations),
            'phone': f'+23480{random.randint(10000000, 99999999)}'
        }
    }
    
    ingestion.add_test_result(test_data)
    print(f"Added case {i+1}/50")

print("✅ Sample data added successfully!")