import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional

class GroundedExplainerEngine:
    """
    Produces deterministic DECISION_CONTEXT payloads and grounded Q&A explanations.
    Uses LLM API if configured, otherwise falls back to deterministic template explanations.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-6-sol")

    def build_decision_context(
        self,
        manager_state: Dict[str, Any],
        recommendation_plan: Dict[str, Any],
        alternative_plans: List[Dict[str, Any]],
        player_lookup: Dict[int, Dict[str, Any]],
        as_of_timestamp: str = "",
        model_version: str = "2.0.0",
        captaincy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates the standardized, immutable DECISION_CONTEXT object.
        """
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "as_of_timestamp": as_of_timestamp or datetime.utcnow().isoformat() + "Z",
            "model_version": model_version,
            "manager": manager_state,
            "recommendation": recommendation_plan,
            "alternatives": alternative_plans,
            "players": player_lookup,
            "captaincy": captaincy or {},
            "allowed_player_ids": sorted(int(pid) for pid in player_lookup.keys()),
            "constraints": {
                "max_club": 3,
                "hit_cost": 4,
                "budget_bank": manager_state.get("bank", 0.0)
            }
        }

    def explain_decision(
        self,
        question: str,
        decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Answers user Q&A strictly grounded in the supplied DECISION_CONTEXT object.
        """
        # 1. Try LLM API if key is present
        if self.api_key:
            try:
                explanation = self._call_llm_api(question, decision_context)
                if explanation:
                    return {
                        "mode": "llm_grounded",
                        "answer": explanation,
                        "decision_context": decision_context
                    }
            except Exception:
                pass

        # 2. Deterministic Template Fallback Explainer
        explanation = self._generate_template_explanation(question, decision_context)
        return {
            "mode": "deterministic_template",
            "answer": explanation,
            "decision_context": decision_context
        }

    def _generate_template_explanation(self, question: str, ctx: Dict[str, Any]) -> str:
        rec = ctx.get("recommendation", {})
        alts = ctx.get("alternatives", [])
        players = ctx.get("players", {})
        captaincy = ctx.get("captaincy", {})

        gain = rec.get("gain_vs_hold", 0.0)
        final_bank = rec.get("final_bank", 0.0)
        hits = rec.get("hits", 0)
        gw1 = rec.get("gameweeks", [{}])[0] if rec.get("gameweeks") else {}
        
        t_in = gw1.get("transfers_in", [])
        t_out = gw1.get("transfers_out", [])
        cap_id = gw1.get("captain")

        t_in_names = [players.get(str(pid), {}).get("web_name", f"Player #{pid}") for pid in t_in]
        t_out_names = [players.get(str(pid), {}).get("web_name", f"Player #{pid}") for pid in t_out]
        cap_name = players.get(str(cap_id), {}).get("web_name", f"Player #{cap_id}")

        q_lower = question.lower()

        if "why" in q_lower or "plan" in q_lower or "recommend" in q_lower:
            if not t_in:
                return (
                    f"**Strategic Decision: ROLL / HOLD TRANSFER**\n\n"
                    f"• **Expected Horizon Gain**: Preserving your free transfer provides higher expected future utility (+{gain} xP vs forced moves).\n"
                    f"• **Bank Preserved**: £{final_bank}m retained for future fixture swings.\n"
                    f"• **Captaincy**: {cap_name} is selected as captain based on highest expected points and minutes security.\n"
                    f"• **Hit Cost Avoided**: 0 pts spent on transfer hits."
                )
            else:
                return (
                    f"**Recommended Move: {', '.join(t_out_names)} → {', '.join(t_in_names)}**\n\n"
                    f"1. **Expected Points Gain**: Plan {rec.get('plan_code', 'A')} projects **+{gain} xP net gain** over holding.\n"
                    f"2. **Transfer Hits**: {hits} hits (-{hits * 4} pts).\n"
                    f"3. **Remaining Bank**: £{final_bank}m.\n"
                    f"4. **Captain Choice**: {cap_name} offers the strongest floor/ceiling projection for GW{gw1.get('gw', 5)}."
                )

        if "captain" in q_lower:
            captain_pick = captaincy.get("diamond") or {}
            if not captain_pick:
                return (
                    "**Captaincy check failed safely**\n\n"
                    "There is no eligible outfield captain with sufficient expected minutes and start probability in the current snapshot. "
                    "Refresh the data or review the lineup before setting an armband."
                )
            cap_name = captain_pick.get("web_name", cap_name)
            return (
                f"**Captaincy Explanation**\n\n"
                f"**{cap_name}** is the balanced captain for GW{gw1.get('gw', 5)} at "
                f"{captain_pick.get('mean_xp', 0)} xP, {captain_pick.get('xmins', 0)} expected minutes and a "
                f"{round(captain_pick.get('start_prob', 0) * 100)}% start probability. "
                f"Only eligible outfield starters are considered."
            )

        if "compare" in q_lower or "beat" in q_lower:
            alt1 = alts[0] if alts else rec
            diff = round(rec.get("expected_points", 0) - alt1.get("expected_points", 0), 2)
            return (
                f"**Plan Comparison (Plan A vs Plan B)**\n\n"
                f"• **Plan A Expected Score**: {rec.get('expected_points', 0)} xP\n"
                f"• **Plan B Expected Score**: {alt1.get('expected_points', 0)} xP\n"
                f"• **Marginal Gain**: Plan A outranks Plan B by **+{diff} xP**.\n"
                f"• **Trade-off**: Plan A provides stronger starting XI expected score while preserving £{final_bank}m in bank."
            )

        # Default Grounded Context Summary
        return (
            f"**Model Grounded Analysis**\n\n"
            f"Based on as_of_timestamp `{ctx.get('as_of_timestamp')}` (Model v{ctx.get('model_version')}):\n"
            f"• Top Recommendation: Plan {rec.get('plan_code', 'A')} ({rec.get('expected_points')} xP)\n"
            f"• Transfers in GW{gw1.get('gw', 5)}: {', '.join(t_in_names) if t_in else 'None (ROLL)'}\n"
            f"• Captain: {cap_name}\n"
            f"• Net gain vs ROLL: +{gain} xP"
        )

    def _call_llm_api(self, question: str, ctx: Dict[str, Any]) -> Optional[str]:
        system_prompt = (
            "You are an analytical Fantasy Premier League assistant.\n"
            "Use ONLY information contained inside DECISION_CONTEXT.\n"
            "Never invent expected points, injuries, availability, prices, fixtures, probabilities, or optimizer outputs.\n"
            "Never recommend or mention a player who is absent from allowed_player_ids.\n"
            "For captain questions, only use captaincy.ranked; goalkeepers and rejected candidates are forbidden.\n"
            "If the context cannot answer safely, state that clearly. Explain recommendations produced by deterministic models clearly."
        )
        user_prompt = f"DECISION_CONTEXT:\n{json.dumps(ctx, indent=2)}\n\nUSER QUESTION: {question}"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "reasoning": {"effort": "medium"},
            "text": {"verbosity": "low"},
        }
        resp = requests.post("https://api.openai.com/v1/responses", headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("output_text"):
                return data["output_text"]
            parts = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text" and content.get("text"):
                        parts.append(content["text"])
            return "\n".join(parts) or None
        return None
