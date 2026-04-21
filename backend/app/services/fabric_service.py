"""
Fabric Data Warehouse Service
Handles Fabric connections and DDL execution
"""

import struct
import os
import json
import re
import time
import subprocess
import pyodbc
import logging

logger = logging.getLogger(__name__)

# Token cache to avoid repeated Azure CLI calls
_token_cache = {
    "token": None,
    "expires_on": 0,
}

# Known az.cmd locations on Windows
_AZ_CMD_PATHS = [
    r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
    r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
]


def _find_az_cmd():
    """Find the az.cmd executable on Windows"""
    for path in _AZ_CMD_PATHS:
        if os.path.isfile(path):
            return path
    return None


def _get_token_via_subprocess():
    """Get Azure AD token by directly invoking az.cmd with full path"""
    az_cmd = _find_az_cmd()
    if not az_cmd:
        raise Exception(f"az.cmd not found in known paths: {_AZ_CMD_PATHS}")

    logger.info(f"Getting token via subprocess: {az_cmd}")
    result = subprocess.run(
        [az_cmd, "account", "get-access-token", "--resource", "https://database.windows.net"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise Exception(f"az CLI failed (exit {result.returncode}): {result.stderr}")

    token_data = json.loads(result.stdout)
    return token_data["accessToken"], token_data.get("expiresOn", "")


def _get_fabric_token():
    """Get an Azure AD access token for Fabric/SQL, with caching"""
    global _token_cache

    # Return cached token if still valid (with 5-minute buffer)
    if _token_cache["token"] and _token_cache["expires_on"] > time.time() + 300:
        logger.info("Using cached Fabric token")
        return _token_cache["token"]

    first_error = None
    second_error = None

    # Primary: direct subprocess call to az.cmd (most reliable on Windows)
    try:
        token, expires_on_str = _get_token_via_subprocess()
        # Parse expiry - az CLI returns ISO format datetime
        try:
            from datetime import datetime
            expires_dt = datetime.fromisoformat(expires_on_str.replace("Z", "+00:00"))
            _token_cache["expires_on"] = expires_dt.timestamp()
        except Exception:
            # If we can't parse expiry, cache for 30 minutes
            _token_cache["expires_on"] = time.time() + 1800
        _token_cache["token"] = token
        logger.info("Got Fabric token via az.cmd subprocess")
        return token
    except Exception as e:
        first_error = e
        logger.warning(f"Subprocess token fetch failed: {e}, trying AzureCliCredential...")

    # Fallback 1: AzureCliCredential
    try:
        from azure.identity import AzureCliCredential
        # Ensure Azure CLI is on PATH
        az_cli_dirs = [
            r"C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin",
            r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin",
        ]
        current_path = os.environ.get("PATH", "")
        for p in az_cli_dirs:
            if os.path.isdir(p) and p not in current_path:
                os.environ["PATH"] = p + os.pathsep + current_path
                current_path = os.environ["PATH"]

        credential = AzureCliCredential()
        token_obj = credential.get_token("https://database.windows.net/.default")
        _token_cache["token"] = token_obj.token
        _token_cache["expires_on"] = token_obj.expires_on
        logger.info("Got Fabric token via AzureCliCredential")
        return token_obj.token
    except Exception as e2:
        second_error = e2
        logger.warning(f"AzureCliCredential failed: {e2}, trying InteractiveBrowserCredential...")

    # Fallback 2: InteractiveBrowserCredential (opens browser for interactive login)
    try:
        from azure.identity import InteractiveBrowserCredential
        credential = InteractiveBrowserCredential()
        token_obj = credential.get_token("https://database.windows.net/.default")
        _token_cache["token"] = token_obj.token
        _token_cache["expires_on"] = token_obj.expires_on
        logger.info("Got Fabric token via InteractiveBrowserCredential")
        return token_obj.token
    except Exception as e3:
        raise Exception(f"All token methods failed. Subprocess: {first_error}, AzureCliCredential: {second_error}, InteractiveBrowserCredential: {e3}")


def _token_bytes(token_str):
    """Convert a token string to the bytes format pyodbc expects for SQL_COPT_SS_ACCESS_TOKEN"""
    token_bytes = token_str.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    return token_struct


class FabricService:
    def __init__(self, server, database):
        self.server = server
        self.database = database
        self.connection = None

    def connect(self):
        """Establish Fabric connection using Azure CLI token"""
        try:
            # Get access token from Azure CLI
            logger.info("Getting Azure AD token via Azure CLI...")
            access_token = _get_fabric_token()

            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )

            # Use token-based auth (SQL_COPT_SS_ACCESS_TOKEN = 1256)
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            self.connection = pyodbc.connect(
                connection_string,
                attrs_before={SQL_COPT_SS_ACCESS_TOKEN: _token_bytes(access_token)},
                timeout=30
            )
            return True, "Connected successfully"

        except Exception as e:
            logger.error(f"Fabric connection failed: {e}")
            return False, str(e)

    def disconnect(self):
        """Close Fabric connection"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass

    def test_connection(self):
        """Test Fabric connection"""
        success, message = self.connect()
        if success:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.disconnect()
                return True, "Fabric connection successful"
            except Exception as e:
                self.disconnect()
                return False, f"Query failed: {str(e)}"
        return False, message

    def get_schemas(self):
        """Get all available schemas from Fabric warehouse"""
        try:
            success, msg = self.connect()
            if not success:
                return False, msg, []

            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT s.name
                FROM sys.schemas s
                INNER JOIN sys.database_principals p ON s.principal_id = p.principal_id
                ORDER BY s.name
            """)
            schemas = [row[0] for row in cursor.fetchall()]
            cursor.close()
            self.disconnect()
            return True, 'Schemas retrieved successfully', schemas

        except Exception as e:
            self.disconnect()
            logger.error(f"Error getting schemas: {e}")
            return False, str(e), []

    def execute_ddl(self, ddl, schema, table_name):
        """Execute DDL in Fabric"""
        try:
            success, msg = self.connect()
            if not success:
                raise Exception(f"Failed to connect to Fabric: {msg}")

            # Fabric uses snapshot isolation — DDL is not allowed inside transactions.
            # Enable autocommit so each statement runs outside a transaction.
            self.connection.autocommit = True

            cursor = self.connection.cursor()

            try:
                # Create schema if needed
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema}')
                    EXEC('CREATE SCHEMA {schema}')
                """)

                # Drop table if exists
                cursor.execute(f"DROP TABLE IF EXISTS {schema}.{table_name}")

                # Execute DDL statements one at a time
                # Split on semicolons but also handle GO batch separators
                raw_statements = ddl.split(';')
                statements = []
                for s in raw_statements:
                    # Split on GO batch separator (standalone line)
                    parts = re.split(r'(?m)^\s*GO\s*$', s)
                    for p in parts:
                        cleaned = p.strip()
                        if cleaned and cleaned.upper() != 'GO':
                            statements.append(cleaned)

                for stmt in statements:
                    logger.info(f"Executing: {stmt[:120]}...")
                    cursor.execute(stmt)

                cursor.close()
                self.disconnect()

                logger.info(f"Successfully created table {schema}.{table_name}")
                return True, f"Table {schema}.{table_name} created successfully"

            except Exception as e:
                cursor.close()
                self.disconnect()
                raise e

        except Exception as e:
            self.disconnect()
            logger.error(f"Error executing DDL: {e}")
            return False, str(e)

    def get_table_columns(self, schema, table_name):
        """Get detailed column information for a table in Fabric"""
        try:
            success, _ = self.connect()
            if not success:
                raise Exception("Failed to connect to Fabric")

            cursor = self.connection.cursor()

            # Query system views for column information
            query = """
                SELECT
                    c.COLUMN_NAME,
                    c.DATA_TYPE,
                    c.CHARACTER_MAXIMUM_LENGTH,
                    c.NUMERIC_PRECISION,
                    c.NUMERIC_SCALE,
                    c.IS_NULLABLE,
                    c.ORDINAL_POSITION
                FROM INFORMATION_SCHEMA.COLUMNS c
                WHERE c.TABLE_SCHEMA = ?
                  AND c.TABLE_NAME = ?
                ORDER BY c.ORDINAL_POSITION
            """

            cursor.execute(query, (schema, table_name))

            columns = []
            for row in cursor.fetchall():
                col_name, data_type, char_length, num_precision, num_scale, is_nullable, ordinal = row

                # Format data type with length/precision
                if data_type in ('varchar', 'char', 'nvarchar', 'nchar'):
                    type_display = f"{data_type}({char_length if char_length else 'max'})"
                elif data_type in ('decimal', 'numeric'):
                    if num_precision and num_scale:
                        type_display = f"{data_type}({num_precision},{num_scale})"
                    elif num_precision:
                        type_display = f"{data_type}({num_precision})"
                    else:
                        type_display = data_type
                elif data_type in ('bigint', 'int', 'smallint', 'tinyint') and num_precision:
                    type_display = f"{data_type}({num_precision})"
                elif data_type in ('datetime2', 'datetimeoffset', 'time') and num_scale is not None:
                    type_display = f"{data_type}({num_scale})"
                else:
                    type_display = data_type

                columns.append({
                    'column_name': col_name,
                    'data_type': type_display,
                    'data_length': char_length,
                    'data_precision': num_precision,
                    'data_scale': num_scale,
                    'nullable': is_nullable,
                    'column_id': ordinal
                })

            cursor.close()
            self.disconnect()

            return columns

        except Exception as e:
            self.disconnect()
            logger.error(f"Error getting table columns from Fabric: {e}")
            raise
