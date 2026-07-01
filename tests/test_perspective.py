import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perspective_guide_tool import (
    ArchitecturePerspectiveGuidePlugin,
    PerspectiveGuideConfig,
    PerspectiveGuideController,
    build_perspective_guides,
    project_point,
    rotate_point,
)


class PerspectiveGuideToolTests(unittest.TestCase):
    def test_project_point_returns_expected_screen_location(self) -> None:
        point = project_point((100, 80), (0, 0), (300, 0), 120)
        self.assertAlmostEqual(point[0], 200.0)
        self.assertEqual(point[1], 120)

    def test_build_perspective_guides_generates_expected_segments(self) -> None:
        rect = ((40, 60), (140, 60), (140, 140), (40, 140))
        guides = build_perspective_guides(rect, (0, 120), (300, 120), 4)

        self.assertEqual(len(guides), 4)
        self.assertEqual(guides[0][0], (40, 60))
        self.assertAlmostEqual(guides[0][1][0], 75.0)
        self.assertEqual(guides[-1][0], (40, 140))

    def test_plugin_generates_guides_for_animation_purposes(self) -> None:
        plugin = ArchitecturePerspectiveGuidePlugin()
        shape = ((40, 60), (140, 60), (140, 140), (40, 140))
        config = PerspectiveGuideConfig(horizon_y=120, vanishing_x=300, depth_steps=3)
        guides = plugin.generate_guides(shape, config)

        self.assertEqual(len(guides), 3)
        self.assertEqual(guides[0][0], (40, 60))

    def test_rotate_point_supports_angle_adjustment(self) -> None:
        rotated = rotate_point((100, 0), 90.0, (0, 0))
        self.assertAlmostEqual(rotated[0], 0.0)
        self.assertAlmostEqual(rotated[1], 100.0)

    def test_controller_preview_summary_contains_key_settings(self) -> None:
        controller = PerspectiveGuideController()
        shape = ((40, 60), (140, 60), (140, 140), (40, 140))
        config = PerspectiveGuideConfig(horizon_y=120, vanishing_x=300, depth_steps=3, angle_degrees=25.0)
        summary = controller.preview_summary(shape, config)

        self.assertIn("horizon", summary.lower())
        self.assertIn("25", summary)
        self.assertIn("3", summary)

    def test_controller_builds_config_from_ui_values(self) -> None:
        controller = PerspectiveGuideController()
        config = controller.build_config(horizon_y=140, vanishing_x=320, angle_degrees=-15, depth_steps=5, guide_color="#ff0000")

        self.assertEqual(config.horizon_y, 140)
        self.assertEqual(config.vanishing_x, 320)
        self.assertEqual(config.angle_degrees, -15)
        self.assertEqual(config.depth_steps, 5)
        self.assertEqual(config.guide_color, "#ff0000")

    def test_controller_renders_panel_controls(self) -> None:
        controller = PerspectiveGuideController()
        controls = controller.build_controls()

        self.assertIn("horizon", controls)
        self.assertIn("vanishing", controls)
        self.assertIn("angle", controls)
        self.assertIn("depth", controls)

    def test_controller_exports_guide_payload(self) -> None:
        controller = PerspectiveGuideController()
        shape = ((40, 60), (140, 60), (140, 140), (40, 140))
        config = PerspectiveGuideConfig(horizon_y=120, vanishing_x=300, depth_steps=3, angle_degrees=10.0)
        payload = controller.export_guides(shape, config)

        self.assertEqual(payload["guide_count"], 3)
        self.assertEqual(payload["config"]["horizon_y"], 120)
        self.assertEqual(payload["config"]["angle_degrees"], 10.0)

    def test_controller_saves_and_loads_json_presets(self) -> None:
        controller = PerspectiveGuideController()
        config = PerspectiveGuideConfig(horizon_y=140, vanishing_x=320, depth_steps=5, angle_degrees=-20.0, guide_color="#00ff00")
        path = Path(__file__).resolve().parent / "tmp_preset.json"
        controller.save_preset(config, path)
        loaded = controller.load_preset(path)

        self.assertEqual(loaded.horizon_y, 140)
        self.assertEqual(loaded.vanishing_x, 320)
        self.assertEqual(loaded.angle_degrees, -20.0)
        self.assertEqual(loaded.guide_color, "#00ff00")
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
