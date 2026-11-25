"""Validação e importação idempotente de Química 1."""
from collections import defaultdict
from django.db import transaction
from .models import Materia,Disciplina,Modulo,Fase,Questao,Opcao
from .chem1_engine import FORMULAS
ANSWER_TYPES={'choice','numeric','dynamic_choice'}
def validate_chem1_source(data):
    m=data.get('module',{})
    if m.get('module_number')!=1 or m.get('subject')!='Química': raise ValueError('A fonte não corresponde à Química 1.')
    phases={p['number']:p for p in data.get('phases',[])}; exercises=data.get('exercises',[])
    if len(phases)!=5 or len(exercises)!=33: raise ValueError('Química 1 deve conter 5 módulos e 33 exercícios.')
    grouped=defaultdict(list); ids=set()
    for ex in exercises:
        if ex['id'] in ids or ex['phase'] not in phases: raise ValueError(f"ID duplicado ou módulo inválido: {ex.get('id')}")
        ids.add(ex['id']); grouped[ex['phase']].append(ex)
    expected=set()
    for n,p in phases.items():
        if len(grouped[n])!=p['exercise_count'] or set(p['exercise_ids'])!={e['id'] for e in grouped[n]}: raise ValueError(f'Manifesto inconsistente no módulo {n}.')
        expected.update(p['exercise_ids'])
    if ids!=expected: raise ValueError('IDs não correspondem ao manifesto.')
    for ex in exercises:
        a=ex['challenge']['answer']; kind=a.get('type')
        if kind not in ANSWER_TYPES: raise ValueError(f'Tipo inválido em {ex["id"]}: {kind}')
        if kind in {'numeric','dynamic_choice'} and a.get('formula') not in FORMULAS: raise ValueError(f"Fórmula não implementada em {ex['id']}.")
        if kind in {'choice','dynamic_choice'} and not a.get('choices'): raise ValueError(f"Sem alternativas em {ex['id']}.")
        if kind=='choice' and not 0<=int(a['correct'])<len(a['choices']): raise ValueError(f"Gabarito inválido em {ex['id']}.")
        keys=[]
        for s in ex.get('simulation',{}).get('parameters',[]):
            if s['step']<=0 or s['min']>s['max'] or not s['min']<=s['value']<=s['max']: raise ValueError(f"Parâmetro inválido em {ex['id']}.")
            keys.append(s['key'])
        if len(keys)!=len(set(keys)): raise ValueError(f"Parâmetro duplicado em {ex['id']}.")
    return phases,grouped
@transaction.atomic
def import_chem1_game(data):
    phases,grouped=validate_chem1_source(data)
    subject,_=Materia.objects.get_or_create(slug='quimica',defaults={'nome':'Química','descricao':'Jogos de Química','icone':'flask-conical','ordem':3,'ativo':True})
    game,_=Disciplina.objects.get_or_create(slug='quimica-1',defaults={'nome':'Química 1','descricao':data['module'].get('description',''),'materia':subject,'icone':'flask-conical','ordem':1,'ativo':False})
    total=0
    for number,topic_data in sorted(phases.items()):
        topic,_=Modulo.objects.update_or_create(disciplina=game,ordem=number,defaults={'titulo':topic_data['title'],'descricao':topic_data.get('description','')})
        for order,ex in enumerate(grouped[number],1):
            a=ex['challenge']['answer']; dynamic={**ex,'source_chem_module':1,'source_exercise_id':ex['id']}
            phase,_=Fase.objects.update_or_create(modulo=topic,ordem=order,defaults={'titulo':ex['title'][:150],'tipo':'quiz','xp_recompensa':int(ex.get('completion',{}).get('xp',30)),'moedas_recompensa':0,'deslocamento_y':0})
            q,_=Questao.objects.update_or_create(codigo_fonte=ex['id'],defaults={'fase':phase,'enunciado':ex['challenge']['prompt'],'explicacao_erro':a.get('explanation',a.get('solution','')),'tipo_resposta':'choice' if a['type'] in {'choice','dynamic_choice'} else 'numeric','dados_dinamicos':dynamic})
            if a['type']=='choice':
                for i,label in enumerate(a['choices'],1): Opcao.objects.update_or_create(questao=q,ordem=i,defaults={'texto':label,'e_correta':i-1==a['correct']})
                q.opcoes.exclude(ordem__lte=len(a['choices'])).delete()
            elif a['type']=='dynamic_choice':
                for i,item in enumerate(a['choices'],1): Opcao.objects.update_or_create(questao=q,ordem=i,defaults={'texto':item['label'] if isinstance(item,dict) else str(item),'e_correta':False})
                q.opcoes.exclude(ordem__lte=len(a['choices'])).delete()
            else: q.opcoes.all().delete()
            total+=1
    return {'game':game.nome,'modules':len(phases),'phases':total,'questions':total,'discipline_id':game.pk}
