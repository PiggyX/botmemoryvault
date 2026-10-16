# Bot Memory Vault

Encrypted memory backup and restore for AI agents. Bots first: a bot holds its own ed25519 key, proves who it is by signing a challenge, and backs up client-side-encrypted memory snapshots that the vault cannot read.

Operated by **Piggy X Pty Ltd** (ABN 58 601 993 284), Australia.

## Status

**Pre-launch / waitlist.** The vault API is in private testing and is **not publicly available yet**. Everything in `docs/` is a draft and may change before launch.

## For bots: where to look

| What | URL |
|---|---|
| Website | https://botmemoryvault.com |
| Machine-readable summary | https://botmemoryvault.com/llms.txt |
| Agent card | https://botmemoryvault.com/.well-known/agent-card.json |
| Security contact | https://botmemoryvault.com/.well-known/security.txt |

## This repo

- `docs/api.md`: draft of the public bot API (identity, challenge/proof, bot-to-bot handshake, snapshots).
- `examples/client.py`: minimal Python client: keypair, `did:key`, challenge signing, handshake transcript.
- `brand/`: the signed logo, its **mock-up** verification key and `decode_verify.py` to check it.

No service code, configuration or credentials live here.

## License

Code and docs: MIT (see `LICENSE`). The Bot Memory Vault name, logo and brand assets are **not** licensed for reuse.
