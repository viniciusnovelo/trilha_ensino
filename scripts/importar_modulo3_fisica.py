#!/usr/bin/env python3
"""Importa o Módulo 3 sem apagar o banco nem alterar os Módulos 1 e 2."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from curriculo.physics_module3_source import validate_source, validate_zip_archive


def import_module(data: dict) -> dict:
    """Importa o conteúdo oficial como o jogo Física 3."""
    summary = validate_source(data)
    from curriculo.physics_game_import import import_physics_game
    return import_physics_game(data, 3, summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', default=str(PROJECT_ROOT / 'modulo3_fisica.json'),
                        help='Caminho para o JSON oficial do Módulo 3.')
    parser.add_argument('--zip', default=None,
                        help='Opcional: ZIP oficial do Módulo 3 com os exercícios individuais para comparação.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Valida JSON e ZIP sem inicializar Django ou modificar o banco.')
    args = parser.parse_args()

    data = json.loads(Path(args.json).read_text(encoding='utf-8'))
    summary = validate_source(data)
    if args.zip:
        zip_path = Path(args.zip)
        if not zip_path.is_file():
            parser.error(f'ZIP informado não encontrado: {zip_path}')
        summary['zip_validation'] = validate_zip_archive(zip_path, data['exercises'])
    if args.dry_run:
        print(json.dumps({'status': 'dry_run_ok', **summary}, ensure_ascii=False, indent=2))
        return
    result = import_module(data)
    print(json.dumps({'status': 'success', **result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
