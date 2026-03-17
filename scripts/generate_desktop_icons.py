#!/usr/bin/env python3
from __future__ import annotations

import math
import shutil
import struct
import subprocess
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "desktop" / "src-tauri" / "icons"
ICONSET_DIR = ICONS_DIR / "icon.iconset"

PNG_OUTPUTS = {
    "16x16.png": 16,
    "32x32.png": 32,
    "48x48.png": 48,
    "64x64.png": 64,
    "128x128.png": 128,
    "128x128@2x.png": 256,
    "256x256.png": 256,
    "512x512.png": 512,
    "1024x1024.png": 1024,
}

ICONSET_OUTPUTS = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix_color(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t))


def circle_distance(x: float, y: float, cx: float, cy: float, radius: float) -> float:
    return math.hypot(x - cx, y - cy) - radius


def ellipse_distance(
    x: float,
    y: float,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    angle_degrees: float,
) -> float:
    angle = math.radians(angle_degrees)
    dx = x - cx
    dy = y - cy
    xr = dx * math.cos(angle) + dy * math.sin(angle)
    yr = -dx * math.sin(angle) + dy * math.cos(angle)
    return (math.sqrt((xr / rx) ** 2 + (yr / ry) ** 2) - 1.0) * min(rx, ry)


def bubble_distance(x: float, y: float) -> float:
    return min(
        circle_distance(x, y, 0.55, 0.43, 0.29),
        circle_distance(x, y, 0.42, 0.56, 0.18),
        ellipse_distance(x, y, 0.29, 0.69, 0.15, 0.09, -34.0),
        circle_distance(x, y, 0.39, 0.63, 0.13),
    )


def blend(
    base_rgb: tuple[float, float, float],
    base_alpha: float,
    overlay_rgb: tuple[float, float, float],
    overlay_alpha: float,
) -> tuple[tuple[float, float, float], float]:
    overlay_alpha = clamp(overlay_alpha)
    out_alpha = overlay_alpha + base_alpha * (1.0 - overlay_alpha)
    if out_alpha <= 0.0:
        return (0.0, 0.0, 0.0), 0.0
    rgb = []
    for index in range(3):
        channel = (
            overlay_rgb[index] * overlay_alpha
            + base_rgb[index] * base_alpha * (1.0 - overlay_alpha)
        ) / out_alpha
        rgb.append(channel)
    return (rgb[0], rgb[1], rgb[2]), out_alpha


def render_icon(size: int) -> bytes:
    pixels = bytearray(size * size * 4)
    deep_blue = (0.05, 0.20, 0.76)
    cyan = (0.40, 0.90, 1.00)
    aqua = (0.62, 0.98, 0.95)
    white = (1.0, 1.0, 1.0)

    for py in range(size):
        for px in range(size):
            x = (px + 0.5) / size
            y = (py + 0.5) / size

            rgb = (0.0, 0.0, 0.0)
            alpha = 0.0

            bubble_d = bubble_distance(x, y)
            shadow_d = bubble_distance(x - 0.04, y - 0.05)
            shadow_alpha = smoothstep(0.12, -0.04, shadow_d) * 0.18
            rgb, alpha = blend(rgb, alpha, (0.02, 0.07, 0.15), shadow_alpha)

            outer_glow = smoothstep(0.15, -0.03, bubble_d) * 0.30
            glow_color = mix_color(cyan, aqua, clamp((x + y) * 0.5))
            rgb, alpha = blend(rgb, alpha, glow_color, outer_glow * 0.55)

            bubble_alpha = smoothstep(0.03, -0.03, bubble_d) * 0.88
            if bubble_alpha > 0.0:
                diag = clamp((x * 0.62) + ((1.0 - y) * 0.38))
                base = mix_color(deep_blue, cyan, diag)
                base = mix_color(base, aqua, clamp((0.62 - y) * 1.15))
                rgb, alpha = blend(rgb, alpha, base, bubble_alpha)

                inner_haze = math.exp(-(((x - 0.37) ** 2) / 0.018 + ((y - 0.26) ** 2) / 0.012))
                rgb, alpha = blend(rgb, alpha, white, inner_haze * bubble_alpha * 0.34)

                lower_haze = math.exp(-(((x - 0.67) ** 2) / 0.045 + ((y - 0.66) ** 2) / 0.038))
                rgb, alpha = blend(rgb, alpha, aqua, lower_haze * bubble_alpha * 0.18)

                sheen_line = math.exp(-(((x - (0.27 + y * 0.26)) ** 2) / 0.0016))
                sheen_alpha = sheen_line * smoothstep(0.42, 0.02, y) * bubble_alpha * 0.28
                rgb, alpha = blend(rgb, alpha, white, sheen_alpha)

                rim = smoothstep(0.030, 0.0, abs(bubble_d)) * 0.26
                rgb, alpha = blend(rgb, alpha, white, rim)

            for center_x in (0.42, 0.54, 0.66):
                dot_d = circle_distance(x, y, center_x, 0.47, 0.053)
                dot_alpha = smoothstep(0.018, -0.018, dot_d) * 0.80
                if dot_alpha <= 0.0:
                    continue
                dot_color = mix_color((0.60, 0.95, 1.0), white, 0.58)
                dot_highlight = math.exp(-(((x - (center_x - 0.018)) ** 2) / 0.00055 + ((y - 0.447) ** 2) / 0.00038))
                rgb, alpha = blend(rgb, alpha, dot_color, dot_alpha)
                rgb, alpha = blend(rgb, alpha, white, dot_highlight * dot_alpha * 0.72)

            droplet_d = circle_distance(x, y, 0.77, 0.24, 0.06)
            droplet_alpha = smoothstep(0.016, -0.02, droplet_d) * 0.58
            if droplet_alpha > 0.0:
                droplet_color = mix_color(cyan, white, 0.30)
                rgb, alpha = blend(rgb, alpha, droplet_color, droplet_alpha)

            offset = (py * size + px) * 4
            pixels[offset] = int(clamp(rgb[0]) * 255)
            pixels[offset + 1] = int(clamp(rgb[1]) * 255)
            pixels[offset + 2] = int(clamp(rgb[2]) * 255)
            pixels[offset + 3] = int(clamp(alpha) * 255)

    return bytes(pixels)


