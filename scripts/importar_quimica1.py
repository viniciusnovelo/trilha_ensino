"""Valida ou importa Química 1; dry-run por padrão."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');sys.path.insert(0,str(ROOT))
import django;django.setup()
from curriculo.chem1_import import validate_chem1_source,import_chem1_game
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
source=ROOT/'modulo1_quimica.json'
if not source.exists(): raise SystemExit('Coloque modulo1_quimica.json na raiz do projeto.')
data=json.loads(source.read_text(encoding='utf-8'));phases,grouped=validate_chem1_source(data)
if args.apply: result=import_chem1_game(data);result['status']='imported'
else: result={'status':'dry_run_ok','game':data['module']['title'],'modules':len(phases),'phases':sum(map(len,grouped.values())),'questions':len(data['exercises']),'answer_types':sorted({e['challenge']['answer']['type'] for e in data['exercises']}),'formulas':sorted({e['challenge']['answer']['formula'] for e in data['exercises'] if e['challenge']['answer'].get('formula')}),'apply_required':True}
print(json.dumps(result,ensure_ascii=False,indent=2))
