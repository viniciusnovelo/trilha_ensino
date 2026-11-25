"""Importa o Matemática 1 a partir de modulo1_matematica.json."""
import json
from pathlib import Path
import django
from django.conf import settings
from django.core.management import execute_from_command_line
import os, sys
ROOT=Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
sys.path.insert(0,str(ROOT))
django.setup()
from curriculo.math1_import import import_math1_game
source=ROOT/"modulo1_matematica.json"
if not source.exists():
    raise SystemExit("Arquivo modulo1_matematica.json não encontrado na raiz do projeto.")
data=json.loads(source.read_text(encoding="utf-8"))
print(json.dumps(import_math1_game(data),ensure_ascii=False,indent=2))
