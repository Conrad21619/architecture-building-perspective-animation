import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perspective_guide_tool import ArchitecturePerspectiveGuidePlugin, PerspectiveGuideConfig, build_perspective_guides, project_point


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


if __name__ == "__main__":
    unittest.main()
