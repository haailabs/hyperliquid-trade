---
name: hyperliquid-trade
description: Execute Hyperliquid trading actions from Hermes, including market, limit, and trigger orders, cancellations, order modifications, leverage updates, isolated margin updates, position closes, and scheduled cancels. Use when the user wants to trade, manage positions, or perform Hyperliquid execution through Hermes.
license: MIT
compatibility: Requires Python 3.10+, network access, hyperliquid-python-sdk, and configured Hyperliquid environment variables.
metadata:
  author: HAAI Labs
  repo: https://github.com/haailabs/hyperliquid-trade
---

# Hyperliquid Trade Skill

Use this skill when the user wants Hermes to execute trading actions on Hyperliquid.

This skill provides a Hermes-native command surface for Hyperliquid trader workflows:

- market orders
- limit orders
- trigger orders
- order cancellations
- cancel by CLOID
- order modifications
- leverage updates
- isolated margin updates
- position closes
- scheduled cancels

Do not use this skill for general market browsing unless that information is required to prepare or validate an execution command.

## Command runner

Run commands through the skill script:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py <command> [args]
```

If the executable wrapper is installed, commands may also be run through:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hlt <command> [args]
```

## Required environment

The following environment variables must be configured before using the skill:

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

Rules:

- Never print, log, expose, or repeat `PRIVATE_KEY`.
- `HL_NETWORK` should be either `mainnet` or `testnet`.
- `HL_ACCOUNT_ADDRESS` should be the Hyperliquid account address used for execution.
- If using a vault, set `HL_VAULT_ADDRESS`.

## Execution policy

Default to dry-run unless the user explicitly requests live execution.

For live execution, include:

```bash
--yes
```

When the user asks to place, cancel, modify, close, or otherwise execute a trading action, make the command explicit before running it whenever practical.

If a command returns:

```json
{"ok": false}
```

report the `error` and `detail` fields plainly.

Do not invent order status, fills, balances, or execution results. Only report what the command returns.

## Common commands

### Check skill status

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py status
```

### Place a market order

Dry run:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order market BTC buy 0.01
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order market BTC buy 0.01 --yes
```

### Place a limit order

Dry run:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order limit BTC buy 0.01 65000
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order limit BTC buy 0.01 65000 --yes
```

### Place a trigger order

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py order trigger BTC buy 0.01 65000 --trigger-price 64000
```

### Cancel an order

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel BTC <order_id>
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel BTC <order_id> --yes
```

### Cancel by CLOID

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel-cloid BTC <cloid>
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py cancel-cloid BTC <cloid> --yes
```

### Modify an order

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py modify BTC <order_id> --price 65000 --size 0.01
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py modify BTC <order_id> --price 65000 --size 0.01 --yes
```

### Set leverage

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py leverage BTC 5
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py leverage BTC 5 --yes
```

### Update isolated margin

Add margin:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py margin BTC add 10
```

Remove margin:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py margin BTC remove 10
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py margin BTC add 10 --yes
```

### Close a position

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py close BTC
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py close BTC --yes
```

### Schedule cancel

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py schedule-cancel --time-ms <timestamp_ms>
```

Live execution:

```bash
$HERMES_HOME/skills/hyperliquid-trade/scripts/hyperliquid_trade.py schedule-cancel --time-ms <timestamp_ms> --yes
```

## Good behavior for agents

When using this skill:

1. Identify the intended trading action.
2. Identify the coin, side, size, price, trigger price, order ID, leverage, or margin amount required by that action.
3. Refuse to guess missing execution-critical values.
4. Prefer dry-run unless live execution is explicitly requested.
5. Use `--yes` only when the user clearly requests live execution.
6. Report command output accurately.
7. If execution fails, report `error` and `detail` plainly.
8. Never expose secrets.

## Examples of user requests that should activate this skill

Use this skill when the user says things like:

- “Place a limit buy on BTC.”
- “Cancel my ETH order.”
- “Modify this order to 0.02 BTC at 65000.”
- “Set BTC leverage to 5x.”
- “Add margin to my SOL position.”
- “Close my BTC position.”
- “Schedule cancels.”
- “Run a dry-run market order.”
- “Execute this Hyperliquid trade through Hermes.”

## Examples of requests that need clarification

Ask for missing details when the user says:

- “Buy BTC” without size or order type.
- “Cancel my order” without order ID, CLOID, or enough context.
- “Close my position” without the coin.
- “Set leverage” without coin or leverage value.
- “Add margin” without coin or amount.

## Error handling

If the script returns JSON with `ok: false`, summarize only the relevant failure fields.

Example:

```json
{
  "ok": false,
  "error": "missing_env",
  "detail": "PRIVATE_KEY is not set"
}
```

Report:

```text
The command failed: missing_env.
Detail: PRIVATE_KEY is not set.
```

Do not add speculative causes unless the command output supports them.

## Safety

This skill can execute live trading actions. Treat all live commands as irreversible unless the exchange response says otherwise.

Never use `--yes` unless live execution is explicitly requested.
