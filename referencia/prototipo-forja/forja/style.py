"""Palettes, perceptual colour ramps (OKLCH) and materials.

Every colour on a model comes from a palette role ("primary", "belly", "eye"...).
Each role is expanded into a 6-tone ramp: shadows drift toward cool hues and gain a
little chroma, highlights drift warm and lose chroma (the classic pixel-art ramp).
Because the whole asset set shares a palette, a collection stays visually coherent.
"""
from dataclasses import dataclass, field
import numpy as np

PALETTES = {
    "default": dict(primary="#7a9cc6", second="#4f6d99", belly="#e8dcc0", accent="#f2c14e",
                    horn="#efe6d2", dark="#1e2233", eye="#1e2233", eye_white="#fbfaf5",
                    blush="#ff9eb1", glow="#9ff3ff", sole="#f4f1ea", lace="#ffffff",
                    shoe="#ff6b6b", shoe2="#4ecdc4", wood="#8a5a3b", metal="#b8c2cc"),
    "coral": dict(primary="#ee6c63", second="#ffc9a8", belly="#ffb4a2", accent="#0081a7",
                  horn="#fdf0d5", dark="#2b2d42", eye="#2b2d42", eye_white="#fffdf2",
                  blush="#ff7aa2", glow="#c4fff9", sole="#f5f3ee", lace="#ffffff",
                  shoe="#00a6b4", shoe2="#ffd166", wood="#8a5a3b", metal="#b8c2cc"),
    "jade": dict(primary="#3aa676", second="#23715a", belly="#f6d68b", accent="#f4ecd8",
                 horn="#f4ecd8", wing="#8fd8bd", dark="#1d2b2a", eye="#1d2b2a",
                 eye_white="#fffbe8", blush="#ff9aa2", glow="#ffe066", sole="#f5f3ee",
                 lace="#ffffff", shoe="#ff5d73", shoe2="#ffd166", wood="#8a5a3b",
                 metal="#b8c2cc"),
    "beetle": dict(primary="#3b5bdb", second="#74c0fc", belly="#2b3150", accent="#ffc53d",
                   horn="#ffc53d", leg="#262b45", dark="#12152a", eye="#12152a",
                   eye_white="#f8f9fa", blush="#ff8fab", glow="#b2f2bb", sole="#f5f3ee",
                   lace="#ffffff", shoe="#ff922b", shoe2="#ffffff", wood="#8a5a3b",
                   metal="#b8c2cc"),
    "slime": dict(primary="#63d471", second="#2f9e44", belly="#3bc9a0", accent="#ffc53d",
                  horn="#ffe8a3", dark="#173d2a", eye="#173d2a", eye_white="#f4fff2",
                  blush="#ff8fab", glow="#e9fbe6", shine="#f1fff0", sole="#f5f3ee",
                  lace="#ffffff", shoe="#845ef7", shoe2="#ffd43b", wood="#8a5a3b",
                  metal="#d9dee3", gem="#ff4d6d"),
    "lich": dict(primary="#4c3a73", second="#2d2347", belly="#6b56a0", accent="#ffd166",
                 bone="#e9e2cf", horn="#e9e2cf", dark="#140f21", eye="#140f21",
                 eye_white="#f4f0ff", glow="#7cf6ff", blush="#c77dff", wood="#5b3a29",
                 metal="#b8c2cc", gem="#7cf6ff", sole="#f5f3ee", lace="#ffffff",
                 shoe="#7cf6ff", shoe2="#ffd166"),
}


def hex_to_rgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255.0


def _lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _gam(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def rgb_to_oklch(rgb):
    r, g, b = _lin(rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return float(L), float(np.hypot(a, bb)), float(np.degrees(np.arctan2(bb, a)) % 360)


def oklch_to_rgb(L, C, H):
    for _ in range(40):
        a, b = C * np.cos(np.radians(H)), C * np.sin(np.radians(H))
        l_ = L + 0.3963377774 * a + 0.2158037573 * b
        m_ = L - 0.1055613458 * a - 0.0638541728 * b
        s_ = L - 0.0894841775 * a - 1.2914855480 * b
        l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
        lin = np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])
        if lin.min() >= -1e-4 and lin.max() <= 1 + 1e-4:
            break
        C *= 0.9
    return _gam(np.clip(lin, 0, 1))


def _toward(h, target, amount):
    d = (target - h + 180) % 360 - 180
    return (h + np.sign(d) * min(abs(d), amount)) % 360


N_DARK, N_LIGHT = 3, 2
BASE = N_DARK          # index of the base tone inside a ramp
N_TONES = N_DARK + N_LIGHT + 1


def make_ramp(color, dl_dark=0.085, dl_light=0.07, hue_dark=9.0, hue_light=7.0):
    rgb = hex_to_rgb(color) if isinstance(color, str) else np.asarray(color, float)
    L0, C0, H0 = rgb_to_oklch(rgb)
    out = []
    for i in range(N_TONES):
        t = i - N_DARK
        L, C, H = L0, C0, H0
        if t < 0:
            L = L0 + t * dl_dark
            C = C0 * (1 + 0.07 * -t)
            if C0 > 0.02:
                H = _toward(H0, 265.0, hue_dark * -t)
        elif t > 0:
            L = L0 + t * dl_light
            C = C0 * (1 - 0.16 * t)
            if C0 > 0.02:
                H = _toward(H0, 95.0, hue_light * t)
        out.append(oklch_to_rgb(float(np.clip(L, 0.08, 0.985)), max(C, 0.0), H))
    return (np.array(out) * 255).round().astype(np.uint8)


def resolve_color(palette, name):
    if name is None:
        return None
    if isinstance(name, str) and name.startswith('#'):
        return name
    if name in palette:
        return palette[name]
    raise KeyError(f"Cor '{name}' nao existe na paleta. Papeis disponiveis: "
                   f"{', '.join(sorted(palette))} (ou use '#rrggbb').")


PATTERNS = {None, "none", "noise", "spots", "stripes", "belly", "gradient", "speckle",
            "scales", "patches", "top"}


@dataclass
class Material:
    name: str
    color: str = "primary"
    second: str = None
    pattern: str = None      # see PATTERNS
    scale: float = 3.0       # pattern size in model units
    amount: float = 0.35     # coverage / height fraction of the pattern
    axis: str = "z"          # stripes direction
    noise: float = 0.3       # tone jitter (0 = flat colour)
    bevel: float = None      # edge highlight strength (None = model default)
    ao: float = 1.0          # how much baked ambient occlusion darkens it
    emissive: bool = False   # ignore lighting (glowing bits)
    extra: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.pattern not in PATTERNS:
            raise ValueError(f"Padrao '{self.pattern}' invalido. Use: "
                             f"{', '.join(sorted(p for p in PATTERNS if p))}")
