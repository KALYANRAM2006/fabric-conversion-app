"""
Oracle to Fabric DDL Converter - Backend Server

Flask API server for handling Oracle and Fabric connections and Claude AI integration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    print(f"Starting Fabric Conversion App Backend")
    print(f"   Server: http://{host}:{port}")
    print(f"   Debug: {debug}")
    print(f"   Press CTRL+C to quit")

    app.run(host=host, port=port, debug=debug)
