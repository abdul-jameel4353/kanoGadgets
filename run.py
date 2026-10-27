#!/usr/bin/env python3
"""Boot helper: initialise DB, seed categories, then run the app."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models
import app as appmod

if __name__ == "__main__":
    models.init_db()
    appmod.seed_categories()
    appmod.app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
                   debug=os.environ.get("DEBUG") == "1")
