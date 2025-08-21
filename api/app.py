import os
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from predict import NFLDFSPredictor

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
    global cached_predictions, last_update

    if cached_predictions is None or len(cached_predictions) == 0:
        return jsonify({"error": "No predictions available"}), 500

    try:
        # Get query parameters
        position = request.args.get("position", "ALL")
        min_salary = request.args.get("min_salary", 0, type=int)
        max_salary = request.args.get("max_salary", 50000, type=int)
        max_ownership = request.args.get("max_ownership", 100, type=float)

        # Work on a DataFrame copy
        df = cached_predictions.copy()

        if position != "ALL":
            df = df[df["position"] == position]

        df = df[
            (df["salary"] >= min_salary)
            & (df["salary"] <= max_salary)
            & (df["ownership"] <= max_ownership)
        ]

        predictions = df.to_dict(orient="records")

        return jsonify(
            {
                "predictions": predictions,
                "total_count": len(predictions),
                "last_update": last_update.isoformat() if last_update else None,
            }
        )

    except Exception as e:
        print(f"Error returning predictions: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    initialize_predictor()
    app.run(host="0.0.0.0", port=port, debug=True)
