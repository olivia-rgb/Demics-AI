import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
import json
import math
import numpy as np

class DiseaseAnalyzer:
    def __init__(self, db_path='demicstech.db'):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _convert_to_native_types(self, obj):
        """Convert numpy/pandas types to native Python types for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self._convert_to_native_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula"""
        if None in [lat1, lon1, lat2, lon2]:
            return float('inf')
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def generate_daily_statistics(self, disease_type: str, date: str) -> Dict:
        """Generate daily statistics for a specific disease"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            COUNT(*) as total_tests,
            SUM(CASE WHEN test_result = 'Positive' THEN 1 ELSE 0 END) as positive_cases,
            SUM(CASE WHEN test_result = 'Negative' THEN 1 ELSE 0 END) as negative_cases,
            COUNT(DISTINCT p.latitude || ',' || p.longitude) as unique_locations
        FROM test_results tr
        JOIN patients p ON tr.patient_id = p.patient_id
        WHERE tr.disease_type = ? AND tr.test_date = ?
        ''', (disease_type, date))
        
        stats = dict(cursor.fetchone())
        
        # Get location breakdown
        cursor.execute('''
        SELECT 
            p.address,
            COUNT(*) as case_count,
            SUM(CASE WHEN tr.test_result = 'Positive' THEN 1 ELSE 0 END) as positive_count
        FROM test_results tr
        JOIN patients p ON tr.patient_id = p.patient_id
        WHERE tr.disease_type = ? AND tr.test_date = ?
        GROUP BY p.address
        ORDER BY positive_count DESC
        ''', (disease_type, date))
        
        locations = [dict(row) for row in cursor.fetchall()]
        
        stats['locations'] = locations
        stats['date'] = date
        stats['disease_type'] = disease_type
        
        # Save to database
        cursor.execute('''
        INSERT OR REPLACE INTO daily_statistics 
        (disease_type, stat_date, total_cases, positive_cases, negative_cases, locations_affected, summary_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            disease_type,
            date,
            stats['total_tests'],
            stats['positive_cases'],
            stats['negative_cases'],
            stats['unique_locations'],
            json.dumps({'locations': locations})
        ))
        
        conn.commit()
        conn.close()
        
        # Convert to native types before returning
        return self._convert_to_native_types(stats)
    
    def generate_monthly_statistics(self, disease_type: str, month: int, year: int) -> Dict:
        """Generate monthly statistics summary"""
        conn = self.get_connection()
        
        query = f'''
        SELECT 
            tr.test_date,
            COUNT(*) as total_tests,
            SUM(CASE WHEN tr.test_result = 'Positive' THEN 1 ELSE 0 END) as positive_cases,
            SUM(CASE WHEN tr.test_result = 'Negative' THEN 1 ELSE 0 END) as negative_cases
        FROM test_results tr
        WHERE tr.disease_type = ?
        AND strftime('%m', tr.test_date) = ?
        AND strftime('%Y', tr.test_date) = ?
        GROUP BY tr.test_date
        ORDER BY tr.test_date
        '''
        
        df = pd.read_sql_query(query, conn, params=(disease_type, f'{month:02d}', str(year)))
        conn.close()
        
        if df.empty:
            return {'error': 'No data found for specified period'}
        
        summary = {
            'disease_type': disease_type,
            'month': int(month),
            'year': int(year),
            'total_tests': int(df['total_tests'].sum()),
            'total_positive': int(df['positive_cases'].sum()),
            'total_negative': int(df['negative_cases'].sum()),
            'avg_daily_cases': float(df['positive_cases'].mean()),
            'peak_day': str(df.loc[df['positive_cases'].idxmax(), 'test_date']) if len(df) > 0 else None,
            'peak_day_cases': int(df['positive_cases'].max()) if len(df) > 0 else 0,
            'daily_breakdown': df.to_dict('records')
        }
        
        # Convert to native types
        return self._convert_to_native_types(summary)
    
    def detect_hotspots(self, disease_type: str, start_date: str, end_date: str, 
                       radius_km: float = 5.0, min_cases: int = 3) -> List[Dict]:
        """
        Detect disease hotspots using clustering analysis
        Groups cases within radius_km that have at least min_cases
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all positive cases in date range with location
        cursor.execute('''
        SELECT 
            tr.result_id,
            tr.test_date,
            p.address,
            p.latitude,
            p.longitude,
            h.hospital_name
        FROM test_results tr
        JOIN patients p ON tr.patient_id = p.patient_id
        JOIN hospitals h ON tr.hospital_id = h.hospital_id
        WHERE tr.disease_type = ?
        AND tr.test_result = 'Positive'
        AND tr.test_date BETWEEN ? AND ?
        AND p.latitude IS NOT NULL
        AND p.longitude IS NOT NULL
        ''', (disease_type, start_date, end_date))
        
        cases = [dict(row) for row in cursor.fetchall()]
        
        if len(cases) < min_cases:
            conn.close()
            return []
        
        # Simple clustering algorithm
        clusters = []
        used_cases = set()
        
        for i, case in enumerate(cases):
            if i in used_cases:
                continue
            
            cluster = [case]
            cluster_indices = {i}
            
            for j, other_case in enumerate(cases):
                if j in used_cases or i == j:
                    continue
                
                distance = self.calculate_distance(
                    case['latitude'], case['longitude'],
                    other_case['latitude'], other_case['longitude']
                )
                
                if distance <= radius_km:
                    cluster.append(other_case)
                    cluster_indices.add(j)
            
            if len(cluster) >= min_cases:
                # Calculate cluster center
                avg_lat = sum(c['latitude'] for c in cluster) / len(cluster)
                avg_lon = sum(c['longitude'] for c in cluster) / len(cluster)
                
                # Determine risk level
                if len(cluster) >= 10:
                    risk_level = 'Critical'
                elif len(cluster) >= 5:
                    risk_level = 'High'
                else:
                    risk_level = 'Moderate'
                
                hotspot = {
                    'location': cluster[0]['address'],
                    'latitude': float(avg_lat),
                    'longitude': float(avg_lon),
                    'case_count': int(len(cluster)),
                    'risk_level': risk_level,
                    'cases': cluster,
                    'radius_km': float(radius_km)
                }
                
                clusters.append(hotspot)
                used_cases.update(cluster_indices)
                
                # Save to database
                cursor.execute('''
                INSERT INTO hotspot_analysis 
                (disease_type, analysis_date, location, latitude, longitude, case_count, risk_level, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    disease_type,
                    end_date,
                    hotspot['location'],
                    avg_lat,
                    avg_lon,
                    len(cluster),
                    risk_level,
                    json.dumps({'cases': [c['result_id'] for c in cluster]})
                ))
        
        conn.commit()
        conn.close()
        
        # Convert to native types
        return self._convert_to_native_types(sorted(clusters, key=lambda x: x['case_count'], reverse=True))
    
    def detect_outbreak(self, disease_type: str, days_window: int = 7, 
                       threshold_increase: float = 2.0) -> Dict:
        """
        Detect potential outbreak by comparing recent cases to historical average
        """
        conn = self.get_connection()
        
        today = datetime.now().date()
        recent_start = today - timedelta(days=days_window)
        historical_start = today - timedelta(days=30)
        
        # Get recent cases
        query_recent = '''
        SELECT COUNT(*) as count
        FROM test_results
        WHERE disease_type = ?
        AND test_result = 'Positive'
        AND test_date BETWEEN ? AND ?
        '''
        
        recent_df = pd.read_sql_query(query_recent, conn, 
                                      params=(disease_type, str(recent_start), str(today)))
        recent_count = int(recent_df['count'][0])
        
        # Get historical average
        query_historical = '''
        SELECT COUNT(*) as count
        FROM test_results
        WHERE disease_type = ?
        AND test_result = 'Positive'
        AND test_date BETWEEN ? AND ?
        '''
        
        historical_df = pd.read_sql_query(query_historical, conn,
                                         params=(disease_type, str(historical_start), str(recent_start)))
        historical_count = int(historical_df['count'][0])
        
        conn.close()
        
        avg_per_week = historical_count / (30 / 7) if historical_count > 0 else 0
        
        is_outbreak = bool(recent_count >= (avg_per_week * threshold_increase) and recent_count >= 5)
        
        result = {
            'disease_type': disease_type,
            'is_outbreak': is_outbreak,
            'recent_cases': int(recent_count),
            'historical_avg': float(round(avg_per_week, 2)),
            'increase_factor': float(round(recent_count / avg_per_week, 2)) if avg_per_week > 0 else 0.0,
            'analysis_date': str(today),
            'alert_level': 'High' if is_outbreak else 'Normal'
        }
        
        # Convert to native types
        return self._convert_to_native_types(result)


# Example usage
if __name__ == "__main__":
    analyzer = DiseaseAnalyzer()
    
    # Generate daily stats
    stats = analyzer.generate_daily_statistics('Malaria', str(datetime.now().date()))
    print("📊 Daily Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Detect hotspots
    from datetime import timedelta
    start_date = str(datetime.now().date() - timedelta(days=30))
    end_date = str(datetime.now().date())
    hotspots = analyzer.detect_hotspots('Malaria', start_date, end_date)
    print(f"\n🔥 Detected {len(hotspots)} hotspots")
    
    # Check for outbreak
    outbreak = analyzer.detect_outbreak('Malaria')
    print(f"\n⚠️ Outbreak Status: {outbreak['alert_level']}")