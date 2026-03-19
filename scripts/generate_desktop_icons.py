#!/usr/bin/env python3
from __future__ import annotations

import math
<<<<<<< Updated upstream
import shutil
import struct
import subprocess
=======
import struct
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    deep_blue = (0.05, 0.20, 0.76)
    cyan = (0.40, 0.90, 1.00)
    aqua = (0.62, 0.98, 0.95)
=======
    ember = (0.76, 0.38, 0.25)
    coral = (0.90, 0.56, 0.41)
    peach = (0.97, 0.80, 0.66)
    cocoa = (0.18, 0.12, 0.09)
    gold = (0.98, 0.86, 0.68)
>>>>>>> Stashed changes
    white = (1.0, 1.0, 1.0)

    for py in range(size):
        for px in range(size):
            x = (px + 0.5) / size
            y = (py + 0.5) / size
<<<<<<< Updated upstream
=======
            ux = 0.15 + (x * 0.7)
            uy = 0.13 + (y * 0.7)
>>>>>>> Stashed changes

            rgb = (0.0, 0.0, 0.0)
            alpha = 0.0

<<<<<<< Updated upstream
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
=======
            bubble_d = bubble_distance(ux, uy)
            shadow_d = bubble_distance(ux - 0.04, uy - 0.05)
            shadow_alpha = smoothstep(0.11, -0.035, shadow_d) * 0.13
            rgb, alpha = blend(rgb, alpha, (0.15, 0.10, 0.08), shadow_alpha)

            outer_glow = smoothstep(0.13, -0.025, bubble_d) * 0.18
            glow_color = mix_color(coral, peach, clamp((ux * 0.45) + (uy * 0.35)))
            rgb, alpha = blend(rgb, alpha, glow_color, outer_glow * 0.48)

            bubble_alpha = smoothstep(0.022, -0.022, bubble_d) * 0.84
            if bubble_alpha > 0.0:
                diag = clamp((ux * 0.62) + ((1.0 - uy) * 0.38))
                base = mix_color(ember, coral, diag)
                base = mix_color(base, peach, clamp((0.58 - uy) * 1.08))
                rgb, alpha = blend(rgb, alpha, base, bubble_alpha)

                inner_haze = math.exp(-(((ux - 0.38) ** 2) / 0.018 + ((uy - 0.27) ** 2) / 0.012))
                rgb, alpha = blend(rgb, alpha, white, inner_haze * bubble_alpha * 0.31)

                upper_orb = circle_distance(ux, uy, 0.35, 0.32, 0.10)
                upper_orb_alpha = smoothstep(0.018, -0.02, upper_orb) * bubble_alpha * 0.46
                rgb, alpha = blend(rgb, alpha, white, upper_orb_alpha)

                lower_haze = math.exp(-(((ux - 0.66) ** 2) / 0.048 + ((uy - 0.68) ** 2) / 0.04))
                rgb, alpha = blend(rgb, alpha, gold, lower_haze * bubble_alpha * 0.16)

                sheen_line = math.exp(-(((ux - (0.27 + uy * 0.26)) ** 2) / 0.0016))
                sheen_alpha = sheen_line * smoothstep(0.44, 0.02, uy) * bubble_alpha * 0.24
                rgb, alpha = blend(rgb, alpha, white, sheen_alpha)

                rim = smoothstep(0.022, 0.0, abs(bubble_d)) * 0.2
                rgb, alpha = blend(rgb, alpha, white, rim)

            for center_x in (0.42, 0.54, 0.66):
                dot_d = circle_distance(ux, uy, center_x, 0.47, 0.053)
                dot_alpha = smoothstep(0.018, -0.018, dot_d) * 0.80
                if dot_alpha <= 0.0:
                    continue
                dot_color = mix_color(cocoa, white, 0.16)
                dot_highlight = math.exp(
                    -(((ux - (center_x - 0.018)) ** 2) / 0.00055 + ((uy - 0.447) ** 2) / 0.00038)
                )
                rgb, alpha = blend(rgb, alpha, dot_color, dot_alpha)
                rgb, alpha = blend(rgb, alpha, white, dot_highlight * dot_alpha * 0.28)

            droplet_d = circle_distance(ux, uy, 0.77, 0.24, 0.06)
            droplet_alpha = smoothstep(0.016, -0.02, droplet_d) * 0.44
            if droplet_alpha > 0.0:
                droplet_color = mix_color(peach, white, 0.52)
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
      <stop offset="0" stop-color="#90E8FF" stop-opacity="0.92" />
      <stop offset="0.48" stop-color="#59B6FF" stop-opacity="0.82" />
      <stop offset="1" stop-color="#1550E8" stop-opacity="0.92" />
    </linearGradient>
    <radialGradient id="glassGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(390 250) rotate(32) scale(370 260)">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.9" />
      <stop offset="0.4" stop-color="#B3F4FF" stop-opacity="0.46" />
      <stop offset="1" stop-color="#B3F4FF" stop-opacity="0" />
