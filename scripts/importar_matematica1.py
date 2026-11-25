"""Valida ou importa o jogo Matemática 1."""
import argparse
import json
from pathlib import Path
import os
import sys
import django

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(ROOT))
django.setup()

from curriculo.math1_import import import_math1_game, validate_math1_source

parser = argparse.ArgumentParser(description="Importa Matemática 1 (5 tópicos, 35 questões).")
parser.add_argument("--apply", action="store_true", help="Grava o jogo no banco. Sem esta opção, apenas valida a fonte.")
args = parser.parse_args()

source = ROOT / "modulo1_matematica.json"
if not source.exists():
    raise SystemExit("Arquivo modulo1_matematica.json não encontrado na raiz do projeto.")
data = json.loads(source.read_text(encoding="utf-8"))
phases, grouped = validate_math1_source(data)

if args.apply:
    result = import_math1_game(data)
    result["status"] = "imported"
else:
    result = {
        "status": "dry_run_ok",
        "game": data["module"]["title"],
        "topics": len(phases),
        "phases": sum(len(items) for items in grouped.values()),
        "questions": len(data["exercises"]),
        "numeric_formulas": len({x["challenge"]["answer"]["formula"] for x in data["exercises"] if x["challenge"]["answer"]["type"] == "numeric"}),
        "apply_required": True,
    }
print(json.dumps(result, ensure_ascii=False, indent=2))
