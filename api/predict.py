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

# Scrapers
try:
    from nflpyStats import GetQBData, GetRBData, GetWRData, GetTEData, GetDepthCharts
    from playerStatScraper import redZonePassing, redZoneRushing, redZoneReceiving, PosPtsperWeek, boomBust
    from teamScrapers import TurnDiff, PenDiff, TeamScoring, targetDistro, Schedule2025, teamDEFData, advancedDEFData, PlaySelection, scrapDVOA, passingDEFData, rushingDEFData, offPlays
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

    def create_features(self) -> pd.DataFrame:
        """
        Build the full player-level feature matrix by merging player and team scrapers.
        Adds one-hot encodings for position/team/opponent and keeps raw string cols only
        for display (not used for modeling).
        """
        print(f"Creating features for season {self.season}...")

        # 1) Load base player data
        player_dfs = []
        for loader, label in [
            (GetQBData, "QB"),
            (GetRBData, "RB"),
            (GetWRData, "WR"),
            (GetTEData, "TE"),
        ]:
            try:
                df = loader()
                if df is not None and not df.empty:
                    df["position"] = label
                    player_dfs.append(df)
                    print(f"✅ Loaded {label} data, shape={df.shape}")
                else:
                    print(f"⚠️ {label} loader returned empty")
            except Exception as e:
                print(f"⚠️ Error loading {label} data: {e}")

        if not player_dfs:
            raise RuntimeError("No player data available from scrapers!")

        players = pd.concat(player_dfs, ignore_index=True)

        # Normalize identifiers
        for c in ("name",):
            if c in players.columns:
                players[c] = players[c].astype(str).str.strip()
        if "team" in players.columns:
            players["team"] = players["team"].astype(str).str.upper()
        if "opponent" in players.columns:
            players["opponent"] = players["opponent"].astype(str).str.upper()

        # 2) Merge player-level scrapers on name
        player_scrapers = [
            (redZonePassing, "redZonePassing"),
            (redZoneRushing, "redZoneRushing"),
            (redZoneReceiving, "redZoneReceiving"),
            (boomBust, "boomBust"),
        ]
        for func, label in player_scrapers:
            try:
                df = func(self.season)
                if df is not None and not df.empty:
                    if "name" not in df.columns:
                        print(f"⚠️ {label} has no 'name' column, skipping")
                        continue
                    df["name"] = df["name"].astype(str).str.strip()
                    players = players.merge(df, on="name", how="left")
                    print(f"✅ Merged {label} on 'name' → players.shape={players.shape}")
                else:
                    print(f"⚠️ {label} returned no usable data")
            except Exception as e:
                print(f"⚠️ Error in {label}: {e}")

        # 3) Merge team-level scrapers on team
        team_scrapers = [
            (TurnDiff, "TurnDiff"),
            (PenDiff, "PenDiff"),
            (TeamScoring, "TeamScoring"),
            (targetDistro, "targetDistro"),
            (teamDEFData, "teamDEFData"),
            (advancedDEFData, "advancedDEFData"),
            (PlaySelection, "PlaySelection"),
            (lambda y: scrapDVOA(y, "overall"), "scrapDVOA_overall"),
            (passingDEFData, "passingDEFData"),
            (rushingDEFData, "rushingDEFData"),
            (offPlays, "offPlays"),
        ]
        for func, label in team_scrapers:
            try:
                df = func(self.season)
                if df is not None and not df.empty:
                    if "team" not in df.columns:
                        print(f"⚠️ {label} has no 'team' column, skipping")
                        continue
                    df["team"] = df["team"].astype(str).str.upper()
                    players = players.merge(df, on="team", how="left")
                    print(f"✅ Merged {label} on 'team' → players.shape={players.shape}")
                else:
                    print(f"⚠️ {label} returned no usable data")
            except Exception as e:
                print(f"⚠️ Error in {label}: {e}")

        # 4) One-hot encode categorical columns (keep originals for display)
        #    (position always exists from above; team/opponent may or may not)
        for col, pref in [("position", "pos"), ("team", "team"), ("opponent", "opp")]:
            if col in players.columns:
                dummies = pd.get_dummies(players[col].astype("category"), prefix=pref)
                players = pd.concat([players, dummies], axis=1)

        # 5) Final tidy: ensure strings for ids, numeric elsewhere (leave raw id cols for UI)
        id_cols = [c for c in ["name", "position", "team", "opponent"] if c in players.columns]
        # Replace inf and NaN only in non-id columns
        not_id = [c for c in players.columns if c not in id_cols]
        players[not_id] = players[not_id].replace([np.inf, -np.inf], np.nan)
        players[not_id] = players[not_id].fillna(0)

        print(f"✨ Final features shape: {players.shape}")
        return players
    
    def prepare_training_data(self, df: pd.DataFrame):
        """
        Create X, y from a (position-filtered) features DF.
        - Drops non-numeric columns except for the one-hot dummies we created.
        - Keeps 'fantasy_points' (or 'points' fallback) as target if present.
        """
        # Pick a target column that exists
        target_col = None
        for cand in ["fantasy_points", "points", "dk_points", "proj_points"]:
            if cand in df.columns:
                target_col = cand
                break

        if target_col is None:
            # If you don’t have historical labels for y, return NaNs but keep X;
            # your training routine should skip training if y is missing.
            y = pd.Series(index=df.index, dtype=float)
        else:
            y = pd.to_numeric(df[target_col], errors="coerce").fillna(0.0)

        # Columns to never feed into the model (ids, raw strings)
        never_cols = {"name", "player_id", "game_id", "season", "week",
                      "position", "team", "opponent"}
        X = df.drop(columns=[c for c in df.columns if c in never_cols], errors="ignore")

        # Keep only numeric columns
        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X = X[numeric_cols].copy()

        # Safety: coerce, remove infs, fill NaNs
        X = X.apply(pd.to_numeric, errors="coerce")
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        return X, y, numeric_cols

    def train_models(self, X: pd.DataFrame, y: pd.Series, position: str):
        """
        Train per-position models with only numeric features.
        Ensures scaler only sees numeric values.
        """
        # Only numeric columns (defensive in case caller passes something unexpected)
        X = X.select_dtypes(include=[np.number])
        if X.empty:
            raise ValueError(f"No numeric features available for position {position}")
    
        # If target is missing or all zeros, skip training gracefully
        if (y is None) or (len(y) != len(X)) or pd.isna(y).all():
            raise ValueError(f"No usable target for position {position}")
    
        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import Ridge
    
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    
        models = {
            "rf": RandomForestRegressor(
                n_estimators=300, max_depth=None, random_state=42, n_jobs=-1
            ),
            "gb": GradientBoostingRegressor(random_state=42),
            "ridge": Ridge(alpha=1.0, random_state=42),
        }
    
        for name, model in models.items():
            model.fit(X_scaled, y)
    
        # Keep track of features used for this position
        self.feature_columns[position] = list(X.columns)
        self.scalers[position] = scaler
        self.models[position] = models
        return models, scaler

    def predict_ensemble(self, X, models, scaler, position):
        if X.empty:
            return pd.Series([], index=X.index)
        X_scaled = scaler.transform(X)
        preds = []
        for model in models:
            try:
                preds.append(model.predict(X_scaled))
            except Exception:
                preds.append(np.zeros(X.shape[0]))
        preds = np.mean(preds, axis=0)
        return pd.Series(preds, index=X.index)

    def generate_predictions(self, features):
        results = []
        for position in self.positions:
            pos_data = features[features["position"] == position]
            if pos_data.empty:
                continue
            X = pos_data.drop(columns=["name", "recent_team", "position"], errors="ignore")
            y = np.random.rand(len(pos_data)) * 20
            models, scaler = self.train_models(X, y, position)
            preds = self.predict_ensemble(X, models, scaler, position)
            for i, (idx, row) in enumerate(pos_data.iterrows()):
                results.append({
                    "player_id": f"{position}_{i}",
                    "name": row.get("name", f"Player {i}"),
                    "position": position,
                    "team": row.get("recent_team", "UNK"),
                    "salary": int(row.get("salary", 5000)),
                    "projection": round(float(preds.loc[idx]), 2),
                    "ownership": round(float(np.random.uniform(5, 20)), 1),
                    "leverage": round(float(np.random.uniform(-10, 10)), 1),
                    "value": round(float(preds.loc[idx]) / (row.get("salary", 5000) / 1000), 2),
                })
        return pd.DataFrame(results)

    def run_full_pipeline(self):
        feats = self.create_features()
        preds = self.generate_predictions(feats)
        return preds
