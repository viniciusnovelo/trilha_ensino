"""Testes de integração do renderer visual do Módulo 3."""
import json
import re
from pathlib import Path

from django.test import SimpleTestCase

from .physics_scenes import SCENE_METADATA


class PhysicsModule3RendererTests(SimpleTestCase):
    def test_all_module3_scenes_have_original_canvas_renderers(self):
        template_path = (
            Path(__file__).parent
            / "templates"
            / "curriculo"
            / "physics_player.html"
        )
        template = template_path.read_text(encoding="utf-8")
        expected = {
            scene
            for scene, metadata in SCENE_METADATA.items()
            if metadata["kind"] == "module3"
        }

        declaration = template.split("const MODULE3_SCENES=new Set(", 1)[1]
        scene_json = declaration.split(");", 1)[0]
        self.assertSetEqual(expected, set(json.loads(scene_json)))

        renderer_start = template.index("function drawModule3Scene(e)")
        renderer_end = template.index("function drawScene(e)", renderer_start)
        renderer = template[renderer_start:renderer_end]
        rendered_cases = set(
            re.findall(r"""\bcase\s*['"]([^'"]+)['"]""", renderer)
        )
        self.assertSetEqual(expected, rendered_cases)

    def test_module3_dispatch_does_not_intercept_module1_or_module2(self):
        template_path = (
            Path(__file__).parent
            / "templates"
            / "curriculo"
            / "physics_player.html"
        )
        template = template_path.read_text(encoding="utf-8")
        module3_dispatch = template.index(
            "if(MODULE3_SCENES.has(e.simulation.scene))"
        )
        module2_dispatch = template.index(
            "if(MODULE2_SCENES.has(e.simulation.scene))"
        )
        self.assertLess(module3_dispatch, module2_dispatch)
