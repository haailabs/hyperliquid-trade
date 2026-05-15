# Hermes Hyperliquid Trade Skill

This package adds signed write operations for Hyperliquid to Hermes.

It is intentionally separate from the official read-only Hyperliquid skill:

- Official skill: read market/account state.
- This skill: place/cancel/modify orders, manage leverage/margin, close positions.

See `SKILL.md` for Hermes instructions and command examples.

## Quick install

```bash
mkdir -p "$HERMES_HOME/skills/hyperliquid-trade"
cp -r . "$HERMES_HOME/skills/hyperliquid-trade/"
cd "$HERMES_HOME/skills/hyperliquid-trade"
python -m pip install -r requirements.txt
chmod +x scripts/hyperliquid_trade.py
```

## Environment

```bash
PRIVATE_KEY=0x...
HL_ACCOUNT_ADDRESS=0x...
HL_NETWORK=mainnet
```

Use an API wallet private key, not your main wallet private key.
