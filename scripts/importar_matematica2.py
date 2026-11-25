"""Valida ou importa Matemática 2; dry-run por padrão."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
sys.path.insert(0,str(ROOT))
import django
django.setup()
from curriculo.math2_import import validate_math2_source,import_math2_game
p=argparse.ArgumentParser()
p.add_argument("--apply",action="store_true")
a=p.parse_args()
source=ROOT/"modulo2_matematica.json"
if not source.exists(): raise SystemExit("Coloque modulo2_matematica.json na raiz do projeto.")
data=json.loads(source.read_text(encoding="utf-8"))
phases,grouped=validate_math2_source(data)
if a.apply: result=import_math2_game(data); result["status"]="imported"
else: result={"status":"dry_run_ok","game":data["module"]["title"],"topics":len(phases),"questions":sum(map(len,grouped.values())),"numeric_formulas":len({e["challenge"]["answer"]["formula"] for e in data["exercises"] if e["challenge"]["answer"]["type"]=="numeric"}),"apply_required":True}
print(json.dumps(result,ensure_ascii=False,indent=2))
