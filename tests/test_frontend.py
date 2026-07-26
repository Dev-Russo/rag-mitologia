import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FrontendGraphTests(unittest.TestCase):
    def test_svg_visibility_is_controlled_through_its_attribute(self) -> None:
        script = (PROJECT_ROOT / "static" / "graph.js").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'elements.svg.toggleAttribute("hidden", state.nodes.size === 0)',
            script,
        )
        self.assertNotIn("elements.svg.hidden =", script)

    def test_graph_script_has_cache_version(self) -> None:
        template = (PROJECT_ROOT / "templates" / "index.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("graph.js') }}?v=2", template)


if __name__ == "__main__":
    unittest.main()
