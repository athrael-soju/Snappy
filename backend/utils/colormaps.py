"""
ColorBrewer-style colormaps implemented in pure numpy.

Provides the same color scales available in the frontend (via chroma-js)
for consistent visualization between frontend and backend.
"""

from enum import Enum
from typing import Tuple

import numpy as np


class ColorScale(str, Enum):
    """Available color scales (matching frontend chroma-js ColorBrewer scales)."""

    # Diverging scales (for comparing high/low)
    SPECTRAL = "Spectral"  # Multi-hue diverging
    RDYLBU = "RdYlBu"  # Red-Yellow-Blue diverging
    RDBU = "RdBu"  # Red-Blue diverging

    # Sequential scales (for intensity)
    YLORRD = "YlOrRd"  # Yellow-Orange-Red
    YLGNBU = "YlGnBu"  # Yellow-Green-Blue
    REDS = "Reds"  # White to red
    BLUES = "Blues"  # White to blue
    ORANGES = "Oranges"  # White to orange
    PURPLES = "Purples"  # White to purple


# ColorBrewer color definitions (9-class versions)
# Each scale is defined as a list of RGB tuples from low to high
_COLORBREWER_SCALES = {
    # Diverging scales
    ColorScale.SPECTRAL: [
        (158, 1, 66),
        (213, 62, 79),
        (244, 109, 67),
        (253, 174, 97),
        (254, 224, 139),
        (255, 255, 191),
        (230, 245, 152),
        (171, 221, 164),
        (102, 194, 165),
        (50, 136, 189),
        (94, 79, 162),
    ],
    ColorScale.RDYLBU: [
        (165, 0, 38),
        (215, 48, 39),
        (244, 109, 67),
        (253, 174, 97),
        (254, 224, 144),
        (255, 255, 191),
        (224, 243, 248),
        (171, 217, 233),
        (116, 173, 209),
        (69, 117, 180),
        (49, 54, 149),
    ],
    ColorScale.RDBU: [
        (103, 0, 31),
        (178, 24, 43),
        (214, 96, 77),
        (244, 165, 130),
        (253, 219, 199),
        (247, 247, 247),
        (209, 229, 240),
        (146, 197, 222),
        (67, 147, 195),
        (33, 102, 172),
        (5, 48, 97),
    ],
    # Sequential scales
    ColorScale.YLORRD: [
        (255, 255, 204),
        (255, 237, 160),
        (254, 217, 118),
        (254, 178, 76),
        (253, 141, 60),
        (252, 78, 42),
        (227, 26, 28),
        (189, 0, 38),
        (128, 0, 38),
    ],
    ColorScale.YLGNBU: [
        (255, 255, 217),
        (237, 248, 177),
        (199, 233, 180),
        (127, 205, 187),
        (65, 182, 196),
        (29, 145, 192),
        (34, 94, 168),
        (37, 52, 148),
        (8, 29, 88),
    ],
    ColorScale.REDS: [
        (255, 245, 240),
        (254, 224, 210),
        (252, 187, 161),
        (252, 146, 114),
        (251, 106, 74),
        (239, 59, 44),
        (203, 24, 29),
        (165, 15, 21),
        (103, 0, 13),
    ],
    ColorScale.BLUES: [
        (247, 251, 255),
        (222, 235, 247),
        (198, 219, 239),
        (158, 202, 225),
        (107, 174, 214),
        (66, 146, 198),
        (33, 113, 181),
        (8, 81, 156),
        (8, 48, 107),
    ],
    ColorScale.ORANGES: [
        (255, 245, 235),
        (254, 230, 206),
        (253, 208, 162),
        (253, 174, 107),
        (253, 141, 60),
        (241, 105, 19),
        (217, 72, 1),
        (166, 54, 3),
        (127, 39, 4),
    ],
    ColorScale.PURPLES: [
        (252, 251, 253),
        (239, 237, 245),
        (218, 218, 235),
        (188, 189, 220),
        (158, 154, 200),
        (128, 125, 186),
        (106, 81, 163),
        (84, 39, 143),
        (63, 0, 125),
    ],
}


