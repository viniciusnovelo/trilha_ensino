#!/usr/bin/env python3
"""Importa os dados-fonte oficiais do Módulo 1 de Física para os models Django."""
from __future__ import annotations
import json
from pathlib import Path
from django.db import transaction
from curriculo.models import Materia, Disciplina, Modulo, Fase, Questao, Opcao
from curriculo.physics_source import validate_source


def import_module(data: dict) -> dict:
    summary = validate_source(data)
    from curriculo.physics_game_import import import_physics_game
    return import_physics_game(data, 1, summary)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))