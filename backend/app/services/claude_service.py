"""
Claude AI Service
Handles DDL conversion using Claude API
"""

from anthropic import Anthropic
import logging

logger = logging.getLogger(__name__)


class ClaudeService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)

    def test_connection(self):
        """Test Claude API connection"""
        try:
            # Try a simple message to test API key
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": "Say 'API test successful'"}
                ]
            )

            return True, "Claude API connection successful"

        except Exception as e:
            logger.error(f"Claude API test failed: {e}")
            return False, str(e)

    def convert_ddl(self, oracle_ddl):
        """Convert Oracle DDL to Fabric DDL using Claude"""
        try:
            prompt = f"""Convert the following Oracle DDL to Microsoft Fabric Data Warehouse compatible DDL (T-SQL).

Important Fabric Data Warehouse requirements:
1. Data types: Use appropriate T-SQL data types
   - NUMBER → DECIMAL or INT/BIGINT for integers
   - NUMBER(p,0) → INT or BIGINT based on precision
   - NUMBER(p,s) → DECIMAL(p,s)
   - VARCHAR2 → VARCHAR or NVARCHAR
   - CHAR → CHAR
   - DATE → DATE or DATETIME2
   - TIMESTAMP → DATETIME2
   - CLOB → VARCHAR(MAX) or NVARCHAR(MAX)
   - BLOB → VARBINARY(MAX)

2. Constraints:
   - Keep PRIMARY KEY constraints
   - Keep UNIQUE constraints
   - Keep NOT NULL constraints
   - Remove Oracle-specific constraint names or adapt them

3. Indexes:
   - Convert CREATE INDEX statements
   - Primary key becomes clustered index

4. Fabric limitations:
   - No IDENTITY columns unless explicitly needed
   - No foreign keys (Fabric doesn't enforce them)
   - Keep schema names simple (dbo, stage, etc.)
   - Column names should remain unchanged

5. Generate clean, executable DDL without comments

Oracle DDL:
```sql
{oracle_ddl}
```

Return ONLY the Fabric-compatible DDL without any explanation or markdown code blocks."""

            message = self.client.messages.create(
                model="claude-sonnet-4-6",
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

            logger.info("Successfully converted DDL with Claude")
            return fabric_ddl

        except Exception as e:
            logger.error(f"Error converting DDL with Claude: {e}")
            raise
