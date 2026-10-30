"""Production entry point for gunicorn.

Run:  gunicorn --bind 0.0.0.0:8000 wsgi:application
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models
import app as appmod

models.init_db()
appmod.seed_categories()

application = appmod.app
