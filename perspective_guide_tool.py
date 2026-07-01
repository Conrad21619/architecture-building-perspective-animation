from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import List, Optional, Sequence, Tuple

Point = Tuple[float, float]
Segment = Tuple[Point, Point]


@dataclass
class PerspectiveGuideConfig:
    horizon_y: float
    vanishing_x: float
    depth_steps: int = 4
    angle_degrees: float = 0.0
    guide_color: str = "#4f46e5"


def interpolate_point(start: Point, end: Point, t: float) -> Point:
    return (
        start[0] + (end[0] - start[0]) * t,
        start[1] + (end[1] - start[1]) * t,
    )


def rotate_point(point: Point, angle_degrees: float, origin: Point = (0, 0)) -> Point:
    angle = radians(angle_degrees)
    x, y = point
    ox, oy = origin
    dx = x - ox
    dy = y - oy
    return (
        ox + dx * cos(angle) - dy * sin(angle),
        oy + dx * sin(angle) + dy * cos(angle),
    )


def project_point(point: Point, origin: Point, vanishing_point: Point, horizon_y: float) -> Point:
    """Project a 2D point into a simple perspective guide by anchoring it to the horizon."""
    x, y = point
    ox, oy = origin
    vx, vy = vanishing_point

    if abs(vx - ox) < 1e-6:
        return (x, horizon_y)

    scale = (horizon_y - y) / max(1e-6, horizon_y - oy)
    projected_x = x + (vx - ox) * scale
    projected_y = horizon_y
    return (projected_x, projected_y)


def build_perspective_guides(shape_points: Sequence[Point], origin: Point, vanishing_point: Point, depth_steps: int) -> List[Segment]:
    """Create guide segments that connect a shape to a vanishing point across a number of depth steps."""
    if depth_steps <= 0:
        return []

    guides: List[Segment] = []
    points = list(shape_points)
    if not points:
        return guides

    guide_count = min(len(points), max(1, depth_steps))
    for index in range(guide_count):
        start = points[index]
        t = (index + 1) / max(guide_count, 1)
        end = interpolate_point(origin, vanishing_point, t)
        guides.append((start, end))
    return guides


def create_animation_guides(shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> List[Segment]:
    """Create a simple set of perspective guides for animation planning."""
    rotated_points = [
        rotate_point(point, config.angle_degrees)
        for point in shape_points
    ]
    return build_perspective_guides(
        rotated_points,
        (0, config.horizon_y),
        (config.vanishing_x, config.horizon_y),
        config.depth_steps,
    )


class ArchitecturePerspectiveGuidePlugin:
    """A lightweight plugin shell that can be adapted into a Krita action."""

    def __init__(self, document: Optional[object] = None) -> None:
        self.document = document

    def generate_guides(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> List[Segment]:
        return create_animation_guides(shape_points, config)

    def preview(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> List[Segment]:
        return self.generate_guides(shape_points, config)


class PerspectiveGuideController:
    """A simple controller for previewing and describing guide settings."""

    def preview_summary(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> str:
        guides = create_animation_guides(shape_points, config)
        return (
            f"Perspective preview: horizon={config.horizon_y}, vanishing={config.vanishing_x}, "
            f"angle={config.angle_degrees}, steps={config.depth_steps}, guides={len(guides)}"
        )
