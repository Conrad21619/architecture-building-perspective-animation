# Architecture Building Perspective Animation Tool

This repository contains a lightweight plugin scaffold for a Krita-style perspective guide tool.

## What it provides
- A simple perspective projection helper for converting points into guide positions.
- A shape-to-guide generator that converts drawn geometry into perspective guide lines.
- Angle-aware preview support for animating building movement from different viewpoints.
- A plugin manifest describing the tool for integration into a host application.

## How the tool works
1. Draw a building outline, window, or any simple shape on the canvas.
2. Feed the shape points into the guide generator.
3. The tool projects those points toward a vanishing direction and can rotate them by an angle for alternate viewpoints.
4. The resulting guides can be used as animation references for movement, rotation, and camera perspective.

## Example usage
```python
from perspective_guide_tool import PerspectiveGuideConfig, ArchitecturePerspectiveGuidePlugin

shape = ((40, 60), (140, 60), (140, 140), (40, 140))
config = PerspectiveGuideConfig(horizon_y=120, vanishing_x=300, depth_steps=4)
plugin = ArchitecturePerspectiveGuidePlugin()
guides = plugin.generate_guides(shape, config)
print(guides)
```

## Verification
Run the tests with:
```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Publishing notes
The repository is structured so it can be published as a simple open-source starter for a Krita perspective-guide workflow. The core logic is isolated in the Python module, making it straightforward to adapt into a full plugin with a visual UI later.