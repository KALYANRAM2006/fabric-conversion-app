"""API Routes for Fabric Conversion App"""

import os
from flask import Blueprint, request, jsonify
import logging
from app.services.oracle_service import OracleService
from app.services.fabric_service import FabricService
from app.services.claude_service import ClaudeService
from app.config.config import ConfigManager

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

config_manager = ConfigManager()


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify backend is running"""
    return jsonify({
        'status': 'online',
        'message': 'Backend server is running',
        'port': int(os.getenv('PORT', 5001))
    }), 200


# Oracle database registry - reads from environment variables
DATABASE_REGISTRY = {
    'EDWP': {
        'label': 'EDWP - Enterprise Data Warehouse Production',
        'user_env': 'EDWP_USER',
        'password_env': 'EDWP_PASSWORD',
        'dsn_env': 'EDWP_DSN',
        'schema_env': 'EDWP_SCHEMA',
    },
    'EDWDBP': {
        'label': 'EDWDBP - Enterprise Data Warehouse DB Production',
        'user_env': 'EDWDBP_USER',
        'password_env': 'EDWDBP_PASSWORD',
        'dsn_env': 'EDWDBP_DSN',
        'schema_env': 'EDWDBP_SCHEMA',
    },
    'EDWT': {
        'label': 'EDWT - Enterprise Data Warehouse Test',
        'user_env': 'EDWT_USER',
        'password_env': 'EDWT_PASSWORD',
        'dsn_env': 'EDWT_DSN',
        'schema_env': 'EDWT_SCHEMA',
    },
    'CLARITY': {
        'label': 'CLARITY - Clarity Production (Read-Only)',
        'user_env': 'CLARITY_USER',
        'password_env': 'CLARITY_PASSWORD',
        'dsn_env': 'CLARITY_DSN',
        'schema_env': 'CLARITY_SCHEMA',
    },
    'EDWDBT': {
        'label': 'EDWDBT - Enterprise Data Warehouse DB Test',
        'user_env': 'EDWDBT_USER',
        'password_env': 'EDWDBT_PASSWORD',
        'dsn_env': 'EDWDBT_DSN',
        'schema_env': 'EDWDBT_SCHEMA',
    },
    'EDWD': {
        'label': 'EDWD - Enterprise Data Warehouse Development',
        'user_env': 'EDWD_USER',
        'password_env': 'EDWD_PASSWORD',
        'dsn_env': 'EDWD_DSN',
        'schema_env': 'EDWD_SCHEMA',
    },
    'EDWDBD': {
        'label': 'EDWDBD - Enterprise Data Warehouse DB Development',
        'user_env': 'EDWDBD_USER',
        'password_env': 'EDWDBD_PASSWORD',
        'dsn_env': 'EDWDBD_DSN',
        'schema_env': 'EDWDBD_SCHEMA',
    },
}


def get_database_credentials(db_key):
    """Get database credentials from environment variables"""
    db_info = DATABASE_REGISTRY.get(db_key)
    if not db_info:
        return None
    return {
        'user': os.getenv(db_info['user_env'], ''),
        'password': os.getenv(db_info['password_env'], ''),
        'dsn': os.getenv(db_info['dsn_env'], ''),
        'schema': os.getenv(db_info['schema_env'], ''),
    }


@api_bp.route('/databases', methods=['GET'])
def get_databases():
    """Get list of available Oracle databases configured in .env"""
    try:
        databases = []
        for key, info in DATABASE_REGISTRY.items():
            # Only include databases that have credentials configured
            user = os.getenv(info['user_env'], '')
            dsn = os.getenv(info['dsn_env'], '')
            if user and dsn:
                databases.append({
                    'key': key,
                    'label': info['label'],
                    'user': user,
                    'dsn': dsn,
                    'schema': os.getenv(info['schema_env'], ''),
                })
        return jsonify({'databases': databases}), 200
    except Exception as e:
        logger.error(f"Error getting databases: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/databases/<db_key>/credentials', methods=['GET'])
def get_database_creds(db_key):
    """Get credentials for a specific database (password masked)"""
    try:
        creds = get_database_credentials(db_key)
        if not creds:
            return jsonify({'error': f'Database {db_key} not found'}), 404
        return jsonify({
            'user': creds['user'],
            'dsn': creds['dsn'],
            'schema': creds['schema'],
            'hasPassword': bool(creds['password']),
        }), 200
    except Exception as e:
        logger.error(f"Error getting database credentials: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/test-oracle-preset', methods=['POST'])
def test_oracle_preset():
    """Test Oracle connection using a preconfigured database from .env"""
    try:
        data = request.json
        db_key = data.get('database_key')
        creds = get_database_credentials(db_key)
        if not creds:
            return jsonify({'success': False, 'error': f'Database {db_key} not configured'}), 400

        oracle_service = OracleService(
            user=creds['user'],
            password=creds['password'],
            dsn=creds['dsn']
        )
        success, message = oracle_service.test_connection()

        if success:
            return jsonify({'success': True, 'message': message}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f"Oracle preset test failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get saved configuration (without sensitive data)"""
    try:
        config = config_manager.get_config()
        # Remove sensitive data, fall back to .env for Fabric defaults
        safe_config = {
            'oracle': {
                'user': config.get('oracle', {}).get('user', ''),
                'dsn': config.get('oracle', {}).get('dsn', ''),
                'schema': config.get('oracle', {}).get('schema', ''),
            },
            'fabric': {
                'server': config.get('fabric', {}).get('server', '') or os.getenv('FABRIC_SERVER', ''),
                'database': config.get('fabric', {}).get('database', '') or os.getenv('FABRIC_DATABASE', ''),
                'schema': config.get('fabric', {}).get('schema', '') or os.getenv('FABRIC_SCHEMA', 'dbo'),
            },
            'hasClaudeKey': bool(config.get('claude', {}).get('api_key') or os.getenv('ANTHROPIC_API_KEY', '').strip())
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


@api_bp.route('/fabric-schemas', methods=['POST'])
def get_fabric_schemas():
    """Get available schemas from Fabric Data Warehouse"""
    try:
        data = request.json
        fabric_service = FabricService(
            server=data.get('server'),
            database=data.get('database')
        )

        success, message, schemas = fabric_service.get_schemas()

        if success:
            return jsonify({'success': True, 'schemas': schemas}), 200
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        logger.error(f"Error getting Fabric schemas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/test-claude', methods=['POST'])
def test_claude():
    """Test Claude API connection"""
    try:
        data = request.json
        api_key = data.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        claude_service = ClaudeService(api_key=api_key, base_url=base_url)

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

        # Support preset database selection
        db_key = data.get('database_key')
        if db_key:
            creds = get_database_credentials(db_key)
            if not creds:
                return jsonify({'error': f'Database {db_key} not configured'}), 400
            oracle_service = OracleService(
                user=creds['user'],
                password=creds['password'],
                dsn=creds['dsn']
            )
        else:
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

        # Support preset database selection
        db_key = data.get('database_key')
        if db_key:
            creds = get_database_credentials(db_key)
            if not creds:
                return jsonify({'error': f'Database {db_key} not configured'}), 400
            oracle_service = OracleService(
                user=creds['user'],
                password=creds['password'],
                dsn=creds['dsn']
            )
        else:
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
        api_key = data.get('claude_api_key') or os.getenv('ANTHROPIC_API_KEY')
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        custom_instructions = data.get('custom_instructions', '')
        claude_service = ClaudeService(api_key=api_key, base_url=base_url)

        oracle_ddl_dict = data.get('oracle_ddl', {})
        results = {}

        for table_name, oracle_ddl in oracle_ddl_dict.items():
            fabric_ddl = claude_service.convert_ddl(oracle_ddl, custom_instructions=custom_instructions)
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
        server = data.get('fabric', {}).get('server') or os.getenv('FABRIC_SERVER', '')
        database = data.get('fabric', {}).get('database') or os.getenv('FABRIC_DATABASE', '')
        logger.info(f"Creating table - server={server[:30]}... db={database}")
        fabric_service = FabricService(
            server=server,
            database=database
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
        server = data.get('fabric', {}).get('server') or os.getenv('FABRIC_SERVER', '')
        database = data.get('fabric', {}).get('database') or os.getenv('FABRIC_DATABASE', '')
        logger.info(f"Batch create - server={server[:30]}... db={database}")
        fabric_service = FabricService(
            server=server,
            database=database
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


@api_bp.route('/compare-columns', methods=['POST'])
def compare_columns():
    """Compare columns between two tables (Oracle-to-Oracle or Oracle-to-Fabric)"""
    try:
        data = request.json
        left = data.get('left', {})
        right = data.get('right', {})

        # Get left side columns
        if left.get('type') == 'oracle':
            left_creds = get_database_credentials(left.get('database'))
            if not left_creds:
                return jsonify({'error': f'Left database {left.get("database")} not configured'}), 400

            left_oracle = OracleService(
                user=left_creds['user'],
                password=left_creds['password'],
                dsn=left_creds['dsn']
            )
            left_columns = left_oracle.get_table_columns(left.get('schema'), left.get('table'))
        else:  # fabric
            # Use provided Fabric server/database or fall back to environment
            fabric_server = left.get('fabricServer') or os.getenv('FABRIC_SERVER')
            fabric_database = left.get('fabricDatabase') or os.getenv('FABRIC_DATABASE')
            left_fabric = FabricService(
                server=fabric_server,
                database=fabric_database
            )
            left_columns = left_fabric.get_table_columns(left.get('schema'), left.get('table'))

        # Get right side columns
        if right.get('type') == 'oracle':
            right_creds = get_database_credentials(right.get('database'))
            if not right_creds:
                return jsonify({'error': f'Right database {right.get("database")} not configured'}), 400

            right_oracle = OracleService(
                user=right_creds['user'],
                password=right_creds['password'],
                dsn=right_creds['dsn']
            )
            right_columns = right_oracle.get_table_columns(right.get('schema'), right.get('table'))
        else:  # fabric
            # Use provided Fabric server/database or fall back to environment
            fabric_server = right.get('fabricServer') or os.getenv('FABRIC_SERVER')
            fabric_database = right.get('fabricDatabase') or os.getenv('FABRIC_DATABASE')
            right_fabric = FabricService(
                server=fabric_server,
                database=fabric_database
            )
            right_columns = right_fabric.get_table_columns(right.get('schema'), right.get('table'))

        return jsonify({
            'left_columns': left_columns,
            'right_columns': right_columns,
            'left_info': left,
            'right_info': right
        }), 200

    except Exception as e:
        logger.error(f"Error comparing columns: {e}")
        return jsonify({'error': str(e)}), 500
