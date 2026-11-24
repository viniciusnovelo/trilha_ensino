#!/usr/bin/env python3
"""Importa o Módulo 2 de Física sem apagar o banco ou alterar o Módulo 1."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.db import transaction
from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from curriculo.physics_module2_source import validate_source, validate_zip_archive


@transaction.atomic
def import_module(data: dict) -> dict:
    summary = validate_source(data)
    materia, _ = Materia.objects.update_or_create(slug='fisica', defaults={
        'nome':'Física','descricao':'Calor, transformações, ondas e luz','icone':'atom','ordem':1,'ativo':True,
    })
    disciplina, _ = Disciplina.objects.update_or_create(slug='fisica', defaults={
        'nome':'Física','descricao':'Trilha de Física','materia':materia,'icone':'atom','ordem':1,'ativo':True,'autor':None,
    })
    modulo, _ = Modulo.objects.update_or_create(disciplina=disciplina, ordem=2, defaults={
        'titulo':'Módulo 2','descricao':data.get('title','Calor, transformações, ondas e luz'),
    })
    phases = {p['number']:p for p in data['phases']}
    phase_objects = {}
    for number, phase in phases.items():
        obj, _ = Fase.objects.update_or_create(modulo=modulo,ordem=number,defaults={
            'titulo':phase['title'],'tipo':'quiz','xp_recompensa':0,'moedas_recompensa':0,
        })
        phase_objects[number]=obj
    expected_ids=set()
    for exercise in data['exercises']:
        expected_ids.add(exercise['id'])
        answer=exercise['challenge']['answer']; kind=answer['type']
        dynamic={**exercise,'source_schema_version':data.get('schema_version'),
                 'source_constants':data.get('constants',{}),'source_module':2,
                 'source_phase_id':phases[exercise['phase']]['id'],
                 'source_phase_metadata':phases[exercise['phase']]}
        question,_=Questao.objects.update_or_create(
            fase=phase_objects[exercise['phase']],codigo_fonte=exercise['id'],
            defaults={'enunciado':exercise['challenge']['prompt'],
                      'explicacao_erro':answer.get('explanation',answer.get('solution','')),
                      'tipo_resposta':kind,'codigo_fonte':exercise['id'],
                      'dados_dinamicos':{**dynamic,'source_exercise_id':exercise['id']}})
        question.opcoes.all().delete()
        if kind=='choice':
            choices=answer.get('choices',answer.get('options',[]))
            Opcao.objects.bulk_create([Opcao(questao=question,texto=label,e_correta=(i==answer['correct']),ordem=i+1) for i,label in enumerate(choices)])
    return {**summary,'materia_id':materia.pk,'disciplina_id':disciplina.pk,'modulo_id':modulo.pk,
            'phase_ids':{str(k):v.pk for k,v in phase_objects.items()},'exercise_ids':sorted(expected_ids)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',default=str(Path(__file__).resolve().parents[1]/'modulo2_fisica.json'))
    parser.add_argument('--zip',default=str(Path(__file__).resolve().parents[1]/'modulo2_exercicios.zip'))
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    data=json.loads(Path(args.json).read_text(encoding='utf-8'))
    summary=validate_source(data)
    if Path(args.zip).is_file():
        summary['zip_validation']=validate_zip_archive(args.zip,data['exercises'])
    if args.dry_run:
        print(json.dumps({'status':'dry_run_ok',**summary},ensure_ascii=False,indent=2));return
    result=import_module(data)
    print(json.dumps({'status':'success',**result},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
