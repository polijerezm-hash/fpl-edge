# FPL Edge — Model Card

## Model Details
- **Name**: FPL Edge Component Projection & MILP Optimization Engine
- **Version**: 3.0.0
- **Architecture**: Decoupled multi-stage pipeline
  1. Availability / xMinutes Probabilistic Engine (with Team-Level Sum-to-11 Reconciliation)
  2. Recent-form xG/xA EWMA with a five-gameweek half-life and sample-size shrinkage
  3. Hybrid expected-points blend: 50% bookmaker-implied xP, 35% EWMA xP, and 15% official `ep_next` when all three sources are available
  4. Multi-period MILP optimization via PuLP, including exact free-transfer rollover, hits, ordered bench, and native WC/FH/BB/TC decisions

## Degraded modes

- Without bookmaker data, available source weights are re-normalized rather than treated as zero.
- Without an LLM key, recommendations use a deterministic grounded explanation.
- Live managers must confirm the reconstructed free-transfer balance before optimization.

## Intended Use
Provides decision support for Fantasy Premier League managers, including transfer recommendations, captain selection, chip timing, and expected points forecasts.

## Model Evaluation Metrics
- **Mean Absolute Error (MAE)**: Points prediction error per position.
- **Minutes MAE**: Expected minutes prediction error.
- **Brier Score**: Probability error for 60+ minute appearances.
- **Spearman Rank Correlation**: Ranking accuracy across top targets.
- **Regret & Captain Efficiency**: Captain points loss relative to optimal choice.
