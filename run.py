#!/usr/bin/env python3
"""
Inspection Photo Review Application
Run this file to start the web application.
"""

import sys
import os

# Add the inspection_app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inspection_app'))

from flask_app import app

if __name__ == '__main__':
    print("=" * 50)
    print("  Inspection Photo Review")
    print("=" * 50)
    print()
    print("  Open in your browser:")
    print("  http://127.0.0.1:8080")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    app.run(host='127.0.0.1', port=8080, debug=True)
