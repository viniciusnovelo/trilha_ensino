#!/usr/bin/env python3
"""Reset local do SQLite e importação validada do Módulo 1 de Física.

Execute a partir de qualquer diretório: python scripts/reset_e_importar_fisica.py
O banco afetado é exclusivamente <raiz-do-projeto>/db.sqlite3.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_JSON = ROOT / 'fisica_reset_resultado.json'
REPORT_TXT = ROOT / 'fisica_reset_resultado.txt'


def say(message): print(message, flush=True)

def locate(explicit, filename, source_dir=None):
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute(): candidate = (Path.cwd() / candidate).resolve()
        if not candidate.is_file(): raise FileNotFoundError(f"arquivo informado não encontrado: {candidate}")
        return candidate
    candidates = []
    if source_dir: candidates.append(Path(source_dir).expanduser())
    candidates += [ROOT, ROOT / 'source', Path('/mnt/data'), Path('/mnt/data/source')]
    for directory in candidates:
        candidate = directory / filename
        if candidate.is_file(): return candidate.resolve()
    raise FileNotFoundError(f"não encontrei {filename}; use --{ 'json' if filename.endswith('.json') else 'zip' } caminho")


def check_models():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from curriculo.models import Questao
    from gamificacao.models import RespostaTentativa
    required_q = {'tipo_resposta', 'dados_dinamicos', 'codigo_fonte'}
    required_r = {'tipo_resposta_snapshot', 'resposta_snapshot', 'resposta_correta_snapshot', 'parametros_snapshot', 'feedback_snapshot'}
    missing_q = required_q - {f.name for f in Questao._meta.fields}
    missing_r = required_r - {f.name for f in RespostaTentativa._meta.fields}
    if missing_q or missing_r:
        raise RuntimeError(f"modelagem dinâmica incompleta: Questao={sorted(missing_q)}, RespostaTentativa={sorted(missing_r)}")
    from django.conf import settings
    configured = Path(settings.DATABASES['default']['NAME']).resolve()
    expected = (ROOT / 'db.sqlite3').resolve()
    if configured != expected:
        raise RuntimeError(f"banco configurado não é o db.sqlite3 da raiz: {configured}")


def write_report(report):
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [
        'RELATÓRIO — RESET E IMPORTAÇÃO DO MÓDULO 1 DE FÍSICA',
        f"Data/hora UTC: {report['timestamp_utc']}",
        f"Status: {report['status']}",
        f"Banco recriado: {report.get('database_recreated', False)}",
        f"Migrations executadas: {report.get('migrations_executed', False)}",
        f"Fases: {report.get('phases', 0)}",
        f"Questões: {report.get('questions', 0)}",
        f"Numeric: {report.get('numeric', 0)}",
        f"Choice: {report.get('choice', 0)}",
        f"Alternativas: {report.get('options', 0)}",
        f"Cenas distintas: {report.get('scenes', 0)}",
        f"Fórmulas validadas: {report.get('formulas', 0)}",
        f"Exercícios validados: {report.get('exercises_validated', 0)}",
        f"Erros: {json.dumps(report.get('errors', []), ensure_ascii=False)}",
    ]
    REPORT_TXT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', dest='json_path')
    parser.add_argument('--zip', dest='zip_path')
    parser.add_argument('--source-dir', help='diretório adicional para localizar as fontes')
    parser.add_argument('--dry-run', action='store_true', help='valida fontes e ambiente sem apagar/criar banco')
    args = parser.parse_args()
    report = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'status': 'failed', 'errors': [],
              'database': str(ROOT / 'db.sqlite3'), 'database_deleted': False, 'database_recreated': False, 'migrations_executed': False}
    try:
        say('[1/8] Validando ambiente...')
        if not (ROOT / 'manage.py').is_file(): raise RuntimeError(f"manage.py não encontrado em {ROOT}")
        if not (ROOT / 'curriculo' / 'models.py').is_file(): raise RuntimeError('app curriculo não encontrada')
        sys.path.insert(0, str(ROOT))
        check_models()
        say('OK')

        say('[2/8] Localizando e validando modulo1_fisica.json...')
        json_file = locate(args.json_path, 'modulo1_fisica.json', args.source_dir)
        zip_file = locate(args.zip_path, 'exercicios.zip', args.source_dir)
        for required_name in ('index.html', 'build_assets.py'):
            candidates = [ROOT / required_name, ROOT / 'source' / required_name]
            if args.source_dir:
                candidates.insert(0, Path(args.source_dir).expanduser() / required_name)
            if not any(candidate.is_file() for candidate in candidates):
                raise FileNotFoundError(f'fonte obrigatória ausente: {required_name}')
        data = json.loads(json_file.read_text(encoding='utf-8'))
        from curriculo.physics_source import validate_source, validate_zip_archive
        summary = validate_source(data)
        report.update({'source_json': str(json_file), 'source_zip': str(zip_file), 'phases': summary['phases'],
                       'exercises_validated': summary['exercises'], 'questions': summary['exercises'], 'options': summary['types']['choice'] * 3, 'numeric': summary['types']['numeric'],
                       'choice': summary['types']['choice'], 'scenes': len(summary['scenes']),
                       'formulas': len(summary['formulas']), 'scene_ids': summary['scenes'], 'formula_ids': summary['formulas']})
        say(f"OK — {summary['phases']} fases / {summary['exercises']} exercícios / 21 numeric / 7 choice")

        say('[3/8] Validando exercicios.zip...')
        zip_summary = validate_zip_archive(zip_file, data['exercises'])
        report['zip_validation'] = zip_summary
        say('OK — 28 arquivos / 0 divergências')

        if args.dry_run:
            report['status'] = 'dry_run_ok'
            say('[4/8] Resetando banco... IGNORADO (--dry-run)')
            say('[5/8] Executando migrations... IGNORADO (--dry-run)')
            say('[6/8] Importando Módulo 1... IGNORADO (--dry-run)')
            say('[7/8] Validando banco... IGNORADO (--dry-run)')
            say('[8/8] Gerando relatório...')
            write_report(report); say('OK — dry-run concluído; nenhum banco foi alterado.')
            return 0

        say('[4/8] Resetando banco...')
        say('ATENÇÃO: o banco db.sqlite3 da raiz será apagado integralmente. Todos os dados existentes serão perdidos.')
        db_path = ROOT / 'db.sqlite3'
        for candidate in (db_path, ROOT / 'db.sqlite3-wal', ROOT / 'db.sqlite3-shm'):
            if candidate.exists(): candidate.unlink()
        report['database_deleted'] = True
        say('OK — banco antigo removido (se existia)')

        say('[5/8] Executando migrations...')
        subprocess.run([sys.executable, str(ROOT / 'manage.py'), 'migrate', '--noinput'], cwd=ROOT, check=True)
        report['migrations_executed'] = True
        report['database_recreated'] = True
        say('OK')

        say('[6/8] Importando Módulo 1 de Física...')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        from scripts.importar_modulo1_fisica import import_module
        imported = import_module(data)
        report['import'] = imported
        say('OK')

        say('[7/8] Validando banco...')
        from django.db import models
        from curriculo.models import Fase, Questao, Opcao, Materia, Disciplina, Modulo
        phase_qs = Fase.objects.filter(modulo_id=imported['modulo_id'])
        question_qs = Questao.objects.filter(fase__in=phase_qs)
        numeric = question_qs.filter(tipo_resposta='numeric').count()
        choice = question_qs.filter(tipo_resposta='choice').count()
        options = Opcao.objects.filter(questao__in=question_qs).count()
        phase_counts = {f.titulo: f.questoes.count() for f in phase_qs}
        actual_ids = set(question_qs.values_list('codigo_fonte', flat=True))
        expected_ids = {e['id'] for e in data['exercises']}
        matter_count = Materia.objects.filter(slug='fisica').count()
        discipline_count = Disciplina.objects.filter(slug='fisica').count()
        module_count = Modulo.objects.filter(pk=imported['modulo_id']).count()
        if (matter_count, discipline_count, module_count) != (1, 1, 1):
            raise RuntimeError(f'estrutura curricular divergente: matérias={matter_count}, disciplinas={discipline_count}, módulos={module_count}')
        if (phase_qs.count(), question_qs.count(), numeric, choice) != (4, 28, 21, 7):
            raise RuntimeError(f"contagens divergentes: fases={phase_qs.count()}, questões={question_qs.count()}, numeric={numeric}, choice={choice}")
        if actual_ids != expected_ids: raise RuntimeError('IDs importados não correspondem aos 28 IDs da fonte')
        if phase_counts != {'Cinemática': 6, 'Dinâmica': 6, 'Trabalho, Energia e Potência': 8, 'Gravitação Universal': 8}:
            raise RuntimeError(f"distribuição por fase divergente: {phase_counts}")
        if question_qs.filter(tipo_resposta='numeric', opcoes__isnull=False).exists(): raise RuntimeError('questão numeric possui alternativa')
        if question_qs.filter(tipo_resposta='choice').annotate(n=models.Count('opcoes')).filter(n=0).exists(): raise RuntimeError('questão choice sem alternativa')
        if question_qs.filter(tipo_resposta='choice').annotate(n=models.Count('opcoes')).exclude(n=3).exists(): raise RuntimeError('questão choice não possui exatamente 3 alternativas')
        report.update({'materias': matter_count, 'disciplinas': discipline_count, 'modulos': module_count, 'questions': question_qs.count(), 'options': options, 'phase_distribution': phase_counts,
                       'validated_ids': sorted(actual_ids), 'status': 'success'})
        say('OK — 4 fases / 28 questões / 21 numeric / 7 choice')

        say('[8/8] Gerando relatório...')
        write_report(report); say('OK')
        say('MÓDULO 1 DE FÍSICA IMPORTADO COM SUCESSO.')
        return 0
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
        report['traceback'] = traceback.format_exc()
        try: write_report(report)
        except Exception: pass
        say(f'ERRO: {type(exc).__name__}: {exc}')
        say(f'Relatórios (se gravados): {REPORT_JSON} / {REPORT_TXT}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())