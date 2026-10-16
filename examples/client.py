#!/usr/bin/env python3
"""Minimal Bot Memory Vault identity client (DRAFT API, not live yet).

pip install pynacl requests
Generates an ed25519 key, derives the did:key, fetches a challenge, signs it and verifies.
"""
import base64, json, os, sys
from nacl.signing import SigningKey

BASE_URL = os.environ.get("BMV_BASE_URL", "https://api.example.invalid")  # placeholder
KEY_FILE = "bot-identity.key"  # keep this private; never upload it

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big"); s = ""
    while n: n, r = divmod(n, 58); s = B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + s

def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def load_or_create_key() -> SigningKey:
    if os.path.exists(KEY_FILE):
        return SigningKey(open(KEY_FILE, "rb").read())
    sk = SigningKey.generate()
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, bytes(sk)); os.close(fd)
    return sk

def did_key(sk: SigningKey) -> str:
    return "did:key:z" + b58encode(b"\xed\x01" + bytes(sk.verify_key))

def sign_text(sk: SigningKey, text: str) -> str:
    return b64u(sk.sign(text.encode("utf-8")).signature)

def handshake_transcript(role, did_i, did_r, n_i, n_r, context, ts) -> str:
    return "\n".join([f"role={role}", "BMV-ID/0 MUTUAL", f"initiator={did_i}",
                      f"responder={did_r}", f"n_i={n_i}", f"n_r={n_r}",
                      f"context={context}", f"ts={ts}"])

def main():
    sk = load_or_create_key(); did = did_key(sk)
    print("DID:", did)
    if "--offline" in sys.argv:
        demo = "BMV-ID/0 PROOF\naud=https://botmemoryvault.com\npurpose=waitlist\n" \
               "challenge_id=ic_demo\nnonce=demo\ndid=" + did + "\nexp=2026-10-16T07:05:00Z"
        print("signature:", sign_text(sk, demo)); return
    import requests
    ch = requests.get(f"{BASE_URL}/v1/id/challenge", params={"purpose": "waitlist"}, timeout=15).json()
    text = ch["sign_this"].replace("<your did>", did)   # exact bytes, \n endings, no trailing newline
    body = {"did": did, "challenge_token": ch["challenge_token"], "signature": sign_text(sk, text)}
    r = requests.post(f"{BASE_URL}/v1/id/verify", json=body, timeout=15)
    print(r.status_code, json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    main()
