# Hermes Hyperliquid Trade Skill

A write-side Hyperliquid trading skill for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

This skill lets Hermes place and manage signed Hyperliquid exchange actions while leaving read-only market/account queries to Hermes' native Hyperliquid skill.

## What this skill does

Use this skill for signed Hyperliquid write actions:

- place market orders
- place limit orders
- place trigger orders
- cancel orders
- cancel by CLOID
- modify orders
- set leverage
- update isolated margin
- close positions at market
- schedule cancel

Use Hermes' native Hyperliquid skill for read-only actions:

- balances
- positions
- account state
- open orders
- fills
- candles
- order book
- mid prices
- market data

## Design principle

Hermes should never call the Hyperliquid SDK directly.

Hermes should always execute the wrapper:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt <command> [args]
```

The wrapper handles Replit/Nix compatibility by creating and repairing a local `.venv` inside the skill directory. This avoids modifying the system Python environment, which is blocked on Replit/Nix by PEP 668.

Do not run:

```bash
python3 scripts/hyperliquid_trade.py ...
python3 -m pip install ...
pip install ...
```

Run only:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt ...
```

## Requirements

- Hermes Agent
- Python 3.9+
- `uv` recommended, but not required
- Hyperliquid API wallet or main wallet private key
- Hyperliquid account funded and enabled for trading

Dependencies are installed locally by the wrapper from:

```bash
requirements.txt
```

The expected Python package is:

```bash
hyperliquid-python-sdk
```

## Environment variables

The skill expects these environment variables to be available to Hermes:

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

### `PRIVATE_KEY`

`PRIVATE_KEY` is the signer key.

It can be either:

1. the main wallet private key, or
2. an API wallet private key.

For bots and agents, an API wallet is strongly preferred because it can trade but cannot withdraw funds.

Never print, inspect, echo, log, or expose `PRIVATE_KEY`.

### `HL_ACCOUNT_ADDRESS`

`HL_ACCOUNT_ADDRESS` is the Hyperliquid account being traded.

If `PRIVATE_KEY` is your main wallet key, `HL_ACCOUNT_ADDRESS` may be omitted; the script can derive the account address from `PRIVATE_KEY`.

If `PRIVATE_KEY` is an API wallet key, `HL_ACCOUNT_ADDRESS` is required and must be the main/master wallet address that authorized the API wallet.

It must not be the API wallet address.

Correct API-wallet setup:

```bash
PRIVATE_KEY=0x...          # API wallet private key
HL_ACCOUNT_ADDRESS=0x...   # main/master Hyperliquid account
```

The skill status command exposes this distinction safely:

```json
{
  "account_address": "0xMainWallet...",
  "agent_address": "0xApiWallet...",
  "api_wallet_mode": true
}
```

## Installation

Copy the skill into Hermes' skills directory:

```bash
mkdir -p "$HERMES_HOME/skills/hyperliquid-trade"
cp -r hyperliquid-trade/* "$HERMES_HOME/skills/hyperliquid-trade/"
```

Make scripts executable:

```bash
chmod +x "$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt"
chmod +x "$HERMES_HOME/skills/hyperliquid-trade/scripts/install_deps.sh"
chmod +x "$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py"
```

Test from anywhere:

```bash
"$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt" status
```

Expected result:

```json
{
  "ok": true,
  "submitted": false
}
```

## Replit/Nix notes

On Replit/Nix, global `pip install` may fail with:

```text
error: externally-managed-environment
```

This is expected.

Do not use:

```bash
--break-system-packages
```

The `scripts/hlt` wrapper avoids this problem by using a local virtual environment:

```text
$HERMES_HOME/skills/hyperliquid-trade/.venv
```

If dependencies are missing or broken, the wrapper repairs the venv automatically.

## Safety model

Every state-changing command supports dry-run mode.

By default, omit `--yes`.

A dry run returns a JSON plan and does not submit a live exchange action.

Only add `--yes` when the user explicitly confirms or directly asks to:

