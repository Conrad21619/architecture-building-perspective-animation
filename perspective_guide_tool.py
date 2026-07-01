from __future__ import annotations

import json
from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

try:
    from tkinter import Canvas, DoubleVar, IntVar, Label, Scale, StringVar, Tk, ttk
except ImportError:  # pragma: no cover - tkinter may be unavailable in headless environments
    Canvas = DoubleVar = IntVar = Label = Scale = StringVar = Tk = ttk = None

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

    def build_controls(self) -> List[str]:
        return ["horizon", "vanishing", "angle", "depth", "color"]

    def build_config(
        self,
        horizon_y: float,
        vanishing_x: float,
        angle_degrees: float,
        depth_steps: int,
        guide_color: str,
    ) -> PerspectiveGuideConfig:
        return PerspectiveGuideConfig(
            horizon_y=horizon_y,
            vanishing_x=vanishing_x,
            angle_degrees=angle_degrees,
            depth_steps=depth_steps,
            guide_color=guide_color,
        )

    def preview_summary(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> str:
        guides = create_animation_guides(shape_points, config)
        return (
            f"Perspective preview: horizon={config.horizon_y}, vanishing={config.vanishing_x}, "
            f"angle={config.angle_degrees}, steps={config.depth_steps}, guides={len(guides)}"
        )

    def save_preset(self, config: PerspectiveGuideConfig, path: Path | str) -> None:
        target = Path(path)
        payload = {
            "horizon_y": config.horizon_y,
            "vanishing_x": config.vanishing_x,
            "angle_degrees": config.angle_degrees,
            "depth_steps": config.depth_steps,
            "guide_color": config.guide_color,
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_preset(self, path: Path | str) -> PerspectiveGuideConfig:
        target = Path(path)
        payload = json.loads(target.read_text(encoding="utf-8"))
        return PerspectiveGuideConfig(
            horizon_y=payload["horizon_y"],
            vanishing_x=payload["vanishing_x"],
            angle_degrees=payload["angle_degrees"],
            depth_steps=payload["depth_steps"],
            guide_color=payload.get("guide_color", "#4f46e5"),
        )

    def export_guides(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> dict:
        guides = create_animation_guides(shape_points, config)
        return {
            "guide_count": len(guides),
            "guides": guides,
            "config": {
                "horizon_y": config.horizon_y,
                "vanishing_x": config.vanishing_x,
                "angle_degrees": config.angle_degrees,
                "depth_steps": config.depth_steps,
                "guide_color": config.guide_color,
            },
        }

    def preview_window(self, shape_points: Sequence[Point], config: PerspectiveGuideConfig) -> Optional[object]:
        if Tk is None or ttk is None or Canvas is None or Label is None or Scale is None or StringVar is None:
            return None

        root = Tk()
        root.title("Architecture Perspective Preview")
        root.geometry("820x520")

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        controls_frame = ttk.LabelFrame(frame, text="Controls", padding=10)
        controls_frame.pack(fill="x", pady=(0, 10))

        horizon_var = DoubleVar(value=float(config.horizon_y))
        vanishing_var = DoubleVar(value=float(config.vanishing_x))
        angle_var = DoubleVar(value=float(config.angle_degrees))
        depth_var = IntVar(value=int(config.depth_steps))
        color_var = StringVar(value=config.guide_color)

        def update_preview() -> None:
            current_config = self.build_config(
                horizon_y=horizon_var.get(),
                vanishing_x=vanishing_var.get(),
                angle_degrees=angle_var.get(),
                depth_steps=depth_var.get(),
                guide_color=color_var.get(),
            )
            canvas.delete("all")
            guides = create_animation_guides(shape_points, current_config)
            for index, (start, end) in enumerate(guides):
                canvas.create_line(start[0], start[1], end[0], end[1], fill=current_config.guide_color, width=2 + index % 2)
            info.config(text=self.preview_summary(shape_points, current_config))

        ttk.Label(controls_frame, text="Horizon").grid(row=0, column=0, sticky="w")
        ttk.Scale(controls_frame, from_=0, to=400, orient="horizontal", variable=horizon_var, command=lambda _value: update_preview()).grid(row=0, column=1, sticky="ew")

        ttk.Label(controls_frame, text="Vanishing").grid(row=1, column=0, sticky="w")
        ttk.Scale(controls_frame, from_=0, to=800, orient="horizontal", variable=vanishing_var, command=lambda _value: update_preview()).grid(row=1, column=1, sticky="ew")

        ttk.Label(controls_frame, text="Angle").grid(row=2, column=0, sticky="w")
        ttk.Scale(controls_frame, from_=-90, to=90, orient="horizontal", variable=angle_var, command=lambda _value: update_preview()).grid(row=2, column=1, sticky="ew")

        ttk.Label(controls_frame, text="Depth").grid(row=3, column=0, sticky="w")
        ttk.Scale(controls_frame, from_=1, to=10, orient="horizontal", variable=depth_var, command=lambda _value: update_preview()).grid(row=3, column=1, sticky="ew")

        ttk.Label(controls_frame, text="Color").grid(row=4, column=0, sticky="w")
        ttk.Entry(controls_frame, textvariable=color_var).grid(row=4, column=1, sticky="ew")
        ttk.Button(controls_frame, text="Refresh", command=update_preview).grid(row=5, column=0, sticky="w", pady=(6, 0))
        ttk.Button(
            controls_frame,
            text="Apply to canvas",
            command=lambda: self.export_guides(shape_points, self.build_config(
                horizon_y=horizon_var.get(),
                vanishing_x=vanishing_var.get(),
                angle_degrees=angle_var.get(),
                depth_steps=depth_var.get(),
                guide_color=color_var.get(),
            )),
        ).grid(row=5, column=1, sticky="e", pady=(6, 0))

        canvas = Canvas(frame, width=720, height=320, bg="white")
        canvas.pack(fill="both", expand=True)

        info = Label(frame, text=self.preview_summary(shape_points, config), anchor="w")
        info.pack(fill="x", pady=(8, 0))
        update_preview()
        return root
