# FPL Edge — Model Card

## Model Details
- **Name**: FPL Edge Component Projection & MILP Optimization Engine
- **Version**: 1.0.0
- **Architecture**: Decoupled multi-stage pipeline
  1. Availability / xMinutes Probabilistic Engine (with Team-Level Sum-to-11 Reconciliation)
  2. Component expected points model (xP = Appearance + Goal xP + Assist xP + Clean Sheet xP + Save xP + Bonus xP - Deductions)
  3. Mixed Integer Linear Programming (MILP) optimization via PuLP

## Intended Use
Provides decision support for Fantasy Premier League managers, including transfer recommendations, captain selection, chip timing, and expected points forecasts.

## Model Evaluation Metrics
- **Mean Absolute Error (MAE)**: Points prediction error per position.
- **Minutes MAE**: Expected minutes prediction error.
- **Brier Score**: Probability error for 60+ minute appearances.
- **Spearman Rank Correlation**: Ranking accuracy across top targets.
- **Regret & Captain Efficiency**: Captain points loss relative to optimal choice.
