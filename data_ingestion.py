import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

class DataIngestion:
    def __init__(self, db_path='demicstech.db'):
        self.db_path = db_path
        self.geolocator = Nominatim(user_agent="demicstech_surveillance")
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def geocode_address(self, address: str) -> tuple:
        """Convert address to latitude and longitude"""
        try:
            location = self.geolocator.geocode(address + ", Nigeria", timeout=10)
            if location:
                return location.latitude, location.longitude
            return None, None
        except GeocoderTimedOut:
            return None, None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None, None
    
    def add_hospital(self, hospital_data: Dict) -> int:
        """Add a new hospital to the system"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Geocode hospital location if coordinates not provided
        lat, lon = hospital_data.get('latitude'), hospital_data.get('longitude')
        if not lat or not lon:
            lat, lon = self.geocode_address(hospital_data['location'])
        
        cursor.execute('''
        INSERT INTO hospitals (hospital_name, location, latitude, longitude, contact_email, api_endpoint)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            hospital_data['hospital_name'],
            hospital_data['location'],
            lat,
            lon,
            hospital_data.get('contact_email'),
            hospital_data.get('api_endpoint')
        ))
        
        hospital_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return hospital_id
    
    def add_patient(self, patient_data: Dict) -> int:
        """Add or update patient information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Geocode patient address
        lat, lon = patient_data.get('latitude'), patient_data.get('longitude')
        if not lat or not lon:
            lat, lon = self.geocode_address(patient_data['address'])
        
        # Check if patient already exists
        cursor.execute('''
        SELECT patient_id FROM patients 
        WHERE hospital_id = ? AND external_patient_id = ?
        ''', (patient_data['hospital_id'], patient_data['external_patient_id']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing patient
            cursor.execute('''
            UPDATE patients 
            SET age = ?, gender = ?, address = ?, latitude = ?, longitude = ?, phone = ?
            WHERE patient_id = ?
            ''', (
                patient_data.get('age'),
                patient_data.get('gender'),
                patient_data['address'],
                lat, lon,
                patient_data.get('phone'),
                existing['patient_id']
            ))
            patient_id = existing['patient_id']
        else:
            # Insert new patient
            cursor.execute('''
            INSERT INTO patients (hospital_id, external_patient_id, age, gender, address, latitude, longitude, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_data['hospital_id'],
                patient_data['external_patient_id'],
                patient_data.get('age'),
                patient_data.get('gender'),
                patient_data['address'],
                lat, lon,
                patient_data.get('phone')
            ))
            patient_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return patient_id
    
    def add_test_result(self, test_data: Dict) -> int:
        """Add a disease test result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # First, ensure patient exists
        patient_id = self.add_patient(test_data['patient_data'])
        
        # Add test result
        cursor.execute('''
        INSERT INTO test_results (patient_id, hospital_id, disease_type, test_result, test_date, severity, symptoms, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_id,
            test_data['hospital_id'],
            test_data['disease_type'],
            test_data['test_result'],
            test_data['test_date'],
            test_data.get('severity'),
            test_data.get('symptoms'),
            test_data.get('notes')
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def bulk_add_test_results(self, test_results: List[Dict]) -> int:
        """Add multiple test results at once"""
        count = 0
        for test_data in test_results:
            try:
                self.add_test_result(test_data)
                count += 1
            except Exception as e:
                print(f"Error adding test result: {e}")
                continue
        
        return count
    
    def fetch_from_hospital_api(self, hospital_id: int, disease_type: str, start_date: str, end_date: str):
        """
        Fetch data from hospital API endpoint
        This is a template - implement based on actual hospital API structure
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT api_endpoint FROM hospitals WHERE hospital_id = ?', (hospital_id,))
        hospital = cursor.fetchone()
        conn.close()
        
        if not hospital or not hospital['api_endpoint']:
            raise ValueError("Hospital API endpoint not configured")
        
        # TODO: Implement actual API fetching logic based on hospital's API structure
        # This would use requests library to fetch data
        # For now, returning a placeholder
        
        return {
            'status': 'success',
            'message': 'API fetching not yet implemented. Use manual data entry.',
            'hospital_id': hospital_id
        }
    
    def get_monthly_cases(self, disease_type: str, month: int, year: int) -> List[Dict]:
        """Get all cases for a specific disease in a given month"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            tr.result_id,
            tr.disease_type,
            tr.test_result,
            tr.test_date,
            tr.severity,
            p.age,
            p.gender,
            p.address,
            p.latitude,
            p.longitude,
            h.hospital_name
        FROM test_results tr
        JOIN patients p ON tr.patient_id = p.patient_id
        JOIN hospitals h ON tr.hospital_id = h.hospital_id
        WHERE tr.disease_type = ?
        AND strftime('%m', tr.test_date) = ?
        AND strftime('%Y', tr.test_date) = ?
        ORDER BY tr.test_date
        ''', (disease_type, f'{month:02d}', str(year)))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results


# Example usage functions
def example_add_malaria_case():
    """Example: Add a malaria test result"""
    ingestion = DataIngestion()
    
    test_data = {
        'hospital_id': 1,
        'disease_type': 'Malaria',
        'test_result': 'Positive',
        'test_date': '2024-11-15',
        'severity': 'Moderate',
        'symptoms': 'Fever, headache, chills',
        'patient_data': {
            'hospital_id': 1,
            'external_patient_id': 'PT001',
            'age': 28,
            'gender': 'Female',
            'address': 'Wuse 2, Abuja',
            'phone': '+234803000000'
        }
    }
    
    result_id = ingestion.add_test_result(test_data)
    print(f"✅ Test result added with ID: {result_id}")


if __name__ == "__main__":
    # Test the ingestion system
    example_add_malaria_case()
    
    # Retrieve November cases
    ingestion = DataIngestion()
    cases = ingestion.get_monthly_cases('Malaria', 11, 2024)
    print(f"\n📊 Found {len(cases)} Malaria cases in November 2024")