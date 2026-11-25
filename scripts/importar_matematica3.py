"""Valida ou importa Matemática 3; dry-run por padrão."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, str(ROOT))

import django
django.setup()

from curriculo.math3_import import validate_math3_source, import_math3_game

parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true", help="Grava o módulo no banco.")
args = parser.parse_args()
source = ROOT / "modulo3_matematica.json"
if not source.exists():
    raise SystemExit("Coloque modulo3_matematica.json na raiz do projeto.")
data = json.loads(source.read_text(encoding="utf-8"))
phases, grouped = validate_math3_source(data)
if args.apply:
    result = import_math3_game(data)
    result["status"] = "imported"
else:
    result = {
        "status": "dry_run_ok",
        "game": data["module"]["title"],
        "topics": len(phases),
        "questions": sum(len(items) for items in grouped.values()),
        "answer_types": sorted({e["challenge"]["answer"]["type"] for e in data["exercises"]}),
        "numeric_formulas": sorted({
            e["challenge"]["answer"]["formula"]
            for e in data["exercises"]
            if e["challenge"]["answer"]["type"] in {"numeric", "pair_numeric", "dynamic_choice"}
        }),
        "apply_required": True,
    }
print(json.dumps(result, ensure_ascii=False, indent=2))