def png_bytes(width: int, height: int, rgba: bytes) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack("!I", len(data))
            + kind
            + data
            + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    stride = width * 4
    for row in range(height):
        raw.append(0)
        start = row * stride
        raw.extend(rgba[start : start + stride])

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), level=9))
        + chunk(b"IEND", b"")
    )


def write_png(path: Path, size: int) -> None:
    path.write_bytes(png_bytes(size, size, render_icon(size)))


def write_ico(path: Path, sizes: list[int]) -> None:
    images = [(size, png_bytes(size, size, render_icon(size))) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    directory = bytearray()
    offset = 6 + (16 * len(images))
    payload = bytearray()

    for size, image in images:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(image),
                offset,
            )
        )
        payload.extend(image)
        offset += len(image)

    path.write_bytes(header + directory + payload)


def build_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="glassFill" x1="214" y1="188" x2="760" y2="724" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#90E8FF" stop-opacity="0.92" />
      <stop offset="0.48" stop-color="#59B6FF" stop-opacity="0.82" />
      <stop offset="1" stop-color="#1550E8" stop-opacity="0.92" />
    </linearGradient>
    <radialGradient id="glassGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(390 250) rotate(32) scale(370 260)">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.9" />
      <stop offset="0.4" stop-color="#B3F4FF" stop-opacity="0.46" />
      <stop offset="1" stop-color="#B3F4FF" stop-opacity="0" />
    </radialGradient>
    <filter id="blur24" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="24" />
    </filter>
  </defs>
  <g fill="none">
    <path
      d="M330 143c97-46 215-29 294 54 98 103 107 274 14 373-79 84-199 113-302 76L199 735l66-139c-64-79-84-188-51-286 22-66 61-122 116-167z"
      fill="#66D7FF"
      fill-opacity="0.26"
      filter="url(#blur24)"
    />
    <path
      d="M330 143c97-46 215-29 294 54 98 103 107 274 14 373-79 84-199 113-302 76L199 735l66-139c-64-79-84-188-51-286 22-66 61-122 116-167z"
      fill="url(#glassFill)"
      stroke="rgba(255,255,255,0.46)"
      stroke-width="14"
    />
    <path
      d="M330 143c97-46 215-29 294 54 98 103 107 274 14 373-79 84-199 113-302 76L199 735l66-139c-64-79-84-188-51-286 22-66 61-122 116-167z"
      fill="url(#glassGlow)"
    />
    <path
      d="M280 214c61-71 154-107 252-95"
      stroke="#FFFFFF"
      stroke-opacity="0.6"
      stroke-width="30"
      stroke-linecap="round"
    />
    <path
      d="M274 305c62-39 107-37 171-8"
      stroke="#FFFFFF"
      stroke-opacity="0.3"
      stroke-width="18"
      stroke-linecap="round"
    />
    <circle cx="430" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="553" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="676" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="785" cy="245" r="60" fill="#A0EDFF" fill-opacity="0.54" />
  </g>
</svg>
"""


def build_icns() -> None:
    iconutil = shutil.which("iconutil")
    if not iconutil:
        raise RuntimeError("iconutil was not found on PATH.")
    subprocess.run(
        [iconutil, "-c", "icns", str(ICONSET_DIR), "-o", str(ICONS_DIR / "icon.icns")],
        check=True,
    )


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    (ICONS_DIR / "logo.svg").write_text(build_svg(), encoding="utf-8")

    for filename, size in PNG_OUTPUTS.items():
        write_png(ICONS_DIR / filename, size)

    for filename, size in ICONSET_OUTPUTS.items():
        write_png(ICONSET_DIR / filename, size)

    write_ico(ICONS_DIR / "icon.ico", [16, 32, 48, 256])
    build_icns()


if __name__ == "__main__":
    main()
