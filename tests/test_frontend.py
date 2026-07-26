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

    def test_graph_assets_have_current_cache_version(self) -> None:
        template = (PROJECT_ROOT / "templates" / "index.html").read_text(
            encoding="utf-8"
        )

        self.assertIn("graph.js') }}?v=3", template)
        self.assertIn("style.css') }}?v=4", template)

    def test_graph_uses_horizontal_levels_without_edge_labels(self) -> None:
        script = (PROJECT_ROOT / "static" / "graph.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("x: paddingX + level * columnGap", script)
        self.assertNotIn('class: "graph-edge-label"', script)
        self.assertNotIn("label.textContent = edge.relation", script)

    def test_node_label_is_added_only_when_selected(self) -> None:
        script = (PROJECT_ROOT / "static" / "graph.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("if (selected) addSelectedLabel(group, node.label)", script)

    def test_graph_exposes_navigation_controls(self) -> None:
        template = (PROJECT_ROOT / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        script = (PROJECT_ROOT / "static" / "graph.js").read_text(
            encoding="utf-8"
        )

        for control_id in ("zoom-out", "fit-graph", "zoom-in"):
            self.assertIn(f'id="{control_id}"', template)
        self.assertIn('elements.svg.addEventListener("pointerdown"', script)
        self.assertIn('"wheel"', script)

    def test_theme_uses_greek_palette_and_title_font(self) -> None:
        template = (PROJECT_ROOT / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        stylesheet = (PROJECT_ROOT / "static" / "style.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("family=Forum", template)
        self.assertIn("--aegean-900", stylesheet)
        self.assertIn("--marble", stylesheet)
        self.assertIn("--gold", stylesheet)

    def test_desktop_layout_stays_inside_viewport(self) -> None:
        stylesheet = (PROJECT_ROOT / "static" / "style.css").read_text(
            encoding="utf-8"
        )

        self.assertIn("height: 100dvh", stylesheet)
        self.assertIn("height: calc(100dvh - 5.25rem)", stylesheet)
        self.assertIn("overflow: hidden", stylesheet)
        self.assertIn("overflow-y: auto", stylesheet)
        self.assertIn("@media (max-width: 900px)", stylesheet)


if __name__ == "__main__":
    unittest.main()
