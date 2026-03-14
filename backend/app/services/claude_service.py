"""
Claude AI Service
Handles DDL conversion using Claude API
"""

import re
from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)


MODEL = "claude-sonnet-4-5"


class ClaudeService:
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        kwargs = {'api_key': api_key}
        if base_url:
            kwargs['base_url'] = base_url
        self.client = Anthropic(**kwargs)

    def test_connection(self):
        """Test Claude API connection"""
        try:
            # Try a simple message to test API key
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Say 'API test successful'"}
                ]
            )

            return True, "Claude API connection successful"

        except Exception as e:
            logger.error(f"Claude API test failed: {e}")
            return False, str(e)

    def convert_ddl(self, oracle_ddl, custom_instructions=''):
        """Convert Oracle DDL to Fabric DDL using Claude"""
        try:
            # Build user instructions section
            user_rules = ''
            if custom_instructions and custom_instructions.strip():
                user_rules = f"""
7. ADDITIONAL USER-SPECIFIED RULES (follow these strictly, but NEVER skip the ALTER TABLE PRIMARY KEY — rule 2 above always applies):
{custom_instructions}
"""

            prompt = f"""Convert the following Oracle DDL to Microsoft Fabric Data Warehouse compatible DDL (T-SQL).

Important Fabric Data Warehouse requirements:
1. Data types: Use appropriate T-SQL data types
   - NUMBER → DECIMAL or INT/BIGINT for integers
   - NUMBER(p,0) → INT or BIGINT based on precision
   - NUMBER(p,s) → DECIMAL(p,s)
   - VARCHAR2 → VARCHAR (NOT NVARCHAR — Fabric only supports NVARCHAR(MAX), not sized NVARCHAR(n))
   - CHAR → CHAR
   - DATE → DATE or DATETIME2(6)
   - TIMESTAMP → DATETIME2(6)
   - TIMESTAMP(n) → DATETIME2(6) — Fabric DATETIME2 precision must be between 0 and 6, never higher
   - CLOB → VARCHAR(MAX) or NVARCHAR(MAX)
   - BLOB → VARBINARY(MAX)
   - IMPORTANT: DATETIME2 must ALWAYS have an explicit precision between 0 and 6. Use DATETIME2(6) as the default. Never use bare DATETIME2 or DATETIME2(7) or higher.

2. PRIMARY KEY — THIS IS CRITICAL:
   - Do NOT put PRIMARY KEY inside the CREATE TABLE statement
   - You MUST generate a SEPARATE ALTER TABLE statement AFTER each CREATE TABLE for every table that has a PK
   - The EXACT syntax for Fabric primary keys is:
       ALTER TABLE schema.table_name ADD CONSTRAINT PK_table_name PRIMARY KEY NONCLUSTERED (column_name) NOT ENFORCED;
   - Both NONCLUSTERED and NOT ENFORCED are REQUIRED — never omit them
   - Example: If Oracle has CONSTRAINT PK_FOO PRIMARY KEY (COL1), you must output:
       CREATE TABLE schema.FOO ( COL1 BIGINT NOT NULL );
       ALTER TABLE schema.FOO ADD CONSTRAINT PK_FOO PRIMARY KEY NONCLUSTERED (COL1) NOT ENFORCED;

3. Other constraints:
   - Do NOT include UNIQUE constraints
   - Keep NOT NULL constraints
   - No FOREIGN KEY constraints
   - Remove Oracle-specific constraint names or adapt them

4. Indexes:
   - Do NOT generate CREATE INDEX statements (Fabric does not support explicit indexes)
   - Do NOT create clustered indexes

5. Fabric limitations:
   - No DEFAULT keyword in column definitions (Fabric does not support column defaults)
   - No IDENTITY columns unless explicitly needed
   - No FOREIGN KEY constraints (Fabric doesn't enforce them)
   - No CHECK constraints
   - No computed columns
   - NVARCHAR(n) is NOT supported — use VARCHAR(n) instead. Only NVARCHAR(MAX) is allowed.
   - Keep schema names simple (dbo, stage, etc.)
   - Column names should remain unchanged

6. Generate clean, executable DDL without comments
{user_rules}
Oracle DDL:
```sql
{oracle_ddl}
```

Return ONLY the Fabric-compatible DDL without any explanation or markdown code blocks."""

            message = self.client.messages.create(
                model=MODEL,
                max_tokens=4000,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            fabric_ddl = message.content[0].text.strip()

            # Clean up markdown if present
            if fabric_ddl.startswith("```"):
                lines = fabric_ddl.split('\n')
                # Remove first and last lines if they're markdown
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                fabric_ddl = '\n'.join(lines).strip()

            # Post-processing: convert NVARCHAR(n) to VARCHAR(n) — Fabric only supports NVARCHAR(MAX)
            def _fix_nvarchar(m):
                size = m.group(1)
                if size.strip().upper() == 'MAX':
                    return m.group(0)  # NVARCHAR(MAX) is fine
                return f'VARCHAR({size})'  # NVARCHAR(n) → VARCHAR(n)
            fabric_ddl = re.sub(
                r'NVARCHAR\s*\(([^)]+)\)',
                _fix_nvarchar,
                fabric_ddl,
                flags=re.IGNORECASE
            )

            # Post-processing: strip DEFAULT clauses that Fabric doesn't support
            fabric_ddl = re.sub(
                r'\s+DEFAULT\s+(?:\'[^\']*\'|\"[^\"]*\"|[^,\n\)]+)',
                '',
                fabric_ddl,
                flags=re.IGNORECASE
            )

            # Post-processing: fix DATETIME2 precision for Fabric (must be 0-6)
            # Replace DATETIME2(n) where n > 6 with DATETIME2(6)
            def _fix_datetime2_precision(m):
                precision = int(m.group(1))
                if precision > 6:
                    return 'DATETIME2(6)'
                return m.group(0)
            fabric_ddl = re.sub(
                r'DATETIME2\s*\((\d+)\)',
                _fix_datetime2_precision,
                fabric_ddl,
                flags=re.IGNORECASE
            )
            # Replace bare DATETIME2 (no precision) with DATETIME2(6)
            fabric_ddl = re.sub(
                r'DATETIME2(?!\s*\(\d+\))',
                'DATETIME2(6)',
                fabric_ddl,
                flags=re.IGNORECASE
            )

            # Post-processing: fix PRIMARY KEY constraints for Fabric
            # Remove inline PRIMARY KEY on column definitions inside CREATE TABLE
            # but PRESERVE ALTER TABLE ... PRIMARY KEY NONCLUSTERED ... NOT ENFORCED statements
            fabric_ddl = re.sub(
                r'(\b\w+\s+\w+(?:\([^)]*\))?\s+NOT\s+NULL)\s+PRIMARY\s+KEY',
                r'\1',
                fabric_ddl,
                flags=re.IGNORECASE
            )
            # Remove standalone PRIMARY KEY constraint lines INSIDE CREATE TABLE
            # (these have a comma before them and no ALTER TABLE)
            fabric_ddl = re.sub(
                r',\s*CONSTRAINT\s+\w+\s+PRIMARY\s+KEY\s*\([^)]*\)(?!\s*NOT\s+ENFORCED)',
                '',
                fabric_ddl,
                flags=re.IGNORECASE
            )
            # Remove standalone PRIMARY KEY (col) lines without CONSTRAINT keyword (inside CREATE TABLE)
            fabric_ddl = re.sub(
                r',\s*PRIMARY\s+KEY\s*\([^)]*\)(?!\s*NOT\s+ENFORCED)',
                '',
                fabric_ddl,
                flags=re.IGNORECASE
            )
            # Ensure ALTER TABLE PK statements use correct Fabric syntax:
            # ALTER TABLE x ADD CONSTRAINT y PRIMARY KEY NONCLUSTERED (col) NOT ENFORCED;
            fabric_ddl = re.sub(
                r'(ALTER\s+TABLE\s+\S+\s+ADD\s+CONSTRAINT\s+\S+\s+PRIMARY\s+KEY)\s+(?:CLUSTERED\s+)?\(([^)]+)\)(?:\s+NOT\s+ENFORCED)?',
                r'\1 NONCLUSTERED (\2) NOT ENFORCED',
                fabric_ddl,
                flags=re.IGNORECASE
            )
            # Remove UNIQUE constraints too
            fabric_ddl = re.sub(
                r',?\s*CONSTRAINT\s+\w+\s+UNIQUE\s*\([^)]*\)',
                '',
                fabric_ddl,
                flags=re.IGNORECASE
            )
            fabric_ddl = re.sub(
                r',?\s*UNIQUE\s*\([^)]*\)',
                '',
                fabric_ddl,
                flags=re.IGNORECASE
            )

            # FALLBACK: If Oracle DDL has a PK but the Fabric DDL is missing the ALTER TABLE PK,
            # auto-generate it from the Oracle source
            fabric_ddl = self._ensure_pk_alter_table(oracle_ddl, fabric_ddl)

            logger.info("Successfully converted DDL with Claude")
            return fabric_ddl

        except Exception as e:
            logger.error(f"Error converting DDL with Claude: {e}")
            raise

    def _ensure_pk_alter_table(self, oracle_ddl, fabric_ddl):
        """If Oracle DDL has a PRIMARY KEY but Fabric DDL lacks an ALTER TABLE PK, auto-generate it."""
        # Check if Fabric DDL already has ALTER TABLE ... PRIMARY KEY
        if re.search(r'ALTER\s+TABLE.*PRIMARY\s+KEY', fabric_ddl, re.IGNORECASE):
            return fabric_ddl

        # Extract PK info from Oracle DDL
        # Pattern: CONSTRAINT pk_name PRIMARY KEY (col1, col2, ...)
        pk_match = re.search(
            r'CONSTRAINT\s+(\w+)\s+PRIMARY\s+KEY\s*\(([^)]+)\)',
            oracle_ddl,
            re.IGNORECASE
        )
        if not pk_match:
            # Also check for inline PRIMARY KEY without constraint name
            pk_match = re.search(
                r'PRIMARY\s+KEY\s*\(([^)]+)\)',
                oracle_ddl,
                re.IGNORECASE
            )

        if not pk_match:
            return fabric_ddl  # No PK in Oracle DDL

        # Extract table name from CREATE TABLE in the Fabric DDL
        table_match = re.search(r'CREATE\s+TABLE\s+(\S+)', fabric_ddl, re.IGNORECASE)
        if not table_match:
            return fabric_ddl

        table_name = table_match.group(1)
        # Clean table name (remove trailing parenthesis if present)
        table_name = table_name.rstrip('(')

        if pk_match.lastindex == 2:
            # Has constraint name and columns
            pk_name = pk_match.group(1)
            pk_cols = pk_match.group(2).strip()
        else:
            # Only columns, generate constraint name
            pk_cols = pk_match.group(1).strip()
            short_name = table_name.split('.')[-1] if '.' in table_name else table_name
            pk_name = f'PK_{short_name}'

        alter_stmt = f'\n\nALTER TABLE {table_name} ADD CONSTRAINT {pk_name} PRIMARY KEY NONCLUSTERED ({pk_cols}) NOT ENFORCED;'
        fabric_ddl = fabric_ddl.rstrip().rstrip(';') + ';' + alter_stmt

        logger.info(f"Auto-generated ALTER TABLE PK for {table_name}")
        return fabric_ddl
