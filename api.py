from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sys
import os

# Import our modules
from data_ingestion import DataIngestion
from analysis import DiseaseAnalyzer

app = Flask(__name__)
CORS(app)

ingestion = DataIngestion()
analyzer = DiseaseAnalyzer()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'DemicsTech API'}), 200


@app.route('/api/hospitals', methods=['POST'])
def add_hospital():
    """Add a new hospital to the system"""
    try:
        data = request.json
        hospital_id = ingestion.add_hospital(data)
        return jsonify({
            'success': True,
            'hospital_id': hospital_id,
            'message': 'Hospital added successfully'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Get all hospitals"""
    try:
        conn = ingestion.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hospitals ORDER BY hospital_name')
        hospitals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'hospitals': hospitals}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/test-results', methods=['POST'])
def add_test_result():
    """Add a new test result"""
    try:
        data = request.json
        result_id = ingestion.add_test_result(data)
        return jsonify({
            'success': True,
            'result_id': result_id,
            'message': 'Test result added successfully'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/test-results/bulk', methods=['POST'])
def bulk_add_test_results():
    """Add multiple test results at once"""
    try:
        data = request.json
        count = ingestion.bulk_add_test_results(data.get('results', []))
        return jsonify({
            'success': True,
            'count': count,
            'message': f'{count} test results added successfully'
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """Get daily statistics for a disease"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        date = request.args.get('date', str(datetime.now().date()))
        
        stats = analyzer.generate_daily_statistics(disease_type, date)
        return jsonify({'success': True, 'statistics': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/statistics/monthly', methods=['GET'])
def get_monthly_statistics():
    """Get monthly statistics for a disease"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        
        stats = analyzer.generate_monthly_statistics(disease_type, month, year)
        return jsonify({'success': True, 'statistics': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """Detect and return disease hotspots"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date', str(datetime.now().date()))
        radius_km = float(request.args.get('radius_km', 5.0))
        min_cases = int(request.args.get('min_cases', 3))
        
        if not start_date:
            # Default to last 30 days
            from datetime import timedelta
            start_date = str(datetime.now().date() - timedelta(days=30))
        
        hotspots = analyzer.detect_hotspots(disease_type, start_date, end_date, radius_km, min_cases)
        return jsonify({
            'success': True,
            'hotspots': hotspots,
            'count': len(hotspots)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/outbreak/detect', methods=['GET'])
def detect_outbreak():
    """Detect potential disease outbreak"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        days_window = int(request.args.get('days_window', 7))
        threshold = float(request.args.get('threshold', 2.0))
        
        result = analyzer.detect_outbreak(disease_type, days_window, threshold)
        return jsonify({'success': True, 'outbreak_analysis': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/cases', methods=['GET'])
def get_cases():
    """Get cases for a specific disease and time period"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        month = int(request.args.get('month', datetime.now().month))
        year = int(request.args.get('year', datetime.now().year))
        
        cases = ingestion.get_monthly_cases(disease_type, month, year)
        return jsonify({
            'success': True,
            'cases': cases,
            'count': len(cases)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        disease_type = request.args.get('disease_type', 'Malaria')
        
        today = str(datetime.now().date())
        month = datetime.now().month
        year = datetime.now().year
        
        # Get various analytics
        daily_stats = analyzer.generate_daily_statistics(disease_type, today)
        monthly_stats = analyzer.generate_monthly_statistics(disease_type, month, year)
        outbreak_status = analyzer.detect_outbreak(disease_type)
        
        from datetime import timedelta
        start_date = str(datetime.now().date() - timedelta(days=30))
        hotspots = analyzer.detect_hotspots(disease_type, start_date, today)
        
        return jsonify({
            'success': True,
            'dashboard': {
                'disease_type': disease_type,
                'date': today,
                'daily_statistics': daily_stats,
                'monthly_statistics': monthly_stats,
                'outbreak_status': outbreak_status,
                'hotspots': hotspots[:5]  # Top 5 hotspots
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    print("🚀 Starting DemicsTech API Server...")
    print("📍 API will be available at: http://localhost:5000")
    print("\n📚 Available Endpoints:")
    print("  POST   /api/hospitals")
    print("  GET    /api/hospitals")
    print("  POST   /api/test-results")
    print("  POST   /api/test-results/bulk")
    print("  GET    /api/statistics/daily")
    print("  GET    /api/statistics/monthly")
    print("  GET    /api/hotspots")
    print("  GET    /api/outbreak/detect")
    print("  GET    /api/cases")
    print("  GET    /api/dashboard")
    print("\n✅ Server starting...\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)