---
name: hyperliquid-trade
description: Execute Hyperliquid trading actions from Hermes, including market, limit, and trigger orders, cancellations, order modifications, leverage updates, isolated margin updates, position closes, and scheduled cancels. Use when the user wants to trade, manage positions, or perform signed Hyperliquid execution through Hermes.
license: MIT
compatibility: Requires Python 3.10+, network access, hyperliquid-python-sdk, and Hyperliquid account environment variables.
metadata:
  author: HAAI Labs
  repo: https://github.com/haailabs/hyperliquid-trade
---
# Hyperliquid Trade Skill

Use this skill when the user wants Hermes to execute trading actions on Hyperliquid.

This skill exposes terminal commands for:

- placing market orders
- placing limit orders
- placing trigger orders
- canceling orders
- canceling by CLOID
- modifying orders
- setting leverage
- updating isolated margin
- closing positions
- scheduling cancels

Do not use this skill for passive market/account inspection unless that information is needed before execution.

## Command runner

Run commands through:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt <command> [args]
## Scope

Supported write actions:

- Place limit orders
- Place aggressive IOC market-style orders
- Place reduce-only trigger orders for stop-loss / take-profit
- Cancel by order ID
- Cancel by client order ID (`cloid`)
- Modify a resting order
- Update leverage
- Add/remove isolated margin
- Close an existing position at market
- Schedule or clear Hyperliquid dead-man cancel

Do **not** use this skill for withdrawals, transfers, bridges, or API-wallet creation.

## Security rules

Trading actions are irreversible and may lose money.

Before calling this skill, Hermes must have an explicit user instruction with enough detail to determine:

- coin, for example `BTC` or `ETH`
- action, for example buy/sell/long/short/close/cancel
- size or a safe way to derive size from the current position using the read-only Hyperliquid skill
- order type, for example market, limit, stop-loss, take-profit
- price or trigger price when required

Never invent size, side, leverage, price, or trigger price.

For stop-loss/take-profit on an existing position, first use the read-only Hyperliquid skill to inspect the position. If the user says “set a stop loss on my BTC long at 95000” and the current BTC position is long 0.01, place a reduce-only sell trigger for size 0.01. If the current BTC position is short, use a reduce-only buy trigger.

For leverage changes, the user must explicitly specify the leverage and whether it is cross or isolated unless their wording makes it unambiguous.

## Required environment

The script reads secrets from environment variables and from `.env` files in the current directory and `$HERMES_HOME/.env`.

Required:

```bash
PRIVATE_KEY=0x...
```

Recommended when `PRIVATE_KEY` is an API wallet key:

```bash
HL_ACCOUNT_ADDRESS=0x...   # main wallet public address, not the API-wallet address
```

Optional:

```bash
HL_NETWORK=mainnet         # mainnet or testnet
HL_VAULT_ADDRESS=0x...     # subaccount/vault address if trading on one
```

Important: Hyperliquid API wallets sign with the API-wallet private key, but SDK configuration should still identify the main account address as `account_address`.

## Installation

From this skill directory:

```bash
python -m pip install -r requirements.txt
chmod +x scripts/hyperliquid_trade.py
```

Copy or keep this folder under:

```bash
$HERMES_HOME/skills/hyperliquid-trade/
```

## Command contract

All state-changing commands require `--yes`. Without `--yes`, the script returns a normalized dry-run plan and refuses to submit the transaction.

Base command:

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py <command> [args] --yes
```

Common optional args:

```bash
--network mainnet|testnet
--account-address 0x...
--vault-address 0x...
--expires-after-ms 1710000000000
```

## Examples

### Market long

User: “Long 0.01 BTC at market.”

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py market \
  --coin BTC \
  --side buy \
  --size 0.01 \
  --slippage 0.01 \
  --yes
```

### Limit order

User: “Place a post-only buy for 0.01 BTC at 95000.”

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py limit \
  --coin BTC \
  --side buy \
  --size 0.01 \
  --price 95000 \
  --tif Alo \
  --yes
```

### Stop loss for an existing long

First inspect the position using the read-only Hyperliquid skill. If BTC long size is `0.01`:

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py trigger \
  --coin BTC \
  --side sell \
  --size 0.01 \
  --trigger-price 95000 \
  --tpsl sl \
  --reduce-only \
  --yes
```

### Take profit for an existing short

If ETH short size is `0.5`:

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py trigger \
  --coin ETH \
  --side buy \
  --size 0.5 \
  --trigger-price 2800 \
  --tpsl tp \
  --reduce-only \
  --yes
```

### Cancel by order id

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel \
  --coin BTC \
  --oid 123456789 \
  --yes
```

### Cancel by client order id

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel-cloid \
  --coin BTC \
  --cloid 0x1234567890abcdef1234567890abcdef \
  --yes
```

### Modify an order

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py modify \
  --coin BTC \
  --oid 123456789 \
  --side buy \
  --size 0.01 \
  --price 94000 \
  --tif Gtc \
  --yes
```

### Update leverage

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py leverage \
  --coin BTC \
  --leverage 5 \
  --margin-mode cross \
  --yes
```

### Add isolated margin

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py isolated-margin \
  --coin BTC \
  --amount 25 \
  --yes
```

To remove isolated margin, use a negative amount.

### Close position at market

The SDK detects current side and size unless `--size` is supplied.

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py close-market \
  --coin BTC \
  --slippage 0.01 \
  --yes
```

### Dead-man cancel

Schedule cancel-all 60 seconds from now:

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py schedule-cancel \
  --seconds 60 \
  --yes
```

Clear scheduled cancel:

```bash
python $HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py schedule-cancel \
  --clear \
  --yes
```

## Output

The script always prints JSON. On success:

```json
{
  "ok": true,
  "command": "limit",
  "network": "mainnet",
  "submitted": true,
  "result": {}
}
```

On refusal or validation error:

```json
{
  "ok": false,
  "error": "state-changing commands require --yes"
}
```

Hermes should relay the essential result to the user, including any returned order id, fill status, or exchange error.
