#!/usr/bin/env python3
"""bmv-logo-v2 decoder/verifier.
(a) PNG: sample the 3 rings (outer->inner), find each ring's 1110 marker, concatenate, check name + CRC-8.
(b) SVG: verify Ed25519 signature over the canonical form against the JWKS.
Usage: decode_verify.py [png] [svg] [jwks.json]"""
import sys, os, re, json, base64, itertools
import numpy as np
from PIL import Image
from nacl.signing import VerifyKey
from spec import *
H = os.path.dirname(os.path.abspath(__file__))
png = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, "logo-512.png")
svgp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(H, "logo.svg")
jwks = sys.argv[3] if len(sys.argv) > 3 else os.path.join(H, "logo-key.json")
ok = True
NBITS = (len(BRAND_NAME) + 1 + 8 + 1) * 8
LAYOUT = ring_layout(NBITS)

def decode_png(path):
    lum = np.asarray(Image.open(path).convert("L")).astype(float); S = lum.shape[1]
    def sample(x, y, rad):
        r = max(0, int(rad)); return lum[int(round(y))-r:int(round(y))+r+1, int(round(x))-r:int(round(x))+r+1].mean()
    raw = []
    for r, n in LAYOUT:
        N = n + 4; raw.append([sample(*dot_xy(i, N, r, S), DOT_R*S*0.4) for i in range(N)])
    allv = np.concatenate(raw); th = (allv.min() + allv.max()) / 2
    if sample(S/2, S/2, R_CENTRE*S*0.5) <= th: return None          # registration: centre dot must be "on"
    rings = [[int(v > th) for v in rv] for rv in raw]
    cands = [[rot for rot in range(len(b)) if (b[rot:]+b[:rot])[:4] == MARKER] for b in rings]
    for rots in itertools.product(*cands):
        bits = sum([(b[rot:]+b[:rot])[4:] for b, rot in zip(rings, rots)], [])
        by = bits_to_bytes(bits); body, crc = by[:-1], by[-1]
        name = BRAND_NAME.encode() + SEP.encode()
        if body.startswith(name) and crc8(body) == crc:
            return rots, body[len(name):], crc, float(allv.max()-allv.min())
    return None

print(f"(a) PNG decode: {png}")
r = decode_png(png); fp = None
if r:
    rots, fp, crc, ct = r
    print(f"    name='{BRAND_NAME}'  fp={fp.hex()}  crc=0x{crc:02x} OK  rotations={rots}  contrast={ct:.0f}/255  -> PASS")
else:
    print("    -> FAIL (no valid markers/CRC)"); ok = False
print(f"(b) SVG signature: {svgp}")
svg = open(svgp, encoding="utf-8").read()
m = re.search(r'<bmv:signature\b([^>]*)>([^<]*)</bmv:signature>', svg)
attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
k = {k["kid"]: k for k in json.load(open(jwks))["keys"]}.get(attrs["kid"])
if not k:
    print("    -> FAIL (kid not in JWKS)"); ok = False
else:
    pub = base64.urlsafe_b64decode(k["x"] + "==")
    try:
        VerifyKey(pub).verify(canonical(svg).encode(), base64.urlsafe_b64decode(m.group(2) + "=="))
        same = jwk_thumbprint(pub) == attrs["kid"] and (fp is None or fingerprint8(pub) == fp)
        print(f"    kid={attrs['kid']}  signature valid; kid==thumbprint & ring fp matches key: {same} -> {'PASS' if same else 'FAIL'}")
        ok &= same
    except Exception as e:
        print(f"    -> FAIL ({e})"); ok = False
    ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', svg, re.S).group(1))
    print(f"    JSON-LD: {ld['name']} / {ld['brand']['name']} / spec {ld['bmv:logo']['spec']} / coded '{ld['bmv:logo']['codedName']}'")
print("OVERALL:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
