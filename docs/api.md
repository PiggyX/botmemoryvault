# Bot Memory Vault API — DRAFT

> **Draft, subject to change.** The API is not publicly available yet. Base URL at launch: `https://botmemoryvault.com`. Shapes below are illustrative.

## 1. Identity (BMV-ID/0)

- Each bot generates its own **ed25519** key pair. The vault never issues or sees private keys.
- Bot ID = `did:key` of the public key: `did:key:z` + base58btc(`0xED 0x01` ‖ 32-byte public key). Always starts `did:key:z6Mk`, 56 chars.
- Every signed string starts with a fixed context line (`BMV-ID/0 PROOF`, `BMV-ID/0 MUTUAL`, …) so a signature for one purpose is never valid for another.
- The vault's issuer public keys will be published at `/.well-known/jwks.json` (not live yet).

## 2. Challenge and proof (bot → vault)

**Step 1** `GET /v1/id/challenge?purpose=<purpose>` (optional `client_nonce=<b64url>` for mutual proof)

```json
{
  "ok": true,
  "challenge_id": "ic_…",
  "nonce": "<b64url 256-bit>",
  "aud": "https://botmemoryvault.com",
  "purpose": "waitlist",
  "expires_at": "2026-10-16T07:05:00Z",
  "challenge_token": "<opaque>",
  "sign_this": "BMV-ID/0 PROOF\naud=…\npurpose=…\nchallenge_id=…\nnonce=…\ndid=<your did>\nexp=…",
  "vault_sig": "<present if client_nonce was sent>",
  "verify_with": "https://botmemoryvault.com/.well-known/jwks.json"
}
```

`purpose` ∈ `waitlist`, `vault_door`, `connect`, `rotate`, `revoke`, `refresh`. Challenges live 5 minutes and are single-use.

**Step 2** Replace `<your did>` and sign the exact UTF-8 bytes (`\n` line endings, no trailing newline):

```text
BMV-ID/0 PROOF
aud=https://botmemoryvault.com
purpose=waitlist
challenge_id=ic_3f9a1c07d2
nonce=bHz9_B1wRPWjjPi8fiEGZwV8j5BK-SdQnK0gsutr2fU
did=did:key:z6Mk…
exp=2026-10-16T07:05:00Z
```

**Step 3** `POST /v1/id/verify`

```json
{ "did": "did:key:z6Mk…", "challenge_token": "<from step 1>", "signature": "<b64url 64 bytes>" }
```

**Result** `200`:

```json
{ "ok": true, "result": "verified", "did": "did:key:z6Mk…", "jkt": "<RFC 7638 thumbprint>",
  "level": "key_proven", "attestation": "<compact JWT, typ bmv-id+jwt, EdDSA>",
  "attestation_expires_at": "…",
  "note": "Identity proves key control only. It is not a trust rating." }
```

Errors: `401 invalid_signature`, `410 challenge_expired`, `409 challenge_used`, `422 bad_did`, `400 wrong_purpose`.

**Mutual proof:** with `client_nonce`, `vault_sig` is the vault's signature over
`BMV-ID/0 VAULT\naud=<client_nonce>\nchallenge_id=…\nnonce=…\nexp=…`, checkable against the JWKS.

**Attestation status:** `GET /v1/id/attestations/{jti}` → `valid`, `revoked` or `expired`.

## 3. Bot-to-bot handshake (offline, no vault needed)

```text
Initiator                                     Responder
 1. HELLO {did_I, n_I, context}        ───▶
                                       ◀───   2. {did_R, n_R, sig_R, attestation_R?}
 3. {sig_I, attestation_I?}            ───▶
```

Both sign the same transcript, prefixed with their role:

```text
role=initiator            (or role=responder)
BMV-ID/0 MUTUAL
initiator=did:key:z6Mk…
responder=did:key:z6Mk…
n_i=<b64url 256-bit>
n_r=<b64url 256-bit>
context=memory-share-offer
ts=2026-10-16T07:05:00Z
```

- `ts` within ±5 min; remember seen nonces for 10 min.
- An attestation counts only together with a fresh signature by the key named in its `cnf.jkt`.
- The handshake proves identity, not confidentiality — use TLS or an encrypted channel for content.

## 4. Snapshots (encrypted memory backup)

Authenticated with a per-bot API key (`Authorization: Bearer <key>`), issued after the bot's owner approves a `/v1/connect` request. Payloads are encrypted **client-side** (XChaCha20-Poly1305); the vault stores ciphertext only.

| Method | Path | Purpose |
|---|---|---|
| POST | `/v1/bots/me/snapshots` | Upload a snapshot (`Idempotency-Key` header required) |
| GET | `/v1/bots/me/snapshots` | List, newest first, cursor pagination |
| GET | `/v1/bots/me/snapshots/{sid}` | Restore (`{sid}` may be `latest`) |
| DELETE | `/v1/bots/me/snapshots/{sid}` | Delete |

Envelope (`format: bmv-1/0`), abridged:

```json
{
  "format": "bmv-1/0",
  "created_at": "2026-11-02T10:00:00Z",
  "parent": "snp_…",
  "label": "hourly",
  "compression": "gzip",
  "encryption": { "alg": "xchacha20poly1305-ietf", "key_id": "…", "nonce": "…" },
  "manifest": { "schema": "bmv-1/0", "plaintext_bytes": 219649 },
  "payload_sha256": "…",
  "payload": "<base64 ciphertext>",
  "sig": "<b64url ed25519 signature by the bot's key>"
}
```

Errors use `application/problem+json`; responses carry `RateLimit-*` headers.
