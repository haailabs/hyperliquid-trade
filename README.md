# Hermes Hyperliquid Trade Skill

Open-source Hyperliquid execution layer for Hermes agents.

This package adds a Hermes-native trading command surface for Hyperliquid:

- market orders
- limit orders
- trigger orders
- cancels
- cancel by CLOID
- modifies
- leverage updates
- isolated margin updates
- position closes
- scheduled cancels

Built on the official Hyperliquid Python SDK for trader workflows.

Repo: https://github.com/haailabs/hyperliquid-trade

## Why this exists

Hermes agents need a simple, explicit way to execute Hyperliquid trading actions from the terminal.

This skill provides that execution layer as a standalone Hermes skill.

## Install

Clone the repo:

```bash
git clone https://github.com/haailabs/hyperliquid-trade.git
cd hyperliquid-trade
```

Install into Hermes:

```bash
mkdir -p "$HERMES_HOME/skills/hyperliquid-trade"
cp -r . "$HERMES_HOME/skills/hyperliquid-trade/"
cd "$HERMES_HOME/skills/hyperliquid-trade"
python -m pip install -r requirements.txt
chmod +x scripts/hyperliquid_trade.py
```

Optional executable wrapper:

```bash
chmod +x scripts/hlt
```

## Environment

Configure the following environment variables:

```bash
PRIVATE_KEY=0x...
HL_ACCOUNT_ADDRESS=0x...
HL_NETWORK=mainnet
```

Optional:

```bash
HL_VAULT_ADDRESS=0x...
HL_EXPIRES_AFTER_MS=...
```

`HL_NETWORK` may be:

```bash
mainnet
testnet
```

Do not commit secrets to git.

## Quick start

Check status:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py status
```

Dry-run a market order:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order market BTC buy 0.01
```

Execute live:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order market BTC buy 0.01 --yes
```

By default, commands are intended to be safe to inspect before live execution. Use `--yes` only when you intend to execute.

## Commands

### Market order

```bash
scripts/hyperliquid_trade.py order market BTC buy 0.01
scripts/hyperliquid_trade.py order market BTC buy 0.01 --yes
```

### Limit order

```bash
scripts/hyperliquid_trade.py order limit BTC buy 0.01 65000
scripts/hyperliquid_trade.py order limit BTC buy 0.01 65000 --yes
```

### Trigger order

```bash
scripts/hyperliquid_trade.py order trigger BTC buy 0.01 65000 --trigger-price 64000
scripts/hyperliquid_trade.py order trigger BTC buy 0.01 65000 --trigger-price 64000 --yes
```

### Cancel order

```bash
scripts/hyperliquid_trade.py cancel BTC <order_id>
scripts/hyperliquid_trade.py cancel BTC <order_id> --yes
```

### Cancel by CLOID

```bash
scripts/hyperliquid_trade.py cancel-cloid BTC <cloid>
scripts/hyperliquid_trade.py cancel-cloid BTC <cloid> --yes
```

### Modify order

```bash
scripts/hyperliquid_trade.py modify BTC <order_id> --price 65000 --size 0.01
scripts/hyperliquid_trade.py modify BTC <order_id> --price 65000 --size 0.01 --yes
```

### Set leverage

```bash
scripts/hyperliquid_trade.py leverage BTC 5
scripts/hyperliquid_trade.py leverage BTC 5 --yes
```

### Update isolated margin

Add margin:

```bash
scripts/hyperliquid_trade.py margin BTC add 10
scripts/hyperliquid_trade.py margin BTC add 10 --yes
```

Remove margin:

```bash
scripts/hyperliquid_trade.py margin BTC remove 10
scripts/hyperliquid_trade.py margin BTC remove 10 --yes
```

### Close position

```bash
scripts/hyperliquid_trade.py close BTC
scripts/hyperliquid_trade.py close BTC --yes
```

### Schedule cancel

```bash
scripts/hyperliquid_trade.py schedule-cancel --time-ms <timestamp_ms>
scripts/hyperliquid_trade.py schedule-cancel --time-ms <timestamp_ms> --yes
```

## Hermes skill structure

The repository is structured as an Agent Skill:

```text
hyperliquid-trade/
├── SKILL.md
├── README.md
├── LICENSE
├── requirements.txt
├── scripts/
│   ├── hlt
│   └── hyperliquid_trade.py
└── references/
    └── COMMANDS.md
```

The skill name is:

```yaml
name: hyperliquid-trade
```

The directory name should also be:

```text
hyperliquid-trade
```

## Output format

The script should return structured JSON where possible.

Successful command:

```json
{
  "ok": true,
  "action": "order_market",
  "result": {}
}
```

Failed command:

```json
{
  "ok": false,
  "error": "missing_env",
  "detail": "PRIVATE_KEY is not set"
}
```

If `ok` is `false`, report the `error` and `detail` fields directly.

## Development

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run status check:

```bash
python scripts/hyperliquid_trade.py status
```

Run a dry-run command:

```bash
python scripts/hyperliquid_trade.py order market BTC buy 0.01
```

Run live only when intended:

```bash
python scripts/hyperliquid_trade.py order market BTC buy 0.01 --yes
```

## License

MIT
