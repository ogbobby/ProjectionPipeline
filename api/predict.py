import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
import warnings

# Floor/Ceiling multipliers (tunable)
FLOOR_MULTIPLIER = 1.0   # use 1.0 for conservative floor (cash games), higher for riskier
CEILING_MULTIPLIER = 1.5 # use >1.0 to widen upside range (e.g., 1.5–2.0 for GPPs)

# Add the scripts directory to path to import our scrapers
current_dir = os.path.dirname(__file__)
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.append(scripts_dir)
salaryPath = "/home/iamgeneral/Documents/NewRepo/ProjectionPipeline/api/data/"
# Scrapers
try:
    from nflpyStats import GetQBData, GetRBData, GetWRData, GetTEData, GetDepthCharts
    from playerStatScraper import redZonePassing, redZoneRushing, redZoneReceiving, PosPtsperWeek, boomBust
    from teamScrapers import TurnDiff, PenDiff, TeamScoring, targetDistro, Schedule2025, teamDEFData, advancedDEFData, PlaySelection, scrapDVOA, passingDEFData, rushingDEFData#,offPlays
    from bs4 import Comment
    print("Successfully imported all scrapers")
except Exception as e:
    print(f"⚠️ Error importing scrapers: {e}")

# ------------------ Utility ------------------

def _coerce_numeric(df, exclude=None):
    if exclude is None:
        exclude = []
    for col in df.columns:
        if col not in exclude:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                pass
    return df

def sanitize_for_json(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.fillna(0).replace([np.inf, -np.inf], 0).to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.fillna(0).replace([np.inf, -np.inf], 0).tolist()
    if isinstance(obj, np.ndarray):
        return np.nan_to_num(obj).tolist()
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(i) for i in obj]
    return obj
# -----------------------Salary csv Loader -------------------

def load_salary_csv(path=salaryPath):
    """Load salary data and normalize column names."""
    if not os.path.exists(path):
        print(f"⚠️ Salary file not found: {path}")
        return pd.DataFrame()

    df = pd.read_csv(path)
    print(f"✅ Loaded salary file {path}, shape={df.shape}")
    print(f"Columns before normalization: {df.columns.tolist()}")

    # Normalize columns
    df.columns = df.columns.str.lower().str.strip()
    rename_map = {
        "name": "name",
        "player_name": "name",
        "teamabbrev": "team",
        "team": "team",
        "position": "position",
        "salary": "salary",
        "dk_salary": "salary"
    }
    df.rename(columns=rename_map, inplace=True)

    required_cols = {"name", "team", "position", "salary"}
    if not required_cols.issubset(df.columns):
        print(f"⚠️ Salary file missing required columns. Found {df.columns.tolist()}")
        return pd.DataFrame()

    df["name"] = df["name"].astype(str).str.strip().str.title()
    df["team"] = df["team"].astype(str).str.upper()
    df["position"] = df["position"].astype(str).str.upper()
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce").fillna(0).astype(int)

    print(f"✅ Normalized salary data, shape={df.shape}")
    return df
# ------------------ Predictor ------------------

