# FPL Edge — System Architecture

FPL Edge is an advanced Fantasy Premier League decision-support system built on a decoupled, deterministic analytics pipeline with an auxiliary grounded AI explainer layer.

```
+-----------------------------------------------------------------------+
|                             1. DATA ENGINE                            |
|       (FplOfficialProvider / DemoProvider / Snapshot Repository)       |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                     2. AVAILABILITY / xMINUTES ENGINE                 |
|  (P(start), P(sub), E(mins), Team-Level Probabilistic Reconciliation) |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                        3. PROJECTION ENGINE                           |
|       (Component xP: Goals, Assists, CS, Saves, Bonus + Monte Carlo)  |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                     4. PLANNING / OPTIMISATION ENGINE                 |
|     (PuLP MILP Solver: 1-5 GW Horizon, Top 5 Feasible Plans, HOLD)     |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                   5. STRATEGY / PERSONALISATION ENGINE                |
|      (Safe / Balanced / Aggressive Profiles, Effective Ownership)     |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                     6. EXPLANATION / AI ENGINE                        |
|  (Deterministic DECISION_CONTEXT Payload + Grounded LLM Explainer)    |
+-----------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                          7. WEB INTERFACE                             |
|          (Next.js, React, Tailwind CSS, Recharts, Football Pitch)     |
+-----------------------------------------------------------------------+
```

## Key Principles
1. **Separation of Concerns**: The LLM NEVER generates projections, injuries, or optimization solutions.
2. **Traceability**: Every recommendation can be traced backwards:
   Recommendation -> Optimizer decision -> Player xP -> xMinutes -> Features -> Source snapshot timestamp.
3. **No Leakage**: All projections specify an `as_of_timestamp` and use strictly pre-deadline snapshots.
4. **Offline Resiliency**: The system operates with full functionality using seed fallback datasets when the official API is unreachable.