- place
- execute
- buy
- sell
- long
- short
- close
- cancel
- modify
- submit a live action

This rule is intended for Hermes agent use.

## Basic commands

### Status

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt status
```

### Dry-run market buy

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt market \
  --coin BTC \
  --side buy \
  --size 0.01 \
  --slippage 0.01
```

### Submit market buy

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt market \
  --coin BTC \
  --side buy \
  --size 0.01 \
  --slippage 0.01 \
  --yes
```

### Limit order

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt limit \
  --coin BTC \
  --side buy \
  --size 0.01 \
  --price 90000 \
  --tif Gtc
```

### Set leverage

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt leverage \
  --coin BTC \
  --leverage 5 \
  --yes
```

### Close position at market

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt close-market \
  --coin BTC \
  --slippage 0.01 \
  --yes
```

### Cancel all open orders for a coin

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt cancel \
  --coin BTC \
  --all \
  --yes
```

## JSON response contract

The script returns JSON.

Success:

```json
{
  "ok": true
}
```

Dry-run or non-submitted command:

```json
{
  "submitted": false
}
```

Live action submitted:

```json
{
  "submitted": true
}
```

Failure:

```json
{
  "ok": false,
  "error": "...",
  "detail": "..."
}
```

When `"ok": false`, Hermes should report the `error` and `detail` fields plainly.

## Hermes instruction block

Add this to `SKILL.md` so Hermes knows how to use the skill:

```markdown
# Hermes execution rules

This is the write-side Hyperliquid trading skill.

Use this skill only for signed Hyperliquid exchange actions: market orders, limit orders, trigger orders, cancellations, modifications, leverage changes, isolated margin updates, and closing positions.

Use Hermes' native Hyperliquid skill for read-only account and market data.

On Replit/Nix, do not call `python3`, `pip`, or the Hyperliquid SDK directly.

Always execute:

`$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt <command> [args]`

Default to dry-run mode by omitting `--yes`.

Only add `--yes` when the user explicitly confirms or directly asks to place, execute, buy, sell, long, short, close, cancel, modify, or otherwise submit a live action.

Never expose, print, inspect, echo, or log `PRIVATE_KEY`.

`PRIVATE_KEY` is the signer key.

`HL_ACCOUNT_ADDRESS` is the main Hyperliquid account being traded.

If `PRIVATE_KEY` is an API wallet key, `HL_ACCOUNT_ADDRESS` must be the main/master wallet address that authorized the API wallet, not the API wallet address.

If `"ok": false`, report the `error` and `detail` fields plainly.
```

## Troubleshooting

### `bash: python: command not found`

Use the wrapper instead:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt status
```

Do not call `python` directly.

### `No module named 'eth_account'`

Dependencies are missing from the local venv.

Run:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt status
```

The wrapper should repair the venv automatically.

### `externally-managed-environment`

This is Replit/Nix blocking global pip installs.

Use the wrapper. Do not use `--break-system-packages`.

### `api_wallet_mode: true`

This is normal when `PRIVATE_KEY` is an API wallet key.

Confirm:

```text
account_address = main/master Hyperliquid account
agent_address   = API wallet derived from PRIVATE_KEY
```

### Empty account data or unexpected account

Check `HL_ACCOUNT_ADDRESS`.

If using an API wallet, `HL_ACCOUNT_ADDRESS` must be the main/master wallet address, not the API wallet address.

## Security notes

- Prefer a Hyperliquid API wallet over a main wallet private key.
- Never commit secrets.
- Never store `PRIVATE_KEY` in this repository.
- Keep secrets in Replit Secrets, environment variables, or your deployment secret manager.
- Use dry-runs before live submissions.
- Treat `--yes` as the live-trading switch.

## Repository layout

```text
hyperliquid-trade/
├── SKILL.md
├── README.md
├── requirements.txt
├── _meta.json
├── scripts/
│   ├── hlt
│   ├── install_deps.sh
│   └── hyperliquid_trade.py
└── references/
    └── hyperliquid-write-api-notes.md
```

## License

MIT