class NFLDFSPredictor:
    def __init__(self, season=2024):
        self.season = season
        self.positions = ["QB", "RB", "WR", "TE"]
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}

    def load_player_data(self):
        dfs = []
        for fn in [GetQBData, GetRBData, GetWRData, GetTEData]:
            try:
                df = fn()
                if df is not None and not df.empty:
                    dfs.append(df)
            except Exception as e:
                print(f"⚠️ Error in {fn.__name__}: {e}")
        if not dfs:
            return pd.DataFrame([
                {"name": "Mock QB", "recent_team": "NE", "position": "QB", "salary": 5000},
                {"name": "Mock RB", "recent_team": "DAL", "position": "RB", "salary": 5000},
                {"name": "Mock WR", "recent_team": "KC", "position": "WR", "salary": 5000},
                {"name": "Mock TE", "recent_team": "SF", "position": "TE", "salary": 5000},
            ])
        return pd.concat(dfs, ignore_index=True)
    
    def create_features(self):
        """
        Build the full player feature set for the given season.
        Pulls player stats, merges team/positional data, coerces numeric columns, 
        and ensures positions are preserved.
        """
        season = self.season
        print(f"Creating features for season {season}...")

        # -------------------------------
        # 1. Load Base Player Data
        # -------------------------------
        try:
            qbs = GetQBData()
            rbs = GetRBData()
            wrs = GetWRData()
            tes = GetTEData()

            players = pd.concat([qbs, rbs, wrs, tes], ignore_index=True)
            print(f"✅ Loaded player data, shape={players.shape}")
        except Exception as e:
            raise RuntimeError(f"CRITICAL ERROR: Failed to load player data → {e}")

        # -------------------------------
        # 2. Merge External Features (Team & Positional)
        # -------------------------------
        def safe_merge(base, func, key, label, *args):
            """Try merging additional feature sets and log errors without breaking pipeline."""
            try:
                df = func(*args)
                if df is not None and not df.empty:
                    base = base.merge(df, on=key, how="left")
                    print(f"✅ Merged {label} on '{key}' → players.shape={base.shape}")
                else:
                    print(f"⚠️ {label} returned no usable data")
            except Exception as e:
                print(f"⚠️ Error in {label}: {e}")
            return base

        # Merge all features that require year
        players = safe_merge(players, redZonePassing, "name", "redZonePassing", season)
        players = safe_merge(players, redZoneRushing, "name", "redZoneRushing", season)
        players = safe_merge(players, redZoneReceiving, "name", "redZoneReceiving", season)
        players = safe_merge(players, boomBust, "name", "boomBust", season)
        players = safe_merge(players, TurnDiff, "team", "TurnDiff", season)
        players = safe_merge(players, PenDiff, "team", "PenDiff", season)
        players = safe_merge(players, TeamScoring, "team", "TeamScoring", season)
        players = safe_merge(players, targetDistro, "team", "targetDistro", season)
        players = safe_merge(players, teamDEFData, "team", "teamDEFData", season)
        players = safe_merge(players, advancedDEFData, "team", "advancedDEFData", season)

        # Merge DVOA by position (requires year and pos)
        for pos in ["QB", "RB", "WR", "TE"]:
            players = safe_merge(players, scrapDVOA, "team", f"DVOA_{pos}", season, pos)

        # -------------------------------
        # 3. Ensure `position` column is preserved as uppercase strings
        # -------------------------------
        if "position" in players.columns:
            players["position"] = players["position"].astype(str).str.upper()

        # -------------------------------
        # 4. Convert All Columns to Numeric Where Possible (EXCEPT identifiers)
        # -------------------------------
        non_numeric_cols = {"position", "name", "team"}
        for col in list(players.columns):
            if col not in non_numeric_cols:
                try:
                    players[col] = pd.to_numeric(players[col], errors="coerce")
                except Exception:
                    print(f"⚠️ Could not convert column: {col}")

        # -------------------------------
        # 5. Drop rows missing essential info
        # -------------------------------
        players.dropna(subset=["name", "team", "position"], inplace=True)

        # -------------------------------
        # 6. Validate Position Distribution
        # -------------------------------
        valid_positions = ["QB", "RB", "WR", "TE"]
        print("Position distribution before cleaning:")
        print(players["position"].value_counts())

        players = players[players["position"].isin(valid_positions)].copy()

        # -------------------------------
        # 7. Final Cleanup & Fill Missing Values
        # -------------------------------
        players.fillna(0, inplace=True)
        print(f"✨ Final features shape: {players.shape}")

        #players = players.drop_duplicates(subset=["name", "team", "position"], keep="first")
        #print(f"✨ Final features shape after deduplication: {players.shape}")

        return players
    
    def train_models(self, X, y, position):
        """Train GradientBoostingRegressor models safely, even if data is incomplete."""
        #from sklearn.ensemble import GradientBoostingRegressor
        #from sklearn.preprocessing import StandardScaler
        #import numpy as np

        # Replace NaN with 0 in both X and y
        X = pd.DataFrame(X).fillna(0)
        y = pd.Series(y).fillna(0)

        # If no data, return empty model/scaler
        if X.empty or len(y) == 0:
            print(f"⚠️ No usable data for {position}, skipping training.")
            return {}, None

        scaler = StandardScaler()
        try:
            X_scaled = scaler.fit_transform(X)
        except ValueError:
            print(f"⚠️ Failed to scale X for {position}, skipping.")
            return {}, None

        model = GradientBoostingRegressor(random_state=42)
        try:
            model.fit(X_scaled, y)
            print(f"✅ Successfully trained {position} model on {X.shape[0]} samples.")
            return {"main": model}, scaler
        except Exception as e:
            print(f"❌ Training failed for {position}: {e}")
            return {}, None

    def predict_ensemble(self, X, models, scaler, position):
        """
        Predicts using trained models, ensuring consistent feature usage.
        """
        # Ensure X only has the features seen during training
        missing_cols = [col for col in self.feature_names if col not in X.columns]
        if missing_cols:
            print(f"⚠️ Missing columns in prediction data: {missing_cols} — filling with 0")
            for col in missing_cols:
                X[col] = 0

        # Filter to training feature set, drop extras
        X = X[self.feature_names]

        # Fill missing values with 0
        X = X.fillna(0)

        # Scale and predict
        X_scaled = scaler.transform(X)
        preds = models.predict(X_scaled)

        return preds


    def generate_predictions(self, players, floor_mult=FLOOR_MULTIPLIER, ceiling_mult=CEILING_MULTIPLIER):
        """Generate predictions for each position, merge salary data, and cache results."""
        predictions = []

        # Load salary once
        salary_df = load_salary_csv(salaryPath + "DKSalaries.csv")

        for position in ["QB", "RB", "WR", "TE"]:
            print(f"Training models for {position}...")

            pos_df = players[players["position"] == position].copy()
            if pos_df.empty:
                print(f"⚠️ No data for {position}, skipping.")
                continue

            target = "fantasy_points"
            if target not in pos_df.columns:
                print(f"⚠️ Missing target '{target}' for {position}, skipping.")
                continue

            # Features & target
            features = [
                col for col in pos_df.columns
                if col not in ["player_id", "name", "team", "position", target]
            ]
            X = pos_df[features]
            y = pos_df[target]

            # Train models
            models, scaler = self.train_models(X, y, position)

            if not models or scaler is None:
                print(f"⚠️ No model trained for {position}, assigning zeros.")
                pos_df["prediction"] = 0.0
            else:
                try:
                    X_scaled = scaler.transform(X.fillna(0))
                    pos_df["prediction"] = models["main"].predict(X_scaled)
                    print(f"✅ Generated predictions for {position}, shape={pos_df.shape}")
                except Exception as e:
                    print(f"❌ Prediction failed for {position}: {e}")
                    pos_df["prediction"] = 0.0

            # --- Merge salary for this position ---
            if salary_df.empty:
                pos_df["salary"] = np.nan
            else:
                pos_df["name"] = (
                    pos_df["name"].astype(str).str.strip().str.title()
                    .str.replace(r"\s(Jr\.|III|II)$", "", regex=True)
                )
                pos_df["team"] = pos_df["team"].astype(str).str.upper()
                pos_df["position"] = pos_df["position"].astype(str).str.upper()

                exact = (
                    salary_df[["name", "team", "position", "salary"]]
                    .rename(columns={"salary": "salary_exact"})
                )
                merged = pos_df.merge(exact, on=["name", "team", "position"], how="left")

                fb = (
                    salary_df[["name", "position", "salary"]]
                    .drop_duplicates(["name", "position"])
                    .rename(columns={"salary": "salary_fallback"})
                )
                merged = merged.merge(fb, on=["name", "position"], how="left")

                merged["salary"] = merged["salary_exact"].combine_first(merged["salary_fallback"])
                merged.drop(columns=["salary_exact", "salary_fallback"], inplace=True)
                merged["salary"] = pd.to_numeric(merged["salary"], errors="coerce")
                pos_df = merged

            # Deduplicate & add to predictions list
            pos_df = pos_df.drop_duplicates(subset=["name", "team", "position"], keep="first")
            predictions.append(pos_df[[
                "player_id", "name", "team", "position", "salary",
                "prediction", "fantasy_points"
            ]])

        # Combine all positions
        if not predictions:
            raise RuntimeError("No predictions generated – all positions failed.")

        df = pd.concat(predictions, ignore_index=True)
        
        # Ownership/value/leverage placeholders
        df["ownership"] = 0.0
        df["value"] = df["prediction"] / df["salary"].replace({0: None})
        df["leverage"] = df["prediction"] - df["ownership"]

        # --- Floor & Ceiling using historical variance (normalized by position) ---
        if "fantasy_points" in players.columns:
            # Player-level std dev by position
            player_std = (
                players.groupby(["position", "name"])["fantasy_points"]
                .std()
                .reset_index()
                .rename(columns={"fantasy_points": "player_std"})
            )

            # Position-level fallback (if player has too little history)
            pos_std = (
                players.groupby("position")["fantasy_points"]
                .std()
                .reset_index()
                .rename(columns={"fantasy_points": "pos_std"})
            )

            # Merge stds into df
            df = df.merge(player_std, on=["position", "name"], how="left")
            df = df.merge(pos_std, on="position", how="left")

            # Fill missing player_std with position average
            df["player_std"] = df["player_std"].fillna(df["pos_std"])

            # Drop helper column
            df.drop(columns=["pos_std"], inplace=True)
        else:
            df["player_std"] = 2.0  # fallback constant

        # Configurable floor & ceiling
        #df["floor"] = (df["prediction"] - FLOOR_MULTIPLIER * df["player_std"]).clip(lower=0)
        #df["ceiling"] = df["prediction"] + CEILING_MULTIPLIER * df["player_std"]

        # Configurable floor & ceiling
        df["floor"] = (df["prediction"] - floor_mult * df["player_std"]).clip(lower=0)
        df["ceiling"] = df["prediction"] + ceiling_mult * df["player_std"]


        # # --- Floor & Ceiling using historical variance (normalized by position) ---
        # if "fantasy_points" in players.columns:
        #     # Player-level std dev by position
        #     player_std = (
        #         players.groupby(["position", "name"])["fantasy_points"]
        #         .std()
        #         .reset_index()
        #         .rename(columns={"fantasy_points": "player_std"})
        #     )

        #     # Position-level fallback (if a player has only 1 week of data, std = NaN)
        #     pos_std = (
        #         players.groupby("position")["fantasy_points"]
        #         .std()
        #         .reset_index()
        #         .rename(columns={"fantasy_points": "pos_std"})
        #     )

        #     # Merge player std + position std into df
        #     df = df.merge(player_std, on=["position", "name"], how="left")
        #     df = df.merge(pos_std, on="position", how="left")

        #     # Fill missing player_std with position average
        #     df["player_std"] = df["player_std"].fillna(df["pos_std"])

        #     # Drop helper column
        #     df.drop(columns=["pos_std"], inplace=True)
        # else:
        #     # Fallback constant if no history exists
        #     df["player_std"] = 2.0

        # # Floor and ceiling projections
        # df["floor"] = (df["prediction"] - df["player_std"]).clip(lower=0)
        # df["ceiling"] = df["prediction"] + df["player_std"]

        # Final deduplication
        df = df.drop_duplicates(subset=["name", "team", "position"], keep="first")

        self.cached_predictions = df
        print(f"✅ Final predictions cached, shape={df.shape}")
        return df

    def run_full_pipeline(self):
        feats = self.create_features()
        preds = self.generate_predictions(feats)
        return preds