def _interpolate_color(
    colors: list, t: float
) -> Tuple[int, int, int]:
    """
    Interpolate between colors in a color scale.

    Args:
        colors: List of RGB tuples defining the color scale
        t: Value in [0, 1] to interpolate

    Returns:
        RGB tuple (r, g, b) with values in [0, 255]
    """
    t = np.clip(t, 0.0, 1.0)

    n = len(colors) - 1
    idx = t * n
    lower_idx = int(np.floor(idx))
    upper_idx = min(lower_idx + 1, n)

    # Fractional part for interpolation
    frac = idx - lower_idx

    c1 = colors[lower_idx]
    c2 = colors[upper_idx]

    r = int(c1[0] + frac * (c2[0] - c1[0]))
    g = int(c1[1] + frac * (c2[1] - c1[1]))
    b = int(c1[2] + frac * (c2[2] - c1[2]))

    return (r, g, b)


def get_color(
    value: float, scale: ColorScale = ColorScale.YLORRD
) -> Tuple[int, int, int]:
    """
    Get RGB color for a normalized value using the specified color scale.

    Args:
        value: Normalized value in [0, 1]
        scale: Color scale to use

    Returns:
        RGB tuple (r, g, b) with values in [0, 255]
    """
    colors = _COLORBREWER_SCALES.get(scale, _COLORBREWER_SCALES[ColorScale.YLORRD])
    return _interpolate_color(colors, value)


def apply_colormap(
    values: np.ndarray,
    scale: ColorScale = ColorScale.YLORRD,
) -> np.ndarray:
    """
    Apply a colormap to a 2D array of normalized values.

    Args:
        values: 2D array of normalized values in [0, 1]
        scale: Color scale to use

    Returns:
        3D array of shape (H, W, 3) with RGB values in [0, 255]
    """
    colors = _COLORBREWER_SCALES.get(scale, _COLORBREWER_SCALES[ColorScale.YLORRD])
    colors_array = np.array(colors, dtype=np.float32)
    n_colors = len(colors)

    # Ensure values are clipped to [0, 1]
    values = np.clip(values, 0.0, 1.0)

    # Calculate interpolation indices
    indices = values * (n_colors - 1)
    lower_indices = np.floor(indices).astype(int)
    upper_indices = np.minimum(lower_indices + 1, n_colors - 1)
    fracs = (indices - lower_indices)[..., np.newaxis]

    # Interpolate colors
    lower_colors = colors_array[lower_indices]
    upper_colors = colors_array[upper_indices]
    rgb = lower_colors + fracs * (upper_colors - lower_colors)

    return rgb.astype(np.uint8)


def create_heatmap_rgba(
    values: np.ndarray,
    scale: ColorScale = ColorScale.YLORRD,
    alpha: int = 180,
) -> np.ndarray:
    """
    Create an RGBA heatmap array from normalized values.

    Args:
        values: 2D array of normalized values in [0, 1]
        scale: Color scale to use
        alpha: Alpha channel value (0-255)

    Returns:
        4D array of shape (H, W, 4) with RGBA values in [0, 255]
    """
    rgb = apply_colormap(values, scale)
    h, w = values.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = alpha
    return rgba


def get_scale_label(scale: ColorScale) -> str:
    """Get display name for color scale."""
    labels = {
        ColorScale.SPECTRAL: "Spectral (Diverging)",
        ColorScale.RDYLBU: "Red-Yellow-Blue (Diverging)",
        ColorScale.RDBU: "Red-Blue (Diverging)",
        ColorScale.YLORRD: "Yellow-Orange-Red",
        ColorScale.YLGNBU: "Yellow-Green-Blue",
        ColorScale.REDS: "Reds",
        ColorScale.BLUES: "Blues",
        ColorScale.ORANGES: "Oranges",
        ColorScale.PURPLES: "Purples",
    }
    return labels.get(scale, str(scale))
