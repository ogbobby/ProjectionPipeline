import os
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from predict import NFLDFSPredictor

# Floor/Ceiling multipliers (tunable)
FLOOR_MULTIPLIER = 1.0   # use 1.0 for conservative floor (cash games), higher for riskier
CEILING_MULTIPLIER = 1.5 # use >1.0 to widen upside range (e.g., 1.5–2.0 for GPPs)


# ----------------------------------------------------------------------------
# Flask App Setup
# ----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

predictor = None
cached_predictions = None
last_update = None

# ----------------------------------------------------------------------------
# Helpers for JSON safety
# ----------------------------------------------------------------------------
def sanitize_for_json(obj):
    """Convert pandas/numpy objects into JSON-serializable Python types."""

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.tolist()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(i) for i in obj]

    return obj

# ----------------------------------------------------------------------------
# Initialization
# ----------------------------------------------------------------------------
def initialize_predictor():
    """Initialize the predictor and pre-cache predictions."""
    global predictor, cached_predictions, last_update

    try:
        print("🔄 Initializing predictor with real scraped NFL data...")
        predictor = NFLDFSPredictor(season=2024)
        cached_predictions = predictor.run_full_pipeline()

        if cached_predictions is None or len(cached_predictions) == 0:
            raise RuntimeError("No predictions generated")

        last_update = datetime.utcnow()
        print(f"✅ Predictor initialized. {len(cached_predictions)} predictions cached.")

    except Exception as e:
        print(f"CRITICAL ERROR initializing predictor: {e}")
        traceback.print_exc()
        cached_predictions = None


# ----------------------------------------------------------------------------
# API Routes
# ----------------------------------------------------------------------------
@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    try:
        if predictor.cached_predictions is None:
            return jsonify({"error": "Predictions not ready"}), 503

        df = predictor.cached_predictions.copy()

        # --- Allow override of floor/ceiling multipliers ---
        floor_mult = request.args.get("floor_mult", default=FLOOR_MULTIPLIER, type=float)
        ceiling_mult = request.args.get("ceiling_mult", default=CEILING_MULTIPLIER, type=float)

        if "player_std" in df.columns:
            df["floor"] = (df["prediction"] - floor_mult * df["player_std"]).clip(lower=0)
            df["ceiling"] = df["prediction"] + ceiling_mult * df["player_std"]

        # --- Optional: Salary filters from frontend ---
        min_salary = request.args.get("min_salary", type=int)
        max_salary = request.args.get("max_salary", type=int)
        if min_salary is not None:
            df = df[df["salary"] >= min_salary]
        if max_salary is not None:
            df = df[df["salary"] <= max_salary]

        # ✅ Sanitize values so JSON is always valid
        clean_df = df.replace([np.inf, -np.inf], None).where(pd.notnull(df), None)

        # ✅ Always return wrapped JSON object
        return jsonify({
            "predictions": clean_df.to_dict(orient="records"),
            "total_count": len(clean_df),
            "last_update": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# @app.route("/api/predictions", methods=["GET"])
# def get_predictions():
#     try:
#         if predictor.cached_predictions is None:
#             return jsonify({"error": "Predictions not ready"}), 503

#         df = predictor.cached_predictions.copy()

#         # --- Optional: apply salary filters from frontend query params ---
#         min_salary = request.args.get("min_salary", type=int)
#         max_salary = request.args.get("max_salary", type=int)

#         if min_salary is not None:
#             df = df[df["salary"].fillna(0) >= min_salary]
#         if max_salary is not None:
#             df = df[df["salary"].fillna(0) <= max_salary]

#         # --- Rename columns for frontend compatibility ---
#         df = df.rename(columns={
#             "name": "Name",
#             "position": "Pos",
#             "team": "Team",
#             "salary": "Salary",
#             "projection": "Projection",
#             "ownership": "Ownership",
#             "value": "Value",
#             "leverage": "Leverage"
#         })

#         # --- Ensure only required columns are returned ---
#         output_columns = ["Name", "Pos", "Team", "Salary", "Projection", "Ownership", "Value", "Leverage"]
#         df = df[[col for col in output_columns if col in df.columns]]

#         return jsonify(df.to_dict(orient="records"))

#     except Exception as e:
#         print(f"Error returning predictions: {e}")
#         #return jsonify({"error": str(e)}), 500
#         return jsonify(df.to_dict(orient="records")), 200


# ----------------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    initialize_predictor()
    app.run(host="0.0.0.0", port=port, debug=True)
