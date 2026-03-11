"""
Fabric Data Warehouse Service
Handles Fabric connections and DDL execution
"""

import pyodbc
import logging

logger = logging.getLogger(__name__)


class FabricService:
    def __init__(self, server, database):
        self.server = server
        self.database = database
        self.connection = None

    def connect(self):
        """Establish Fabric connection using Azure AD Interactive"""
        try:
            connection_string = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"Authentication=ActiveDirectoryInteractive;"
                f"Encrypt=yes;"
                f"TrustServerCertificate=no;"
            )

            self.connection = pyodbc.connect(connection_string)
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

    def execute_ddl(self, ddl, schema, table_name):
        """Execute DDL in Fabric"""
        try:
            success, _ = self.connect()
            if not success:
                raise Exception("Failed to connect to Fabric")

            cursor = self.connection.cursor()

            try:
                # Create schema if needed
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema}')
                    EXEC('CREATE SCHEMA {schema}')
                """)
                self.connection.commit()

                # Drop table if exists
                cursor.execute(f"DROP TABLE IF EXISTS {schema}.{table_name}")
                self.connection.commit()

                # Execute DDL statements
                statements = [stmt.strip() for stmt in ddl.split(';') if stmt.strip()]

                for stmt in statements:
                    if stmt:
                        cursor.execute(stmt)
                        self.connection.commit()

                cursor.close()
                self.disconnect()

                logger.info(f"Successfully created table {schema}.{table_name}")
                return True, f"Table {schema}.{table_name} created successfully"

            except Exception as e:
                try:
                    self.connection.rollback()
                except:
                    pass
                cursor.close()
                self.disconnect()
                raise e

        except Exception as e:
            self.disconnect()
            logger.error(f"Error executing DDL: {e}")
            return False, str(e)
