"""Shared constants and helpers for bmv-logo-v2 (bot-only, 3 concentric rings)."""
import hashlib, base64, json, math, re, itertools
SPEC = "bmv-logo-v2"
BRAND_NAME = "Bot Memory Vault"      # <- one-line swap (e.g. "Bot Memory Vote")
SEP = ":"
# machine-first palette: max luminance contrast
BG, ON, OFF, REG = "#000000", "#ffffff", "#5a5a5a", "#ffffff"
ACC, INK, MUT, LINE = "#8fe3cf", "#f2f7f5", "#b9cac5", "#2c4350"   # bot-view annotations only
MARKER = [1, 1, 1, 0]                 # per-ring start marker at 12 o'clock
R_FINDER, R_CENTRE = 0.485, 0.04      # outer finder ring + centre registration dot
DOT_R = 0.0115
FONT = "DejaVu Sans"
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def jwk_thumbprint(pub):
    j = json.dumps({"crv": "Ed25519", "kty": "OKP", "x": b64u(pub)}, separators=(",", ":"), sort_keys=True)
    return b64u(hashlib.sha256(j.encode()).digest())
def fingerprint8(pub): return base64.urlsafe_b64decode(jwk_thumbprint(pub) + "=")[:8]
def crc8(data, poly=0x07):
    c = 0
    for b in data:
        c ^= b
        for _ in range(8): c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c
def to_bits(bs): return [(b >> (7-i)) & 1 for b in bs for i in range(8)]
def bits_to_bytes(bits): return bytes(int("".join(map(str, bits[i:i+8])), 2) for i in range(0, len(bits), 8))
def body_bytes(fp): return BRAND_NAME.encode("ascii") + SEP.encode() + fp
def stream_bits(fp):
    b = body_bytes(fp); return to_bits(b + bytes([crc8(b)]))
def ring_layout(nbits):
    """Split nbits across 3 rings (outer, middle, inner) roughly by circumference.
    Returns [(radius, data_bits)]; each ring gets 4 marker dots + data_bits dots."""
    radii = [0.44, 0.365, 0.29]
    w = [r/sum(radii) for r in radii]
    d = [round(nbits*x) for x in w[:2]]; d.append(nbits - sum(d))
    return list(zip(radii, d))
def ring_dots(fp):
    """[(radius, [bits incl. marker])] in reading order outer->inner."""
    bits = stream_bits(fp); out = []; i = 0
    for r, n in ring_layout(len(bits)):
        out.append((r, MARKER + bits[i:i+n])); i += n
    return out
def dot_xy(i, n, r, S):
    a = 2*math.pi*i/n
    return S/2 + r*S*math.sin(a), S/2 - r*S*math.cos(a)
SIG_PLACEHOLDER = "__BMV_SIG__"
def canonical(svg): return re.sub(r'(<bmv:signature\b[^>]*>)[^<]*(</bmv:signature>)', r'\1\2', svg)
