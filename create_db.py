import sqlite3 
from datetime import datetime
import json

def create_database():
    """Create the DemicsTech surveillance database with all necessary tables"""
    conn = sqlite3.connect('demicstech.db')
    cursor = conn.cursor()
    
    # Hospitals/Data Sources Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hospitals (
        hospital_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_name TEXT NOT NULL,
        location TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        contact_email TEXT,
        api_endpoint TEXT,
        last_sync TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Patients Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_id INTEGER,
        external_patient_id TEXT,
        age INTEGER,
        gender TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
        UNIQUE(hospital_id, external_patient_id)
    )
    ''')
    
    # Disease Test Results Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        hospital_id INTEGER,
        disease_type TEXT NOT NULL,
        test_result TEXT NOT NULL,
        test_date DATE NOT NULL,
        severity TEXT,
        symptoms TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
    )
    ''')
    
    # Hotspot Analysis Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hotspot_analysis (
        analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_type TEXT NOT NULL,
        analysis_date DATE NOT NULL,
        location TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        case_count INTEGER,
        risk_level TEXT,
        analysis_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Daily Summary Statistics Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_statistics (
        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_type TEXT NOT NULL,
        stat_date DATE NOT NULL,
        total_cases INTEGER,
        positive_cases INTEGER,
        negative_cases INTEGER,
        locations_affected INTEGER,
        summary_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(disease_type, stat_date)
    )
    ''')
    
    # Outbreak Alerts Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS outbreak_alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_type TEXT NOT NULL,
        alert_date DATE NOT NULL,
        location TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        severity TEXT,
        case_count INTEGER,
        alert_message TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_test_date ON test_results(test_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_disease_type ON test_results(disease_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_hospital ON patients(hospital_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_date ON outbreak_alerts(alert_date)')
    
    conn.commit()
    
    # Optional test hospital
    cursor.execute('''
    INSERT OR IGNORE INTO hospitals (hospital_name, location, latitude, longitude, contact_email)
    VALUES (?, ?, ?, ?, ?)
    ''', ('National Hospital Abuja', 'Central District, Abuja', 9.0579, 7.4951, 'contact@nationalhospital.ng'))
    
    conn.commit()
    conn.close()
    
    print("✅ Database created successfully!")
    print("📊 Tables created:")
    print("   - hospitals")
    print("   - patients")
    print("   - test_results")
    print("   - hotspot_analysis")
    print("   - daily_statistics")
    print("   - outbreak_alerts")

def view_database_stats():
    """View current database statistics"""
    conn = sqlite3.connect('demicstech.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n📈 Database Statistics:")
    print("-" * 50)
    
    tables = ['hospitals', 'patients', 'test_results', 'hotspot_analysis', 'daily_statistics', 'outbreak_alerts']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
        count = cursor.fetchone()['count']
        print(f"{table.capitalize()}: {count} records")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    view_database_stats()
