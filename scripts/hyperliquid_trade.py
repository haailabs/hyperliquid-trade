#!/usr/bin/env python3
"""
Hyperliquid write-side CLI for Hermes.

Uses the official hyperliquid-python-sdk for signing and submission.
Secrets are read from env / .env; private keys are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional


def load_dotenv_files() -> None:
    """Minimal .env loader to avoid adding python-dotenv as a dependency."""
    candidates = [
        Path.cwd() / ".env",
        Path(os.environ.get("HERMES_HOME", "")) / ".env" if os.environ.get("HERMES_HOME") else None,
    ]
    for path in candidates:
        if not path or not path.exists():
            continue
        try:
            for raw_line in path.read_text().splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            # Do not fail trading just because a non-critical .env file cannot be read.
            pass


def emit(payload: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


def normalize_private_key(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("PRIVATE_KEY is empty")
    if not value.startswith("0x"):
        value = "0x" + value
    if len(value) != 66:
        # Do not print the key. Just give the expected shape.
        raise ValueError("PRIVATE_KEY must be a 32-byte hex private key, with or without 0x prefix")
    return value


def import_sdk():
    try:
        import eth_account
        from hyperliquid.exchange import Exchange
        from hyperliquid.utils import constants
        from hyperliquid.utils.types import Cloid
    except Exception as exc:
        emit(
            {
                "ok": False,
                "error": "Missing Hyperliquid SDK dependencies. Run: python -m pip install -r requirements.txt",
                "detail": str(exc),
            },
            2,
        )
    return eth_account, Exchange, constants, Cloid


def network_url(constants: Any, network: str) -> str:
    network = network.lower()
    if network == "mainnet":
        return constants.MAINNET_API_URL
    if network == "testnet":
        return constants.TESTNET_API_URL
    raise ValueError("--network must be mainnet or testnet")


def env_first(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def bool_side(side: str) -> bool:
    s = side.lower()
    if s in {"buy", "long", "bid"}:
        return True
    if s in {"sell", "short", "ask"}:
        return False
    raise ValueError("--side must be buy/sell or long/short")


def limit_type(tif: str) -> dict[str, dict[str, str]]:
    # Hyperliquid SDK/docs use Gtc, Ioc, Alo capitalization.
    canonical = {"gtc": "Gtc", "ioc": "Ioc", "alo": "Alo"}
    key = tif.lower()
    if key not in canonical:
        raise ValueError("--tif must be Gtc, Ioc, or Alo")
    return {"limit": {"tif": canonical[key]}}


def trigger_type(trigger_px: float, is_market: bool, tpsl: str) -> dict[str, dict[str, Any]]:
    t = tpsl.lower()
    if t not in {"tp", "sl"}:
        raise ValueError("--tpsl must be tp or sl")
    return {
        "trigger": {
            "triggerPx": str(trigger_px),
            "isMarket": bool(is_market),
            "tpsl": t,
        }
    }


def cloid_or_none(Cloid: Any, value: Optional[str]) -> Any:
    if not value:
        return None
    return Cloid.from_str(value)


def oid_or_cloid(Cloid: Any, oid: Optional[int], cloid: Optional[str]) -> Any:
    if oid is None and not cloid:
        raise ValueError("provide --oid or --cloid")
    if oid is not None and cloid:
        raise ValueError("provide only one of --oid or --cloid")
    return oid if oid is not None else Cloid.from_str(cloid)


def make_exchange(args: argparse.Namespace):
    load_dotenv_files()
    eth_account, Exchange, constants, Cloid = import_sdk()

    private_key = env_first("PRIVATE_KEY", "HL_PRIVATE_KEY", "HYPERLIQUID_PRIVATE_KEY")
    if not private_key:
        emit(
            {
                "ok": False,
                "error": "Missing PRIVATE_KEY environment variable.",
                "hint": "Set PRIVATE_KEY to the authorized Hyperliquid API-wallet private key.",
            },
            2,
        )

    try:
        private_key = normalize_private_key(private_key)
        account = eth_account.Account.from_key(private_key)
        network = args.network or env_first("HL_NETWORK", "HYPERLIQUID_NETWORK") or "mainnet"
        base_url = network_url(constants, network)
    except Exception as exc:
        emit({"ok": False, "error": str(exc)}, 2)

    account_address = (
        args.account_address
        or env_first("HL_ACCOUNT_ADDRESS", "ACCOUNT_ADDRESS", "HYPERLIQUID_ACCOUNT_ADDRESS")
        or account.address
    )
    vault_address = args.vault_address or env_first("HL_VAULT_ADDRESS", "VAULT_ADDRESS", "HYPERLIQUID_VAULT_ADDRESS")

    exchange = Exchange(
        account,
        base_url,
        account_address=account_address,
        vault_address=vault_address,
    )

    expires_after_ms = args.expires_after_ms
    if expires_after_ms is not None:
        exchange.set_expires_after(expires_after_ms)

    config = {
        "network": network,
        "account_address": account_address,
        "agent_address": account.address,
        "vault_address": vault_address,
        "expires_after_ms": expires_after_ms,
        "api_wallet_mode": account_address.lower() != account.address.lower(),
    }
    return exchange, config, Cloid


def require_yes(args: argparse.Namespace, plan: dict[str, Any]) -> None:
    if not args.yes:
        emit(
            {
                "ok": False,
                "submitted": False,
                "error": "State-changing commands require --yes.",
                "dry_run_plan": plan,
            },
            1,
        )


def command_status(args: argparse.Namespace) -> None:
    exchange, config, _ = make_exchange(args)
    emit({"ok": True, "command": "status", "submitted": False, "config": config})


def command_limit(args: argparse.Namespace) -> None:
    order_type = limit_type(args.tif)
    plan = {
        "command": "limit",
        "coin": args.coin,
        "is_buy": bool_side(args.side),
        "size": args.size,
        "price": args.price,
        "order_type": order_type,
        "reduce_only": args.reduce_only,
        "cloid": args.cloid,
    }
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)
    result = exchange.order(
        args.coin,
        plan["is_buy"],
        args.size,
        args.price,
        order_type,
        reduce_only=args.reduce_only,
        cloid=cloid_or_none(Cloid, args.cloid),
    )
    emit({"ok": True, "command": "limit", "submitted": True, **config, "result": result})


def command_market(args: argparse.Namespace) -> None:
    is_buy = bool_side(args.side)
    plan = {
        "command": "market",
        "coin": args.coin,
        "is_buy": is_buy,
        "size": args.size,
        "slippage": args.slippage,
        "reduce_only": args.reduce_only,
        "cloid": args.cloid,
    }
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)

    if args.reduce_only:
        # SDK market_open is not reduce-only, so construct the aggressive IOC order explicitly.
        px = exchange._slippage_price(args.coin, is_buy, args.slippage, None)
        result = exchange.order(
            args.coin,
            is_buy,
            args.size,
            px,
            {"limit": {"tif": "Ioc"}},
            reduce_only=True,
            cloid=cloid_or_none(Cloid, args.cloid),
        )
    else:
        result = exchange.market_open(
            args.coin,
            is_buy,
            args.size,
            slippage=args.slippage,
            cloid=cloid_or_none(Cloid, args.cloid),
        )
    emit({"ok": True, "command": "market", "submitted": True, **config, "result": result})


def command_trigger(args: argparse.Namespace) -> None:
    is_buy = bool_side(args.side)
    order_type = trigger_type(args.trigger_price, args.is_market, args.tpsl)
    limit_px = args.limit_price if args.limit_price is not None else args.trigger_price
    plan = {
        "command": "trigger",
        "coin": args.coin,
        "is_buy": is_buy,
        "size": args.size,
        "limit_price": limit_px,
        "trigger_price": args.trigger_price,
        "is_market": args.is_market,
        "tpsl": args.tpsl.lower(),
        "reduce_only": args.reduce_only,
        "grouping": args.grouping,
        "cloid": args.cloid,
    }
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)

    # Use bulk_orders to preserve grouping for TP/SL semantics.
    order = {
        "coin": args.coin,
        "is_buy": is_buy,
        "sz": args.size,
        "limit_px": limit_px,
        "order_type": order_type,
        "reduce_only": args.reduce_only,
    }
    cloid = cloid_or_none(Cloid, args.cloid)
    if cloid:
        order["cloid"] = cloid
    result = exchange.bulk_orders([order], grouping=args.grouping)
    emit({"ok": True, "command": "trigger", "submitted": True, **config, "result": result})


def command_cancel(args: argparse.Namespace) -> None:
    plan = {"command": "cancel", "coin": args.coin, "oid": args.oid}
    require_yes(args, plan)
    exchange, config, _ = make_exchange(args)
    result = exchange.cancel(args.coin, args.oid)
    emit({"ok": True, "command": "cancel", "submitted": True, **config, "result": result})


def command_cancel_cloid(args: argparse.Namespace) -> None:
    plan = {"command": "cancel-cloid", "coin": args.coin, "cloid": args.cloid}
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)
    result = exchange.cancel_by_cloid(args.coin, Cloid.from_str(args.cloid))
    emit({"ok": True, "command": "cancel-cloid", "submitted": True, **config, "result": result})


def command_modify(args: argparse.Namespace) -> None:
    order_type = limit_type(args.tif)
    plan = {
        "command": "modify",
        "coin": args.coin,
        "oid": args.oid,
        "cloid": args.cloid,
        "is_buy": bool_side(args.side),
        "size": args.size,
        "price": args.price,
        "order_type": order_type,
        "reduce_only": args.reduce_only,
        "new_cloid": args.new_cloid,
    }
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)
    oid = oid_or_cloid(Cloid, args.oid, args.cloid)
    result = exchange.modify_order(
        oid,
        args.coin,
        plan["is_buy"],
        args.size,
        args.price,
        order_type,
        reduce_only=args.reduce_only,
        cloid=cloid_or_none(Cloid, args.new_cloid),
    )
    emit({"ok": True, "command": "modify", "submitted": True, **config, "result": result})


def command_leverage(args: argparse.Namespace) -> None:
    is_cross = args.margin_mode.lower() == "cross"
    plan = {
        "command": "leverage",
        "coin": args.coin,
        "leverage": args.leverage,
        "is_cross": is_cross,
    }
    require_yes(args, plan)
    exchange, config, _ = make_exchange(args)
    result = exchange.update_leverage(args.leverage, args.coin, is_cross=is_cross)
    emit({"ok": True, "command": "leverage", "submitted": True, **config, "result": result})


def command_isolated_margin(args: argparse.Namespace) -> None:
    plan = {
        "command": "isolated-margin",
        "coin": args.coin,
        "amount_usdc": args.amount,
    }
    require_yes(args, plan)
    exchange, config, _ = make_exchange(args)
    result = exchange.update_isolated_margin(args.amount, args.coin)
    emit({"ok": True, "command": "isolated-margin", "submitted": True, **config, "result": result})


def command_close_market(args: argparse.Namespace) -> None:
    plan = {
        "command": "close-market",
        "coin": args.coin,
        "size": args.size,
        "slippage": args.slippage,
        "cloid": args.cloid,
    }
    require_yes(args, plan)
    exchange, config, Cloid = make_exchange(args)
    result = exchange.market_close(
        args.coin,
        sz=args.size,
        slippage=args.slippage,
        cloid=cloid_or_none(Cloid, args.cloid),
    )
    emit({"ok": True, "command": "close-market", "submitted": True, **config, "result": result})


def command_schedule_cancel(args: argparse.Namespace) -> None:
    if args.clear:
        cancel_time = None
    elif args.at_ms is not None:
        cancel_time = args.at_ms
    elif args.seconds is not None:
        cancel_time = int(time.time() * 1000) + int(args.seconds * 1000)
    else:
        raise ValueError("provide --clear, --at-ms, or --seconds")

    plan = {"command": "schedule-cancel", "time": cancel_time}
    require_yes(args, plan)
    exchange, config, _ = make_exchange(args)
    result = exchange.schedule_cancel(cancel_time)
    emit({"ok": True, "command": "schedule-cancel", "submitted": True, **config, "result": result})


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--network", choices=["mainnet", "testnet"], default=None)
    parser.add_argument("--account-address", default=None)
    parser.add_argument("--vault-address", default=None)
    parser.add_argument("--expires-after-ms", type=int, default=None)
    parser.add_argument("--yes", action="store_true", help="Required for state-changing actions.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hyperliquid_trade.py",
        description="Signed Hyperliquid exchange actions for Hermes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="Show non-secret runtime config.")
    add_common(p)
    p.set_defaults(func=command_status)

    p = sub.add_parser("limit", help="Place a limit order.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--side", required=True)
    p.add_argument("--size", type=float, required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--tif", default="Gtc")
    p.add_argument("--reduce-only", action="store_true")
    p.add_argument("--cloid", default=None)
    p.set_defaults(func=command_limit)

    p = sub.add_parser("market", help="Place an aggressive IOC market-style order.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--side", required=True)
    p.add_argument("--size", type=float, required=True)
    p.add_argument("--slippage", type=float, default=0.01)
    p.add_argument("--reduce-only", action="store_true")
    p.add_argument("--cloid", default=None)
    p.set_defaults(func=command_market)

    p = sub.add_parser("trigger", help="Place a trigger order, typically TP or SL.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--side", required=True)
    p.add_argument("--size", type=float, required=True)
    p.add_argument("--trigger-price", type=float, required=True)
    p.add_argument("--limit-price", type=float, default=None)
    p.add_argument("--is-market", action="store_true", default=True)
    p.add_argument("--tpsl", choices=["tp", "sl"], required=True)
    p.add_argument("--reduce-only", action="store_true")
    p.add_argument("--grouping", choices=["na", "normalTpsl", "positionTpsl"], default="positionTpsl")
    p.add_argument("--cloid", default=None)
    p.set_defaults(func=command_trigger)

    p = sub.add_parser("cancel", help="Cancel by order id.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--oid", type=int, required=True)
    p.set_defaults(func=command_cancel)

    p = sub.add_parser("cancel-cloid", help="Cancel by client order id.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--cloid", required=True)
    p.set_defaults(func=command_cancel_cloid)

    p = sub.add_parser("modify", help="Modify a resting order.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--oid", type=int, default=None)
    p.add_argument("--cloid", default=None)
    p.add_argument("--side", required=True)
    p.add_argument("--size", type=float, required=True)
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--tif", default="Gtc")
    p.add_argument("--reduce-only", action="store_true")
    p.add_argument("--new-cloid", default=None)
    p.set_defaults(func=command_modify)

    p = sub.add_parser("leverage", help="Update cross or isolated leverage.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--leverage", type=int, required=True)
    p.add_argument("--margin-mode", choices=["cross", "isolated"], required=True)
    p.set_defaults(func=command_leverage)

    p = sub.add_parser("isolated-margin", help="Add or remove isolated margin in USDC.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--amount", type=float, required=True)
    p.set_defaults(func=command_isolated_margin)

    p = sub.add_parser("close-market", help="Close an existing position at market.")
    add_common(p)
    p.add_argument("--coin", required=True)
    p.add_argument("--size", type=float, default=None)
    p.add_argument("--slippage", type=float, default=0.01)
    p.add_argument("--cloid", default=None)
    p.set_defaults(func=command_close_market)

    p = sub.add_parser("schedule-cancel", help="Schedule or clear dead-man cancel.")
    add_common(p)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--seconds", type=float)
    g.add_argument("--at-ms", type=int)
    g.add_argument("--clear", action="store_true")
    p.set_defaults(func=command_schedule_cancel)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except SystemExit:
        raise
    except Exception as exc:
        emit({"ok": False, "error": str(exc)}, 2)


if __name__ == "__main__":
    main()
