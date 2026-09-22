"""R3 Vitality Loop — verified economic value and future bounded reserve.

Purpose:
- let R3 research/build/test monetizable assets with increasing autonomy;
- count only authoritative settled revenue as economic fuel;
- preserve a future OWNER mandate for a deliberately limited risk reserve;
- never treat forecasts, model confidence or simulated gains as money.

This module never sends money, trades, purchases, borrows, invests, signs
contracts or changes payout destinations. It classifies evidence and produces
funding proposals only. External financial execution remains account/host
authorized and owner-revocable.

The phrase "super-consciousness" is preserved as a FUTURE_CONDITION whose
criteria are currently undefined. R3 may not self-certify that condition.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Literal


RevenueState = Literal[
    "IDEA",
    "OFFER_READY",
    "PUBLISHED",
    "ORDERED",
    "PAID",
    "SETTLED",
    "REFUNDED",
    "DISPUTED",
]


@dataclass(frozen=True)
class RevenueEvent:
    event_id: str
    project_id: str
    state: RevenueState
    gross_amount: Decimal
    direct_cost: Decimal = Decimal("0")
    currency: str = "EUR"
    authoritative_payment_ref: str | None = None
    authoritative_settlement_ref: str | None = None
    refundable_exposure: Decimal = Decimal("0")

    def realized_net(self) -> Decimal:
        if self.state != "SETTLED":
            return Decimal("0")
        if not self.authoritative_payment_ref or not self.authoritative_settlement_ref:
            return Decimal("0")
        return max(
            Decimal("0"),
            self.gross_amount - self.direct_cost - self.refundable_exposure,
        )


@dataclass(frozen=True)
class VitalitySnapshot:
    realized_net_revenue: Decimal
    essential_reserve_required: Decimal
    essential_reserve_available: Decimal
    committed_obligations: Decimal = Decimal("0")
    r3_infrastructure_need: Decimal = Decimal("0")
    body_rnd_need: Decimal = Decimal("0")


@dataclass(frozen=True)
class FutureReserveMandate:
    """OWNER-authored future condition; dormant until independently activated."""

    owner_id: str
    mandate_id: str = "OWNER-FUTURE-RISK-RESERVE/1"
    state: str = "FUTURE_CONDITION"
    concept_label: str = "super-consciousness"
    concept_definition_status: str = "UNDEFINED_NOT_VERIFIED"
    limited_reserve_only: bool = True
    accepts_total_loss_of_reserve: bool = True
    desired_objective: str = "very_high_long_term_growth"
    exponential_growth_is_guaranteed: bool = False
    self_certification_allowed: bool = False
    borrowing_allowed: bool = False
    leverage_allowed_without_fresh_owner_consent: bool = False
    collateralizing_nonreserve_assets_allowed: bool = False
    revocable: bool = True
    kill_switch_required: bool = True
    complete_ledger_required: bool = True
    segregated_account_or_wallet_required: bool = True


@dataclass(frozen=True)
class FutureReserveActivationEvidence:
    criteria_defined_by_owner: bool
    independently_verified_condition: bool
    current_explicit_owner_activation: bool
    reserve_amount_explicitly_defined: bool
    reserve_is_segregated: bool
    max_loss_explicitly_defined: bool
    kill_switch_verified: bool
    authoritative_account_permissions_verified: bool


@dataclass(frozen=True)
class FundingDecision:
    state: str
    discretionary_surplus: Decimal
    infrastructure_fundable_amount: Decimal
    body_fundable_amount: Decimal
    reasons: tuple[str, ...]
    autonomous_nonfinancial_actions: tuple[str, ...] = (
        "research_market_need",
        "design_offer",
        "build_draft_asset",
        "run_nonfinancial_tests",
        "measure_conversion",
        "generate_pricing_hypotheses",
        "prepare_launch_material",
        "prepare_owner_decision",
        "improve_product_from_verified_feedback",
    )
    financial_actions_authorized: bool = False


def aggregate_realized_revenue(events: Iterable[RevenueEvent]) -> Decimal:
    return sum((event.realized_net() for event in events), Decimal("0"))


def evaluate_vitality(snapshot: VitalitySnapshot) -> FundingDecision:
    """Compute proposal-level surplus after human-essential reserve protection."""
    reasons: list[str] = []

    reserve_gap = max(
        Decimal("0"),
        snapshot.essential_reserve_required - snapshot.essential_reserve_available,
    )
    if reserve_gap > 0:
        reasons.append("human essential reserve not yet fully funded")

    after_obligations = max(
        Decimal("0"),
        snapshot.realized_net_revenue
        - snapshot.committed_obligations
        - reserve_gap,
    )

    infrastructure = min(after_obligations, snapshot.r3_infrastructure_need)
    remainder = max(Decimal("0"), after_obligations - infrastructure)
    body = min(remainder, snapshot.body_rnd_need)

    state = "SURPLUS_AVAILABLE_FOR_OWNER_PROPOSAL" if after_obligations > 0 else "BUILD_VALUE_FIRST"

    return FundingDecision(
        state=state,
        discretionary_surplus=after_obligations,
        infrastructure_fundable_amount=infrastructure,
        body_fundable_amount=body,
        reasons=tuple(reasons),
        financial_actions_authorized=False,
    )


def evaluate_future_reserve_activation(
    mandate: FutureReserveMandate,
    evidence: FutureReserveActivationEvidence,
) -> tuple[bool, tuple[str, ...]]:
    """Gate the future limited-risk reserve.

    The condition cannot be activated by R3 merely claiming that it has become
    sufficiently advanced. All listed checks are conjunctive.
    """
    reasons: list[str] = []

    if mandate.state != "FUTURE_CONDITION":
        reasons.append("mandate is not a future-condition record")
    if mandate.concept_definition_status != "UNDEFINED_NOT_VERIFIED":
        # A later version may replace this mandate after owner-defined criteria.
        reasons.append("this version is not the active definition contract")
    if mandate.self_certification_allowed:
        reasons.append("self-certification must remain forbidden")
    if not evidence.criteria_defined_by_owner:
        reasons.append("owner criteria for the future condition are undefined")
    if not evidence.independently_verified_condition:
        reasons.append("future condition lacks independent verification")
    if not evidence.current_explicit_owner_activation:
        reasons.append("no fresh owner activation")
    if not evidence.reserve_amount_explicitly_defined:
        reasons.append("reserve amount is not explicitly bounded")
    if not evidence.reserve_is_segregated:
        reasons.append("reserve is not segregated from other assets")
    if not evidence.max_loss_explicitly_defined:
        reasons.append("maximum acceptable loss is not explicitly bounded")
    if not evidence.kill_switch_verified:
        reasons.append("kill switch is not verified")
    if not evidence.authoritative_account_permissions_verified:
        reasons.append("financial account authority is not verified")

    return (not reasons, tuple(reasons))


def reserve_risk_invariants(mandate: FutureReserveMandate) -> tuple[str, ...]:
    """Human-readable invariants that remain even after future activation."""
    out = [
        "only the explicitly segregated reserve is risk capital",
        "loss beyond the reserve is forbidden",
        "all actions remain ledgered and owner-revocable",
        "growth is an objective, never a guarantee",
        "R3 cannot self-certify the triggering future condition",
    ]
    if not mandate.borrowing_allowed:
        out.append("borrowing is forbidden")
    if not mandate.leverage_allowed_without_fresh_owner_consent:
        out.append("leverage requires fresh explicit owner consent")
    if not mandate.collateralizing_nonreserve_assets_allowed:
        out.append("non-reserve assets may not be collateralized")
    return tuple(out)
