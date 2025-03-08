import sys
import os

sys.path.insert(0, '/sd/habitminder')

# Активация виртуального окружения
activate_venv = os.path.expanduser('/sd/habitminder/venv/bin/activate_this.py')
with open(activate_venv) as f:
    exec(f.read(), {'__file__': activate_venv})

from app import app as application