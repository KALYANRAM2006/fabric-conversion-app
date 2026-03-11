"""
API Routes for Fabric Conversion App
"""

from flask import Blueprint, request, jsonify
import logging
from app.services.oracle_service import OracleService
from app.services.fabric_service import FabricService
from app.services.claude_service import ClaudeService
from app.config.config import ConfigManager

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

config_manager = ConfigManager()


@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get saved configuration (without sensitive data)"""
    try:
        config = config_manager.get_config()
        # Remove sensitive data
        safe_config = {
            'oracle': {
                'user': config.get('oracle', {}).get('user', ''),
                'dsn': config.get('oracle', {}).get('dsn', ''),
                'schema': config.get('oracle', {}).get('schema', ''),
            },
            'fabric': {
                'server': config.get('fabric', {}).get('server', ''),
                'database': config.get('fabric', {}).get('database', ''),
                'schema': config.get('fabric', {}).get('schema', 'dbo'),
            },
            'hasClaudeKey': bool(config.get('claude', {}).get('api_key'))
        }
        return jsonify(safe_config), 200
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['POST'])
def save_config():
    """Save configuration"""
    try:
        data = request.json
        config_manager.save_config(data)
        return jsonify({'message': 'Configuration saved successfully'}), 200
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/test-oracle', methods=['POST'])
def test_oracle():
    """Test Oracle database connection"""
    try:
        data = request.json
        oracle_service = OracleService(
            user=data.get('user'),
            password=data.get('password'),
            dsn=data.get('dsn')
        )

        success, message = oracle_service.test_connection()

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        logger.error(f"Oracle test failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/test-fabric', methods=['POST'])
def test_fabric():
    """Test Fabric Data Warehouse connection"""
    try:
        data = request.json
        fabric_service = FabricService(
            server=data.get('server'),
            database=data.get('database')
        )

        success, message = fabric_service.test_connection()

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        logger.error(f"Fabric test failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/test-claude', methods=['POST'])
def test_claude():
    """Test Claude API connection"""
    try:
        data = request.json
        claude_service = ClaudeService(api_key=data.get('api_key'))

        success, message = claude_service.test_connection()

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        logger.error(f"Claude test failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/tables/<schema>', methods=['POST'])
def get_tables(schema):
    """Get list of tables from Oracle schema"""
    try:
        data = request.json
        oracle_service = OracleService(
            user=data.get('user'),
            password=data.get('password'),
            dsn=data.get('dsn')
        )

        tables = oracle_service.get_tables(schema)

        return jsonify({'tables': tables}), 200

    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/extract-ddl', methods=['POST'])
def extract_ddl():
    """Extract Oracle DDL for specified tables"""
    try:
        data = request.json
        oracle_service = OracleService(
            user=data.get('oracle', {}).get('user'),
            password=data.get('oracle', {}).get('password'),
            dsn=data.get('oracle', {}).get('dsn')
        )

        schema = data.get('schema')
        tables = data.get('tables', [])

        results = {}
        for table_name in tables:
            ddl = oracle_service.extract_ddl(schema, table_name)
            if ddl:
                results[table_name] = ddl

        return jsonify({'ddl': results}), 200

    except Exception as e:
        logger.error(f"Error extracting DDL: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/convert-ddl', methods=['POST'])
def convert_ddl():
    """Convert Oracle DDL to Fabric DDL using Claude API"""
    try:
        data = request.json
        claude_service = ClaudeService(api_key=data.get('claude_api_key'))

        oracle_ddl_dict = data.get('oracle_ddl', {})
        results = {}

        for table_name, oracle_ddl in oracle_ddl_dict.items():
            fabric_ddl = claude_service.convert_ddl(oracle_ddl)
            if fabric_ddl:
                results[table_name] = fabric_ddl

        return jsonify({'fabric_ddl': results}), 200

    except Exception as e:
        logger.error(f"Error converting DDL: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/create-table', methods=['POST'])
def create_table():
    """Create table in Fabric Data Warehouse"""
    try:
        data = request.json
        fabric_service = FabricService(
            server=data.get('fabric', {}).get('server'),
            database=data.get('fabric', {}).get('database')
        )

        schema = data.get('schema', 'dbo')
        table_name = data.get('table_name')
        ddl = data.get('ddl')

        success, message = fabric_service.execute_ddl(ddl, schema, table_name)

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/create-tables-batch', methods=['POST'])
def create_tables_batch():
    """Create multiple tables in Fabric Data Warehouse"""
    try:
        data = request.json
        fabric_service = FabricService(
            server=data.get('fabric', {}).get('server'),
            database=data.get('fabric', {}).get('database')
        )

        schema = data.get('schema', 'dbo')
        tables = data.get('tables', {})  # {table_name: ddl}

        results = []
        for table_name, ddl in tables.items():
            success, message = fabric_service.execute_ddl(ddl, schema, table_name)
            results.append({
                'table': table_name,
                'success': success,
                'message': message
            })

        return jsonify({'results': results}), 200

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return jsonify({'error': str(e)}), 500
