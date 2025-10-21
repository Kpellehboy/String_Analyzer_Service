#!/bin/bash
export FLASK_APP=string_analyzer/app.py  # path to your main Flask file
export FLASK_ENV=production
flask run --host=0.0.0.0 --port=${PORT}

