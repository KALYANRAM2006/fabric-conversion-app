"""
Oracle Database Service
Handles Oracle connections and DDL extraction
"""

import oracledb
import logging

logger = logging.getLogger(__name__)


class OracleService:
    def __init__(self, user, password, dsn):
        self.user = user
        self.password = password
        self.dsn = dsn
        self.connection = None

    def connect(self):
        """Establish Oracle connection"""
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            return True, "Connected successfully"
        except Exception as e:
            logger.error(f"Oracle connection failed: {e}")
            return False, str(e)

    def disconnect(self):
        """Close Oracle connection"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass

    def test_connection(self):
        """Test Oracle connection"""
        success, message = self.connect()
        if success:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.close()
                self.disconnect()
                return True, "Oracle connection successful"
            except Exception as e:
                self.disconnect()
                return False, f"Query failed: {str(e)}"
        return False, message

    def get_tables(self, schema):
        """Get list of tables from schema"""
        try:
            success, _ = self.connect()
            if not success:
                raise Exception("Failed to connect to Oracle")

            cursor = self.connection.cursor()

            query = """
                SELECT
                    TABLE_NAME,
                    NUM_ROWS,
                    TABLESPACE_NAME
                FROM ALL_TABLES
                WHERE OWNER = :schema
                  AND TABLE_NAME NOT LIKE 'BIN$%'
                  AND TEMPORARY = 'N'
                ORDER BY TABLE_NAME
            """

            cursor.execute(query, {'schema': schema.upper()})
            tables = []

            for row in cursor.fetchall():
                tables.append({
                    'name': row[0],
                    'rows': row[1] or 0,
                    'tablespace': row[2]
                })

            cursor.close()
            self.disconnect()

            return tables

        except Exception as e:
            self.disconnect()
            logger.error(f"Error getting tables: {e}")
            raise

    def extract_ddl(self, schema, table_name):
        """Extract DDL for a table"""
        try:
            success, _ = self.connect()
            if not success:
                raise Exception("Failed to connect to Oracle")

            cursor = self.connection.cursor()

            # Get column definitions
            column_query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE,
                    NULLABLE,
                    DATA_DEFAULT
                FROM ALL_TAB_COLUMNS
                WHERE OWNER = :schema
                  AND TABLE_NAME = :table_name
                ORDER BY COLUMN_ID
            """

            cursor.execute(column_query, {
                'schema': schema.upper(),
                'table_name': table_name.upper()
            })
            columns = cursor.fetchall()

            if not columns:
                raise Exception(f"Table {schema}.{table_name} not found")

            # Build column definitions
            col_defs = []
            for col in columns:
                col_name, data_type, length, precision, scale, nullable, default = col

                # Format data type
                if data_type == 'NUMBER':
                    if precision is None and scale is None:
                        col_type = 'NUMBER'
                    elif scale == 0 or scale is None:
                        col_type = f'NUMBER({precision})'
                    else:
                        col_type = f'NUMBER({precision},{scale})'
                elif data_type in ('VARCHAR2', 'NVARCHAR2'):
                    col_type = f'VARCHAR2({length})'
                elif data_type == 'CHAR':
                    col_type = f'CHAR({length})'
                elif data_type == 'DATE':
                    col_type = 'DATE'
                elif data_type in ('TIMESTAMP', 'TIMESTAMP(6)'):
                    col_type = 'TIMESTAMP'
                elif data_type in ('CLOB', 'NCLOB'):
                    col_type = 'CLOB'
                elif data_type == 'BLOB':
                    col_type = 'BLOB'
                else:
                    col_type = data_type

                null_constraint = '' if nullable == 'Y' else ' NOT NULL'
                default_clause = f' DEFAULT {default.strip()}' if default else ''

                col_def = f"  {col_name} {col_type}{null_constraint}{default_clause}"
                col_defs.append(col_def)

            # Get primary key
            pk_query = """
                SELECT
                    cons.CONSTRAINT_NAME,
                    cols.COLUMN_NAME
                FROM ALL_CONSTRAINTS cons
                JOIN ALL_CONS_COLUMNS cols ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
                    AND cons.OWNER = cols.OWNER
                WHERE cons.CONSTRAINT_TYPE = 'P'
                  AND cons.OWNER = :schema
                  AND cons.TABLE_NAME = :table_name
                ORDER BY cols.POSITION
            """

            cursor.execute(pk_query, {
                'schema': schema.upper(),
                'table_name': table_name.upper()
            })
            pk_rows = cursor.fetchall()
            pk_cols = [row[1] for row in pk_rows]
            pk_name = pk_rows[0][0] if pk_rows else None

            # Build DDL
            ddl = f"CREATE TABLE {schema}.{table_name} (\n"
            ddl += ",\n".join(col_defs)

            if pk_cols:
                ddl += f",\n  CONSTRAINT {pk_name} PRIMARY KEY ({', '.join(pk_cols)})"

            ddl += "\n);"

            cursor.close()
            self.disconnect()

            logger.info(f"Extracted DDL for {schema}.{table_name}")
            return ddl

        except Exception as e:
            self.disconnect()
            logger.error(f"Error extracting DDL: {e}")
            raise

    def get_table_columns(self, schema, table_name):
        """Get detailed column information for a table"""
        try:
            success, _ = self.connect()
            if not success:
                raise Exception("Failed to connect to Oracle")

            cursor = self.connection.cursor()

            query = """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    DATA_LENGTH,
                    DATA_PRECISION,
                    DATA_SCALE,
                    NULLABLE,
                    COLUMN_ID
                FROM ALL_TAB_COLUMNS
                WHERE OWNER = :schema
                  AND TABLE_NAME = :table_name
                ORDER BY COLUMN_ID
            """

            cursor.execute(query, {
                'schema': schema.upper(),
                'table_name': table_name.upper()
            })

            columns = []
            for row in cursor.fetchall():
                col_name, data_type, data_length, data_precision, data_scale, nullable, col_id = row

                # Format data type with length/precision
                if data_type in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR'):
                    type_display = f"{data_type}({data_length})"
                elif data_type == 'NUMBER':
                    if data_precision:
                        if data_scale and data_scale > 0:
                            type_display = f"NUMBER({data_precision},{data_scale})"
                        else:
                            type_display = f"NUMBER({data_precision})"
                    else:
                        type_display = "NUMBER"
                elif data_type == 'DATE':
                    type_display = f"DATE(7)"
                elif data_type.startswith('TIMESTAMP'):
                    type_display = data_type
                else:
                    type_display = data_type

                columns.append({
                    'column_name': col_name,
                    'data_type': type_display,
                    'data_length': data_length,
                    'data_precision': data_precision,
                    'data_scale': data_scale,
                    'nullable': 'YES' if nullable == 'Y' else 'NO',
                    'column_id': col_id
                })

            cursor.close()
            self.disconnect()

            return columns

        except Exception as e:
            self.disconnect()
            logger.error(f"Error getting table columns: {e}")
            raise
