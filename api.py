from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sys
import os

# Import our modules
from data_ingestion import DataIngestion
from analysis import DiseaseAnalyzer
from database import create_database, check_database_exists

app = Flask(__name__)
CORS(app)

# Initialize database on startup
DB_PATH = os.environ.get('DATABASE_PATH', 'demicstech.db')

print("🔍 Checking database...")
if not check_database_exists(DB_PATH):
    print("📦 Database not found. Creating new database...")
    create_database(DB_PATH)
    print("✅ Database initialized successfully!")
else:
    print("✅ Database found and ready!")

# Initialize services
ingestion = DataIngestion(db_path=DB_PATH)
analyzer = DiseaseAnalyzer(db_path=DB_PATH)


@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'service': 'DemicsTech API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'hospitals': '/api/hospitals',
            'test_results': '/api/test-results',
            'statistics': '/api/statistics',
            'hotspots': '/api/hotspots',
            'outbreak': '/api/outbreak/detect',
            'dashboard': '/api/dashboard'
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = ingestion.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM hospitals')
        hospital_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'service': 'DemicsTech API',
            'database': 'connected',
            'hospitals_registered': hospital_count
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'DemicsTech API',
            'error': str(e)
        }), 500


@app.route('/api/hospitals', methods=['POST'])
def add_hospital():
    """Add a new hospital to the system"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('hospital_name') or not data.get('location'):
            return jsonify({
                'success': False,
                'error': 'hospital_name and location are required'
            }), 400
        
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
        
        # Validate required fields
        required_fields = ['hospital_id', 'disease_type', 'test_result', 'test_date', 'patient_data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
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
        results = data.get('results', [])
        
        if not results:
            return jsonify({
                'success': False,
                'error': 'No results provided'
            }), 400
        
        count = ingestion.bulk_add_test_results(results)
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


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    # Get port from environment variable (for Render deployment)
    port = int(os.environ.get('PORT', 5000))
    
    print("\n" + "="*60)
    print("🚀 DemicsTech API Server Starting...")
    print("="*60)
    print(f"📍 Server URL: http://0.0.0.0:{port}")
    print(f"💾 Database: {DB_PATH}")
    print("\n📚 Available Endpoints:")
    print("  GET    /              - API information")
    print("  GET    /health        - Health check")
    print("  POST   /api/hospitals - Add hospital")
    print("  GET    /api/hospitals - Get all hospitals")
    print("  POST   /api/test-results - Add test result")
    print("  POST   /api/test-results/bulk - Bulk add test results")
    print("  GET    /api/statistics/daily - Daily statistics")
    print("  GET    /api/statistics/monthly - Monthly statistics")
    print("  GET    /api/hotspots - Detect hotspots")
    print("  GET    /api/outbreak/detect - Detect outbreak")
    print("  GET    /api/cases - Get cases")
    print("  GET    /api/dashboard - Dashboard data")
    print("="*60)
    print("✅ Server ready!\n")
    
    # Run the app
    # Use debug=False for production on Render
    app.run(debug=False, host='0.0.0.0', port=port)