=======
      <stop offset="0" stop-color="#FFD7B0" stop-opacity="0.94" />
      <stop offset="0.48" stop-color="#EA8E69" stop-opacity="0.84" />
      <stop offset="1" stop-color="#B84A33" stop-opacity="0.9" />
    </linearGradient>
    <radialGradient id="glassGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(390 250) rotate(32) scale(370 260)">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0.9" />
      <stop offset="0.4" stop-color="#FFE6CC" stop-opacity="0.46" />
      <stop offset="1" stop-color="#FFE6CC" stop-opacity="0" />
>>>>>>> Stashed changes
    </radialGradient>
    <filter id="blur24" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="24" />
    </filter>
  </defs>
  <g fill="none">
    <path
      d="M330 143c97-46 215-29 294 54 98 103 107 274 14 373-79 84-199 113-302 76L199 735l66-139c-64-79-84-188-51-286 22-66 61-122 116-167z"
<<<<<<< Updated upstream
      fill="#66D7FF"
      fill-opacity="0.26"
=======
      fill="#F5A97B"
      fill-opacity="0.24"
>>>>>>> Stashed changes
      filter="url(#blur24)"
    />
    <path
      d="M330 143c97-46 215-29 294 54 98 103 107 274 14 373-79 84-199 113-302 76L199 735l66-139c-64-79-84-188-51-286 22-66 61-122 116-167z"
      fill="url(#glassFill)"
<<<<<<< Updated upstream
      stroke="rgba(255,255,255,0.46)"
=======
      stroke="#FFFFFF"
      stroke-opacity="0.46"
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
      stroke-opacity="0.3"
      stroke-width="18"
      stroke-linecap="round"
    />
    <circle cx="430" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="553" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="676" cy="484" r="54" fill="#E8FCFF" fill-opacity="0.86" />
    <circle cx="785" cy="245" r="60" fill="#A0EDFF" fill-opacity="0.54" />
=======
      stroke-opacity="0.22"
      stroke-width="18"
      stroke-linecap="round"
    />
    <circle cx="385" cy="332" r="96" fill="#FFF8F0" fill-opacity="0.46" />
    <circle cx="430" cy="484" r="54" fill="#2A1A13" fill-opacity="0.8" />
    <circle cx="553" cy="484" r="54" fill="#2A1A13" fill-opacity="0.8" />
    <circle cx="676" cy="484" r="54" fill="#2A1A13" fill-opacity="0.8" />
    <circle cx="785" cy="245" r="60" fill="#FFE0C1" fill-opacity="0.48" />
>>>>>>> Stashed changes
  </g>
</svg>
"""


<<<<<<< Updated upstream
def build_icns() -> None:
    iconutil = shutil.which("iconutil")
    if not iconutil:
        raise RuntimeError("iconutil was not found on PATH.")
    subprocess.run(
        [iconutil, "-c", "icns", str(ICONSET_DIR), "-o", str(ICONS_DIR / "icon.icns")],
        check=True,
    )
=======
def write_icns(path: Path) -> None:
    chunk_types = {
        16: b"icp4",
        32: b"icp5",
        64: b"icp6",
        128: b"ic07",
        256: b"ic08",
        512: b"ic09",
        1024: b"ic10",
    }
    chunks = []
    total_length = 8

    for size in (16, 32, 64, 128, 256, 512, 1024):
        image = png_bytes(size, size, render_icon(size))
        chunk = chunk_types[size] + struct.pack(">I", len(image) + 8) + image
        chunks.append(chunk)
        total_length += len(chunk)

    path.write_bytes(b"icns" + struct.pack(">I", total_length) + b"".join(chunks))
>>>>>>> Stashed changes


def main() -> None:
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    (ICONS_DIR / "logo.svg").write_text(build_svg(), encoding="utf-8")

    for filename, size in PNG_OUTPUTS.items():
        write_png(ICONS_DIR / filename, size)

    for filename, size in ICONSET_OUTPUTS.items():
        write_png(ICONSET_DIR / filename, size)

    write_ico(ICONS_DIR / "icon.ico", [16, 32, 48, 256])
<<<<<<< Updated upstream
    build_icns()
=======
    write_icns(ICONS_DIR / "icon.icns")
>>>>>>> Stashed changes


if __name__ == "__main__":
    main()
