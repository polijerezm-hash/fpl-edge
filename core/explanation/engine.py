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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")

    def build_decision_context(
        self,
        manager_state: Dict[str, Any],
        recommendation_plan: Dict[str, Any],
        alternative_plans: List[Dict[str, Any]],
        player_lookup: Dict[int, Dict[str, Any]],
        as_of_timestamp: str = "",
        model_version: str = "1.0.0"
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
            return (
                f"**Captaincy Explanation**\n\n"
                f"**{cap_name}** is selected as captain for GW{gw1.get('gw', 5)}. "
                f"The model selects {cap_name} because they offer the highest expected points product "
                f"(expected minutes × component goal/assist probabilities) while maintaining high starting certainty."
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
            "Explain recommendations produced by deterministic models clearly."
        )
        user_prompt = f"DECISION_CONTEXT:\n{json.dumps(ctx, indent=2)}\n\nUSER QUESTION: {question}"

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return None
