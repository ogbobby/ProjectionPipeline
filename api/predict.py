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
    
    # def create_features(self):

    #     print(f"Creating features for season {self.season}...")

    #     # -----------------------
    #     # 1. Load Player Data
    #     # -----------------------
    #     try:
    #         qbs = GetQBData()
    #         rbs = GetRBData()
    #         wrs = GetWRData()
    #         tes = GetTEData()
    #     except Exception as e:
    #         raise RuntimeError(f"CRITICAL ERROR: Failed to load player data → {e}")

    #     players = pd.concat([qbs, rbs, wrs, tes], ignore_index=True, sort=False)
    #     print(f"✅ Loaded player data, shape={players.shape}")

    #     # -----------------------
    #     # 2. Merge Additional Data
    #     # -----------------------
    #     def safe_merge(df, data_func, on, name):
    #         try:
    #             data = data_func()
    #             if data is None or data.empty:
    #                 print(f"⚠️ {name} returned no usable data")
    #                 return df
    #             merged = df.merge(data, on=on, how="left")
    #             print(f"✅ Merged {name} on '{on}' → players.shape={merged.shape}")
    #             return merged
    #         except Exception as e:
    #             print(f"⚠️ Error in {name}: {e}")
    #             return df

    #     # Merge player-level
    #     players = safe_merge(players, redZonePassing(self.season), "name", "redZonePassing")
    #     players = safe_merge(players, redZoneRushing(self.season), "name", "redZoneRushing")
    #     players = safe_merge(players, redZoneReceiving(self.season), "name", "redZoneReceiving")
    #     players = safe_merge(players, boomBust(self.season), "name", "boomBust")

    #     # Merge team-level
    #     players = safe_merge(players, TurnDiff(self.season), "team", "TurnDiff")
    #     players = safe_merge(players, PenDiff(self.season), "team", "PenDiff")
    #     players = safe_merge(players, TeamScoring(self.season), "team", "TeamScoring")
    #     players = safe_merge(players, targetDistro(self.season), "team", "targetDistro")
    #     players = safe_merge(players, teamDEFData(self.season), "team", "teamDEFData")
    #     players = safe_merge(players, advancedDEFData(self.season), "team", "advancedDEFData")

    #     # -----------------------
    #     # 3. Clean Data Types
    #     # -----------------------
    #     id_columns = ["player_id", "name", "team", "season", "week"]
    #     for col in players.columns:
    #         if col in id_columns:
    #             continue

    #         # Flatten nested objects
    #         players[col] = players[col].apply(lambda x: str(x) if isinstance(x, (list, dict, pd.DataFrame)) else x)

    #         # Remove non-numeric chars (keep digits, minus, decimal)
    #         players[col] = players[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True)

    #         # Convert to numeric & fill NaN
    #         players[col] = pd.to_numeric(players[col], errors="coerce").fillna(0)

    #     # -----------------------
    #     # 4. Final Cleanup
    #     # -----------------------
    #     players = players.fillna(0)
    #     players.reset_index(drop=True, inplace=True)

    #     print(f"✨ Final features shape: {players.shape}")
    #     return players

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
    # def train_models(self, X, y, position):
    #     """
    #     Trains Gradient Boosting and Random Forest models on numeric-only features.
    #     Automatically filters invalid columns and removes NaNs.
    #     """
    #     print(f"Training models for {position}...")
    
    #     # Ensure DataFrame format
    #     X = pd.DataFrame(X)
    
    #     # Keep numeric-only columns
    #     numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    #     X = X[numeric_cols]
    
    #     # Drop rows with any NaNs just in case
    #     nan_rows = X.isna().sum(axis=1) > 0
    #     if nan_rows.any():
    #         print(f"⚠️ Dropping {nan_rows.sum()} rows with NaNs before training.")
    #         X = X[~nan_rows]
    #         y = y[~nan_rows]
    
    #     # Final log of features used
    #     print(f"✅ Training on {len(numeric_cols)} numeric features:")
    #     print(f"   Features: {numeric_cols}")
    
    #     # Scale features
    #     scaler = StandardScaler()
    #     X_scaled = scaler.fit_transform(X)
    
    #     # Train models
    #     gbr = GradientBoostingRegressor(random_state=42)
    #     rf = RandomForestRegressor(n_estimators=200, random_state=42)
    
    #     gbr.fit(X_scaled, y)
    #     rf.fit(X_scaled, y)
    
    #     print(f"✅ Finished training {position} models.")
    #     return {"gbr": gbr, "rf": rf}, scaler

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

    # def predict_ensemble(self, X, models, scaler, position):
    #     if X.empty:
    #         return pd.Series([], index=X.index)
    #     X_scaled = scaler.transform(X)
    #     preds = []
    #     for model in models:
    #         try:
    #             preds.append(model.predict(X_scaled))
    #         except Exception:
    #             preds.append(np.zeros(X.shape[0]))
    #     preds = np.mean(preds, axis=0)
    #     return pd.Series(preds, index=X.index)

    def generate_predictions(self, players):
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
    
        # Final deduplication
        df = df.drop_duplicates(subset=["name", "team", "position"], keep="first")
    
        self.cached_predictions = df
        print(f"✅ Final predictions cached, shape={df.shape}")
        return df

    # def generate_predictions(self, players):
    #     """Generate predictions for each position, merge salary data, and cache results."""
    #     predictions = []

    #     # Load salary data once
    #     salary_df = load_salary_csv(salaryPath+"DKSalaries.csv")

    #     for position in ["QB", "RB", "WR", "TE"]:
    #         print(f"Training models for {position}...")

    #         # Filter players by position
    #         pos_df = players[players["position"] == position].copy()
    #         if pos_df.empty:
    #             print(f"⚠️ No data for {position}, skipping.")
    #             continue

    #         # Ensure target exists
    #         target = "fantasy_points"
    #         if target not in pos_df.columns:
    #             print(f"⚠️ Missing target '{target}' for {position}, skipping.")
    #             continue

    #         # Features & target
    #         features = [
    #             col for col in pos_df.columns
    #             if col not in ["player_id", "name", "team", "position", target]
    #         ]
    #         X = pos_df[features]
    #         y = pos_df[target]

    #         # Train models
    #         models, scaler = self.train_models(X, y, position)

    #         if not models or scaler is None:
    #             print(f"⚠️ No model trained for {position}, assigning zeros.")
    #             pos_df["prediction"] = 0.0
    #         else:
    #             try:
    #                 X_scaled = scaler.transform(X.fillna(0))
    #                 pos_df["prediction"] = models["main"].predict(X_scaled)
    #                 print(f"✅ Generated predictions for {position}, shape={pos_df.shape}")
    #             except Exception as e:
    #                 print(f"❌ Prediction failed for {position}: {e}")
    #                 pos_df["prediction"] = 0.0

    #             # --- Salary merge (exact first, then fallback by name+position) ---
    #     salary_df = load_salary_csv(salaryPath+"DKSalaries.csv" if 'salaryPath' in globals() else "DKSalaries.csv")
    #     if salary_df.empty:
    #         print("⚠️ No salary data found, leaving salary blank.")
    #         pos_df["salary"] = np.nan
    #     else:
    #         # Normalize for join (keep it light; your loader already normalizes)
    #         pos_df["name"] = (
    #             pos_df["name"].astype(str).str.strip().str.title()
    #             .str.replace(r"\s(Jr\.|III|II)$", "", regex=True)
    #         )
    #         pos_df["team"] = pos_df["team"].astype(str).str.upper()
    #         pos_df["position"] = pos_df["position"].astype(str).str.upper()

    #         # 1) Exact match on name+team+position -> salary_exact
    #         exact = (
    #             salary_df[["name", "team", "position", "salary"]]
    #             .rename(columns={"salary": "salary_exact"})
    #         )
    #         merged = pos_df.merge(exact, on=["name", "team", "position"], how="left")

    #         # 2) Fallback on name+position only -> salary_fallback
    #         fb = (
    #             salary_df[["name", "position", "salary"]]
    #             .drop_duplicates(["name", "position"])
    #             .rename(columns={"salary": "salary_fallback"})
    #         )
    #         merged = merged.merge(fb, on=["name", "position"], how="left")

    #         # 3) Prefer exact, else fallback
    #         merged["salary"] = merged["salary_exact"].combine_first(merged["salary_fallback"])

    #         # Housekeeping
    #         merged.drop(columns=["salary_exact", "salary_fallback"], inplace=True)

    #         # Make sure it's numeric
    #         merged["salary"] = pd.to_numeric(merged["salary"], errors="coerce")

    #         matched = merged["salary"].notna().sum()
    #         print(f"✅ Salary matched for {matched}/{len(merged)} {position} players.")

    #         # Optional: show a few that still missed
    #         miss = merged[merged["salary"].isna()]
    #         if not miss.empty:
    #             #print(f"⚠️ Still missing salary for {len(miss)} {position} players (top 5):")
    #             #print(miss[["name", "team", "position"]].head(5).to_string(index=False))
    #             print(f"⚠️ Still missing salary for {len(miss)} {position} players (e.g., {', '.join(miss['name'].head(5))})")


    #         pos_df = merged
    #     # --- end salary merge ---
        
    #     # Collect predictions for this position
    #     predictions.append(pos_df[[
    #         "player_id", "name", "team", "position",
    #         "salary", "prediction", "fantasy_points"
    #     ]])
        
    #     # Combine all positions
    #     if not predictions:
    #         raise RuntimeError("No predictions generated – all positions failed.")

    #     df = pd.concat(predictions, ignore_index=True)

    #     # Placeholder ownership/value/leverage until we add real logic
    #     df["ownership"] = 0.0
    #     df["value"] = df["prediction"] / df["salary"].replace({0: None})
    #     df["leverage"] = df["prediction"] - df["ownership"]

    #     # Cache predictions for API
    #     df = df.drop_duplicates(subset=["name", "team", "position"], keep="first")
    #     self.cached_predictions = df
    #     print(f"✅ Final predictions cached, shape={df.shape}")
    #     return df

    # def generate_predictions(self, players):
    #     """Generate predictions safely, returning 0s if models cannot be trained."""
    #     predictions = []

    #     for position in ["QB", "RB", "WR", "TE"]:
    #         print(f"Training models for {position}...")

    #         # Select features for this position
    #         pos_df = players[players["position"] == position].copy()
    #         if pos_df.empty:
    #             print(f"⚠️ No data for {position}, skipping.")
    #             continue

    #         features = [col for col in pos_df.columns if col not in ["player_id", "name", "team", "position", "fantasy_points"]]
    #         target = "fantasy_points"

    #         if target not in pos_df.columns:
    #             print(f"⚠️ Missing target '{target}' for {position}, skipping.")
    #             continue

    #         X = pos_df[features]
    #         y = pos_df[target]

    #         models, scaler = self.train_models(X, y, position)

    #         if not models or scaler is None:
    #             print(f"⚠️ No model trained for {position}, assigning zeros.")
    #             pos_df["prediction"] = 0.0
    #         else:
    #             try:
    #                 X_scaled = scaler.transform(X.fillna(0))
    #                 pos_df["prediction"] = models["main"].predict(X_scaled)
    #                 print(f"✅ Generated predictions for {position}, shape={pos_df.shape}")
    #             except Exception as e:
    #                 print(f"❌ Prediction failed for {position}: {e}")
    #                 pos_df["prediction"] = 0.0

    #         predictions.append(pos_df[["player_id", "name", "team", "position", "prediction"]])

    #     # If no predictions at all
    #     if not predictions:
    #         raise RuntimeError("No predictions generated – all positions failed.")

    #     # Combine all position predictions
    #     df = pd.concat(predictions, ignore_index=True)

    #     # Load and merge salary
    #     salary_df = load_salary_csv("DKSalaries.csv")
    #     if not salary_df.empty:
    #         df = df.merge(
    #             salary_df[["name", "team", "position", "salary"]],
    #             on=["name", "team", "position"],
    #             how="left"
    #         )
    #         print(f"✅ Merged salary data → {df['salary'].notna().sum()} matched players.")
    #     else:
    #         print("⚠️ No salary data found, leaving salary blank.")
    #         df["salary"] = None

    #     # Ensure ownership column exists (frontend expects it)
    #         if "ownership" not in df.columns:
    #             df["ownership"] = None

    #         self.cached_predictions = df
    #         return df

    #     self.cached_predictions = df
    #     return df

    def run_full_pipeline(self):
        feats = self.create_features()
        preds = self.generate_predictions(feats)
        return preds
