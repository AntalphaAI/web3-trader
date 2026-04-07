#!/usr/bin/env python3
"""
Hyperliquid Risk Control Engine

Three-tier trade confirmation:
  - SMALL  (<$100):   auto-execute, notify after
  - MEDIUM ($100-1000): single confirmation required
  - LARGE  (>$1000 or leverage >10x): double confirmation required

Configuration is stored in ~/.web3-trader/hl_risk.yaml
Users can customize thresholds via CLI: `hl_cli.py risk-config`
"""

import os
import sys
import json
import yaml
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

# ── Defaults ─────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "thresholds": {
        "small_max_usd": 100,       # < this = auto-execute
        "medium_max_usd": 1000,     # < this = single confirm; >= this = double confirm
        "high_leverage_x": 10,      # >= this leverage = always double confirm
    },
    "enabled": True,
    "auto_execute_small": True,
}

CONFIG_PATH = os.path.expanduser("~/.web3-trader/hl_risk.yaml")


class RiskLevel(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class RiskAssessment:
    """Result of risk evaluation for a trade."""
    level: RiskLevel
    estimated_usd: float
    leverage: Optional[int]
    reasons: list
    requires_confirmation: int  # 0=auto, 1=single, 2=double


# ── Config Management ────────────────────────────────────────────────

def load_config() -> Dict:
    """Load risk config from file, fallback to defaults."""
    import copy
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                user_cfg = yaml.safe_load(f) or {}
            # Merge with defaults (deep copy to avoid mutation)
            cfg = copy.deepcopy(DEFAULT_CONFIG)
            if "thresholds" in user_cfg:
                cfg["thresholds"].update(user_cfg["thresholds"])
            if "enabled" in user_cfg:
                cfg["enabled"] = user_cfg["enabled"]
            if "auto_execute_small" in user_cfg:
                cfg["auto_execute_small"] = user_cfg["auto_execute_small"]
            return cfg
        except Exception:
            return copy.deepcopy(DEFAULT_CONFIG)
    return copy.deepcopy(DEFAULT_CONFIG)


def save_config(cfg: Dict) -> str:
    """Save risk config to file. Returns the path."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    os.chmod(CONFIG_PATH, 0o600)
    return CONFIG_PATH


def get_config_summary(cfg: Optional[Dict] = None) -> str:
    """Human-readable config summary."""
    cfg = cfg or load_config()
    t = cfg["thresholds"]
    status = "✅ 已启用" if cfg.get("enabled", True) else "❌ 已禁用"
    auto = "是" if cfg.get("auto_execute_small", True) else "否"
    return (
        f"🛡️ Hyperliquid 风控配置 ({status})\n"
        f"\n"
        f"   📊 三级确认阈值:\n"
        f"   ├─ 🟢 小额自动: < ${t['small_max_usd']:,}\n"
        f"   ├─ 🟡 中额单确认: ${t['small_max_usd']:,} - ${t['medium_max_usd']:,}\n"
        f"   ├─ 🔴 大额双确认: ≥ ${t['medium_max_usd']:,}\n"
        f"   └─ ⚠️ 高杠杆双确认: ≥ {t['high_leverage_x']}x\n"
        f"\n"
        f"   小额自动执行: {auto}\n"
        f"   配置文件: {CONFIG_PATH}"
    )


# ── Risk Assessment ──────────────────────────────────────────────────

def assess_trade(
    size: float,
    price: float,
    leverage: Optional[int] = None,
    is_close: bool = False,
    cfg: Optional[Dict] = None,
) -> RiskAssessment:
    """
    Evaluate trade risk level.

    Args:
        size: Order size (e.g. 0.1 ETH)
        price: Current market price
        leverage: Leverage multiplier (None = not applicable)
        is_close: True if closing a position (always auto)
        cfg: Risk config (loads from file if None)

    Returns:
        RiskAssessment with level, reasons, and confirmation requirement
    """
    cfg = cfg or load_config()

    if not cfg.get("enabled", True):
        return RiskAssessment(
            level=RiskLevel.SMALL,
            estimated_usd=abs(size) * price,
            leverage=leverage,
            reasons=["风控已禁用"],
            requires_confirmation=0,
        )

    t = cfg["thresholds"]
    estimated_usd = abs(size) * price
    reasons = []

    # Closing positions are always auto (reduce risk)
    if is_close:
        return RiskAssessment(
            level=RiskLevel.SMALL,
            estimated_usd=estimated_usd,
            leverage=leverage,
            reasons=["平仓操作，自动执行"],
            requires_confirmation=0,
        )

    # Determine level
    level = RiskLevel.SMALL
    confirms = 0

    # Check amount thresholds
    if estimated_usd >= t["medium_max_usd"]:
        level = RiskLevel.LARGE
        confirms = 2
        reasons.append(f"金额 ${estimated_usd:,.2f} ≥ ${t['medium_max_usd']:,} (大额)")
    elif estimated_usd >= t["small_max_usd"]:
        level = RiskLevel.MEDIUM
        confirms = 1
        reasons.append(f"金额 ${estimated_usd:,.2f} ≥ ${t['small_max_usd']:,} (中额)")
    else:
        reasons.append(f"金额 ${estimated_usd:,.2f} < ${t['small_max_usd']:,} (小额)")

    # High leverage overrides to LARGE
    if leverage is not None and leverage >= t["high_leverage_x"]:
        if level != RiskLevel.LARGE:
            level = RiskLevel.LARGE
            confirms = 2
        reasons.append(f"杠杆 {leverage}x ≥ {t['high_leverage_x']}x (高杠杆)")

    # Small trades: auto-execute if enabled
    if level == RiskLevel.SMALL and cfg.get("auto_execute_small", True):
        confirms = 0

    return RiskAssessment(
        level=level,
        estimated_usd=estimated_usd,
        leverage=leverage,
        reasons=reasons,
        requires_confirmation=confirms,
    )


def format_risk_assessment(ra: RiskAssessment) -> str:
    """Format risk assessment for user display."""
    emoji = {"small": "🟢", "medium": "🟡", "large": "🔴"}
    label = {"small": "小额自动", "medium": "中额", "large": "大额"}
    confirm_text = {0: "自动执行", 1: "需要确认一次", 2: "需要确认两次"}

    lines = [
        f"{emoji[ra.level.value]} 风控评估: {label[ra.level.value]} (${ra.estimated_usd:,.2f})",
    ]
    if ra.leverage:
        lines.append(f"   杠杆: {ra.leverage}x")
    lines.append(f"   确认要求: {confirm_text[ra.requires_confirmation]}")
    for r in ra.reasons:
        lines.append(f"   • {r}")
    return "\n".join(lines)


def format_risk_preview(
    action: str,
    coin: str,
    side: str,
    size: float,
    price: float,
    ra: RiskAssessment,
    extra: Optional[Dict] = None,
) -> str:
    """
    Format a complete trade preview with risk assessment.
    Used by Agent to show user before confirmation.
    """
    emoji = {"small": "🟢", "medium": "🟡", "large": "🔴"}
    level_label = {"small": "LOW", "medium": "MEDIUM", "large": "HIGH"}

    lines = [
        f"{'─' * 40}",
        f"⚡ {action} 交易预览",
        f"{'─' * 40}",
        f"   币种: {coin}",
        f"   方向: {side}",
        f"   数量: {size}",
        f"   价格: ${price:,.2f}",
        f"   价值: ${ra.estimated_usd:,.2f}",
    ]

    if ra.leverage:
        lines.append(f"   杠杆: {ra.leverage}x")

    if extra:
        for k, v in extra.items():
            lines.append(f"   {k}: {v}")

    lines.extend([
        f"{'─' * 40}",
        f"   {emoji[ra.level.value]} 风险等级: {level_label[ra.level.value]}",
    ])
    for r in ra.reasons:
        lines.append(f"   • {r}")
    lines.append(f"{'─' * 40}")

    return "\n".join(lines)


# ── Balance Pre-check ────────────────────────────────────────────────

def check_balance_sufficient(
    client,  # HyperliquidClient
    coin: str,
    size: float,
    price: float,
    leverage: Optional[int] = None,
    is_buy: bool = True,
) -> Tuple[bool, str]:
    """
    Pre-check if account has sufficient margin for a trade.

    Returns:
        (sufficient: bool, message: str)
    """
    address = client.effective_address
    if not address:
        return False, "❌ 无法确定账户地址，请检查配置"

    try:
        state = client.get_user_state(address)
    except Exception as e:
        return False, f"❌ 无法查询账户状态: {e}"

    margin = state.get("marginSummary", {})
    account_value = float(margin.get("accountValue", "0"))
    total_margin_used = float(margin.get("totalMarginUsed", "0"))
    withdrawable = float(state.get("withdrawable", "0"))

    # Estimate required margin
    notional = abs(size) * price
    effective_leverage = leverage if leverage else 1
    # Rough margin estimate: notional / leverage + some buffer for fees
    required_margin = (notional / effective_leverage) * 1.02  # 2% buffer for fees

    available_margin = account_value - total_margin_used

    if available_margin < required_margin:
        return False, (
            f"❌ 保证金不足\n"
            f"   账户价值: ${account_value:,.2f}\n"
            f"   已用保证金: ${total_margin_used:,.2f}\n"
            f"   可用保证金: ${available_margin:,.2f}\n"
            f"   预估所需: ${required_margin:,.2f}\n"
            f"   缺口: ${required_margin - available_margin:,.2f}"
        )

    return True, (
        f"✅ 保证金充足\n"
        f"   可用: ${available_margin:,.2f} | 预估所需: ${required_margin:,.2f}"
    )


# ── Failure Recovery ─────────────────────────────────────────────────

def check_fill_after_failure(
    client,  # HyperliquidClient
    coin: str,
    expected_size: float,
    is_buy: bool,
    time_window_ms: int = 10000,
) -> Tuple[bool, Optional[Dict]]:
    """
    After a failed order, check if it actually filled (network issue vs real failure).

    Args:
        client: HyperliquidClient
        coin: Trading pair
        expected_size: Expected fill size
        is_buy: Buy or sell
        time_window_ms: Look back this many ms (default 10s)

    Returns:
        (was_filled: bool, fill_info: Optional[Dict])
    """
    import time as _time

    address = client.effective_address
    if not address:
        return False, None

    try:
        fills = client.get_user_fills(address)
    except Exception:
        return False, None

    now_ms = int(_time.time() * 1000)
    cutoff = now_ms - time_window_ms
    expected_side = "B" if is_buy else "A"

    for fill in fills:
        fill_time = fill.get("time", 0)
        if fill_time < cutoff:
            continue
        if fill.get("coin") != coin:
            continue
        if fill.get("side") != expected_side:
            continue
        fill_size = float(fill.get("sz", "0"))
        # Fuzzy match: within 10% of expected
        if abs(fill_size - abs(expected_size)) / max(abs(expected_size), 0.0001) < 0.1:
            return True, {
                "coin": fill.get("coin"),
                "side": "BUY" if is_buy else "SELL",
                "size": fill.get("sz"),
                "price": fill.get("px"),
                "fee": fill.get("fee"),
                "time": fill.get("time"),
                "oid": fill.get("oid"),
            }

    return False, None


def format_recovery_result(was_filled: bool, fill_info: Optional[Dict]) -> str:
    """Format fill-check result for user."""
    if was_filled and fill_info:
        return (
            f"⚠️ 订单报错但实际已成交！\n"
            f"   {fill_info['coin']} {fill_info['side']} | "
            f"成交价: ${float(fill_info['price']):,.2f} | "
            f"数量: {fill_info['size']} | 手续费: {fill_info['fee']}\n"
            f"   ⚠️ 请勿重复下单"
        )
    return "✅ 确认未成交，可以安全重试"


# ── CLI Config Command ───────────────────────────────────────────────

def cmd_risk_config(args):
    """Interactive risk config setup."""
    cfg = load_config()

    if args.show:
        print(get_config_summary(cfg))
        if args.json:
            print(json.dumps(cfg, indent=2))
        return

    if args.reset:
        import copy
        cfg = copy.deepcopy(DEFAULT_CONFIG)
        path = save_config(cfg)
        print(f"✅ 风控配置已重置为默认值")
        print(get_config_summary(cfg))
        return

    # Update specific values
    changed = False

    if args.small is not None:
        cfg["thresholds"]["small_max_usd"] = args.small
        changed = True

    if args.medium is not None:
        cfg["thresholds"]["medium_max_usd"] = args.medium
        changed = True

    if args.leverage is not None:
        cfg["thresholds"]["high_leverage_x"] = args.leverage
        changed = True

    if args.enable is not None:
        cfg["enabled"] = args.enable
        changed = True

    if args.auto_small is not None:
        cfg["auto_execute_small"] = args.auto_small
        changed = True

    if changed:
        # Validate: small < medium
        if cfg["thresholds"]["small_max_usd"] >= cfg["thresholds"]["medium_max_usd"]:
            print("❌ 错误: 小额阈值必须小于中额阈值", file=sys.stderr)
            sys.exit(1)
        path = save_config(cfg)
        print(f"✅ 风控配置已更新")
    else:
        print("ℹ️ 未指定修改项，显示当前配置:")

    print(get_config_summary(cfg))
