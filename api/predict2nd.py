# predict.py
# Complete rewrite to integrate all scrapers, feature engineering, training, and prediction
# Designed to be robust to missing columns and still produce a clean predictions DataFrame.

from __future__ import annotations
import sys
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

# ML
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error

# Add the scripts directory to path to import our scrapers
current_dir = os.path.dirname(__file__)
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.append(scripts_dir)
#we need to add all the functions that we werent using before PlaySelection, scrapDVOA, passingDEFData, rushingDEFData, offPlays
try:
    from nflpyStats import GetQBData, GetRBData, GetWRData, GetTEData, GetDepthCharts
    from playerStatScraper import redZonePassing, redZoneRushing, redZoneReceiving, PosPtsperWeek, boomBust
    from teamScrapers import TurnDiff, PenDiff, TeamScoring, targetDistro, Schedule2025, teamDEFData, advancedDEFData, PlaySelection, scrapDVOA, passingDEFData, rushingDEFData #offPlays
    print("Successfully imported all scrapers")
except ImportError as e:
    print(f"Error importing scrapers: {e}")
    print(f"Scripts directory: {scripts_dir}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

def load_df(obj, label):
    """Handle both functions and DataFrames"""
    try:
        if callable(obj):  # it's a function, call it
            df = obj()
        else:              # it's already a DataFrame
            df = obj

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            print(f"⚠️ {label} returned empty or invalid")
            return pd.DataFrame()

        return df.copy()

    except Exception as e:
        print(f"⚠️ Error in {label}: {e}")
        return pd.DataFrame()


# ---------------------------
# Imports from your scrapers
# ---------------------------
try:
    # Player-level
    from nflpyStats import GetQBData, GetRBData, GetWRData, GetTEData, GetDepthCharts
    from playerStatScraper import (
        redZonePassing,
        redZoneRushing,
        redZoneReceiving,
        PosPtsperWeek,
        boomBust,
    )

    # Team-level
    from teamScrapers import (
        TurnDiff,
        PenDiff,
        TeamScoring,
        targetDistro,
        Schedule2025,
        teamDEFData,
        advancedDEFData,
        PlaySelection,
        scrapDVOA,
        passingDEFData,
        rushingDEFData,
        #offPlays,
    )
    print("Successfully imported all scrapers")
except Exception as e:
    print(f"Error importing scrapers: {e}")


# ===========================
# Utility helpers
# ===========================

NON_FEATURE_COLS = {
    "name",
    "player_id",
    "player_display_name",
    "position",
    "team",
    "recent_team",
    "opponent",
    "opp",
    "week",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "name_key",
    "team_key",
    "opponent_key",
    "depth_chart_order",
    "starter",
    "status",
    "salary",  # kept for output, not as feature
}

PREFERRED_TARGET_COLS = [
    # Preferred target variable (historical fantasy points or per-week/pg)
    "fantasyPts_perGame",
    "posptsperweek",
    "fantasy_points_per_game",
    "fantasy_points_pg",
    "fantasy_points",
    "fpts_pg",
    "fpts",
]


def _lower_strip(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower()


def _upper_strip(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.upper()


def safe_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to convert all non-key columns to numeric, coercing errors."""
    out = df.copy()
    for c in out.columns:
        if c in {"name", "team", "position", "opponent", "player_display_name"}:
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out.replace([np.inf, -np.inf], np.nan, inplace=True)
    return out


def choose_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def ensure_columns(df: pd.DataFrame, needed: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in needed:
        if c not in out.columns:
            out[c] = np.nan
    return out


def null0(s: pd.Series) -> pd.Series:
    return s.fillna(0)


def series_pct(n: pd.Series, d: pd.Series) -> pd.Series:
    d = d.replace(0, np.nan)
    return (n / d).fillna(0)


# ===========================
# Main predictor class
# ===========================

class NFLDFSPredictor:
    def __init__(self):
        # Positions to model
        self.positions: List[str] = ["QB", "RB", "WR", "TE"]

        # Storage
        self.models: Dict[str, Dict[str, object]] = {}     # per position: {"rf": ..., "gb": ...}
        self.scalers: Dict[str, StandardScaler] = {}       # per position scaler
        self.feature_columns: Dict[str, List[str]] = {}    # per position feature list

        # Basic knobs
        self.random_state = 42
        self.min_samples_to_train = 150  # per position

    # ---------------------------
    # SCRAPE + MERGE
    # ---------------------------
    def create_features(self) -> pd.DataFrame:
        """Create raw feature set by combining all player and team scrapers."""
        # ---- Player-level
        def load_df(fn, label) -> pd.DataFrame:
            try:
                df = fn()
                if df is None:
                    print(f"⚠️ {label} returned None")
                    return pd.DataFrame()
                if not isinstance(df, pd.DataFrame) or df.empty:
                    print(f"⚠️ {label} returned empty/no DataFrame")
                    return pd.DataFrame()
                return df.copy()
            except Exception as e:
                print(f"⚠️ Error in {label}: {e}")
                return pd.DataFrame()

        qb = load_df(GetQBData, "GetQBData")
        rb = load_df(GetRBData, "GetRBData")
        wr = load_df(GetWRData, "GetWRData")
        te = load_df(GetTEData, "GetTEData")

        for df, pos in [(qb, "QB"), (rb, "RB"), (wr, "WR"), (te, "TE")]:
            if not df.empty and "position" not in df.columns:
                df["position"] = pos

        # Normalize name/team columns if present
        def norm_player_df(df: pd.DataFrame) -> pd.DataFrame:
            if df.empty:
                return df
            df = df.copy()
            # Name column
            name_col = choose_existing_col(
                df, ["name", "player_display_name", "player", "Player"]
            )
            if name_col is None:
                # fabricate a name if absolutely necessary
                df["name"] = df.index.astype(str)
            else:
                df.rename(columns={name_col: "name"}, inplace=True)

            # Team column
            team_col = choose_existing_col(
                df, ["team", "recent_team", "Tm", "Team", "team_name", "player_team"]
            )
            if team_col is None:
                df["team"] = "UNK"
            else:
                df.rename(columns={team_col: "team"}, inplace=True)

            # Position
            pos_col = choose_existing_col(df, ["position", "Pos", "pos"])
            if pos_col is None:
                df["position"] = "UNK"
            else:
                df.rename(columns={pos_col: "position"}, inplace=True)

            # Salary (optional)
            sal_col = choose_existing_col(df, ["salary", "Salary"])
            if sal_col and sal_col != "salary":
                df.rename(columns={sal_col: "salary"}, inplace=True)

            # Normalize keys
            df["name_key"] = _lower_strip(df["name"])
            df["team"] = _upper_strip(df["team"])
            return df

        qb, rb, wr, te = (norm_player_df(qb), norm_player_df(rb),
                          norm_player_df(wr), norm_player_df(te))

        # Combine all players
        players = pd.concat([df for df in [qb, rb, wr, te] if not df.empty],
                            ignore_index=True)
        if players.empty:
            print("❌ No base player data found from positional scrapers.")
            return pd.DataFrame()

        # Drop exact duplicates by name + team + position
        players = players.drop_duplicates(subset=["name_key", "team", "position"])

        # Add depth charts optionally (not required in merges)
        depth = load_df(GetDepthCharts, "GetDepthCharts")
        if not depth.empty:
            depth = depth.copy()
            # Normalize columns
            name_col = choose_existing_col(depth, ["name", "player_display_name", "player"])
            if name_col and name_col != "name":
                depth.rename(columns={name_col: "name"}, inplace=True)
            team_col = choose_existing_col(depth, ["team", "recent_team", "Tm", "Team"])
            if team_col and team_col != "team":
                depth.rename(columns={team_col: "team"}, inplace=True)
            depth["name_key"] = _lower_strip(depth["name"])
            depth["team"] = _upper_strip(depth["team"])
            players = players.merge(
                depth.drop_duplicates(subset=["name_key", "team"]),
                on=["name_key", "team"],
                how="left",
                suffixes=("", "_depth"),
            )

        # Player-level extras (merge on name_key)
        def merge_player_extra(players_df: pd.DataFrame, extra_fn, label: str) -> pd.DataFrame:
            extra = load_df(extra_fn, label)
            if extra.empty:
                return players_df
            extra = extra.copy()
            name_col = choose_existing_col(extra, ["name", "player_display_name", "player"])
            if name_col and name_col != "name":
                extra.rename(columns={name_col: "name"}, inplace=True)
            extra["name_key"] = _lower_strip(extra["name"])
            # De-dup on name_key
            extra = extra.groupby("name_key", as_index=False).first()
            return players_df.merge(extra, on="name_key", how="left", suffixes=("", f"_{label.lower()}"))

        players = merge_player_extra(players, redZonePassing('2024'), "redZonePassing")
        players = merge_player_extra(players, redZoneRushing('2024'), "redZoneRushing")
        players = merge_player_extra(players, redZoneReceiving('2024'), "redZoneReceiving")
        #players = merge_player_extra(players, PosPtsperWeek('2024'), "PosPtsperWeek")
        players = merge_player_extra(players, boomBust('2024'), "boomBust")

        # Team-level merges (merge on team)
        def merge_team_extra(players_df: pd.DataFrame, extra_fn, label: str) -> pd.DataFrame:
            extra = load_df(extra_fn, label)
            if extra.empty:
                return players_df
            extra = extra.copy()
            tcol = choose_existing_col(extra, ["team", "Tm", "Team", "team_name"])
            if tcol and tcol != "team":
                extra.rename(columns={tcol: "team"}, inplace=True)
            extra["team"] = _upper_strip(extra["team"])
            extra = extra.groupby("team", as_index=False).first()
            return players_df.merge(extra, on="team", how="left", suffixes=("", f"_{label.lower()}"))

        team_mergers = [
            (TurnDiff('2024'), "TurnDiff"),
            (PenDiff('2024'), "PenDiff"),
            (TeamScoring('2024'), "TeamScoring"),
            (targetDistro('2024'), "targetDistro"),
            (teamDEFData('2024'), "teamDEFData"),
            (advancedDEFData('2024'), "advancedDEFData"),
            (PlaySelection, "PlaySelection"),
            (scrapDVOA('2024','WR'), "scrapDVOA"),
            (passingDEFData('2024'), "passingDEFData"),
            (rushingDEFData('2024'), "rushingDEFData"),
            #(offPlays, "offPlays"),
        ]
        for fn, label in team_mergers:
            players = merge_team_extra(players, fn, label)

        # Schedule → brings opponent
        sched = load_df(Schedule2025, "Schedule2025")
        if not sched.empty:
            sched = sched.copy()
            tcol = choose_existing_col(sched, ["team", "Tm", "Team"])
            if tcol and tcol != "team":
                sched.rename(columns={tcol: "team"}, inplace=True)
            ocol = choose_existing_col(sched, ["opponent", "Opp", "opp", "OPP"])
            if ocol and ocol != "opponent":
                sched.rename(columns={ocol: "opponent"}, inplace=True)

            sched["team"] = _upper_strip(sched["team"])
            sched["opponent"] = _upper_strip(sched["opponent"])
            # one row per team is enough if it's current/forthcoming context; else first row
            sched = sched.groupby("team", as_index=False).first()
            players = players.merge(sched[["team", "opponent"]], on="team", how="left")
        else:
            players["opponent"] = "UNK"

        # Salary default
        if "salary" not in players.columns:
            players["salary"] = 5000

        # Final cleaning
        players = safe_to_numeric(players)
        players.replace([np.inf, -np.inf], np.nan, inplace=True)
        players.fillna(0, inplace=True)

        # Guarantee required columns
        players = ensure_columns(players, ["name", "team", "position", "opponent", "salary"])

        # De-dup name again, prefer most complete row
        players = players.sort_values(by=players.columns.tolist()).drop_duplicates(
            subset=["name_key", "team", "position"], keep="last"
        )

        print(f"✅ create_features(): {players.shape[0]} players, {players.shape[1]} columns")
        return players.reset_index(drop=True)

    # ---------------------------
    # Feature Engineering
    # ---------------------------
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer advanced features from raw stats (red-zone rates, TD rates, per-game, etc.)."""
        out = df.copy()

        # Heuristic column guesses (since scrapers may differ)
        # Passing volume/TD
        pass_att = choose_existing_col(out, ["pass_attempts", "Att", "passAtt", "passAttempts"])
        pass_td = choose_existing_col(out, ["pass_td", "TD", "passTD", "passing_td"])

        # Rushing volume/TD
        rush_att = choose_existing_col(out, ["rush_attempts", "rushAtt", "rushAttempts", "Att_rush"])
        rush_td = choose_existing_col(out, ["rush_td", "rushTD", "rushing_td"])

        # Receiving volume/TD
        targets = choose_existing_col(out, ["targets", "Tgt", "tgt"])
        rec_td = choose_existing_col(out, ["rec_td", "receiving_td", "recTD"])

        # Red zone components
        rz_pass_att = choose_existing_col(out, ["redzonepassingattempts", "redZonePassingAttempts"])
        rz_rush_att = choose_existing_col(out, ["redzonerushattempts", "redZoneRushAttempts"])
        rz_tgt = choose_existing_col(out, ["redzonetargets", "redZoneTargets"])

        # Games
        games = choose_existing_col(out, ["games", "G", "g", "gp", "Games"])

        # Simple derived percentages/rates
        if rz_pass_att and pass_att:
            out["redZonePassPct"] = series_pct(out[rz_pass_att], out[pass_att])
        else:
            out["redZonePassPct"] = 0.0

        if rz_rush_att and rush_att:
            out["redZoneRushPct"] = series_pct(out[rz_rush_att], out[rush_att])
        else:
            out["redZoneRushPct"] = 0.0

        if rz_tgt and targets:
            out["redZoneTargetPct"] = series_pct(out[rz_tgt], out[targets])
        else:
            out["redZoneTargetPct"] = 0.0

        if pass_td and pass_att:
            out["passTD_Rate"] = series_pct(out[pass_td], out[pass_att])
        else:
            out["passTD_Rate"] = 0.0

        if rush_td and rush_att:
            out["rushTD_Rate"] = series_pct(out[rush_td], out[rush_att])
        else:
            out["rushTD_Rate"] = 0.0

        if rec_td and targets:
            out["recTD_Rate"] = series_pct(out[rec_td], out[targets])
        else:
            out["recTD_Rate"] = 0.0

        # Boom/Bust
        boom_col = choose_existing_col(out, ["boom", "Boom", "boom_count"])
        bust_col = choose_existing_col(out, ["bust", "Bust", "bust_count"])
        if boom_col and bust_col:
            out["boomRate"] = out[boom_col] / (out[boom_col] + out[bust_col] + 1.0)
        else:
            out["boomRate"] = 0.0

        # Fantasy per game target (from PosPtsperWeek or similar)
        ppg_col = choose_existing_col(out, ["fantasyPts_perGame", "PosPtsperWeek", "posptsperweek"])
        if ppg_col and games:
            # If PosPtsperWeek looks like total per season, divide by games
            out["fantasyPts_perGame"] = out[ppg_col] / out[games].replace(0, np.nan)
            out["fantasyPts_perGame"] = out["fantasyPts_perGame"].fillna(0)
        elif ppg_col:
            out["fantasyPts_perGame"] = out[ppg_col]
        else:
            # Fallback heuristic proxy from mixed rates
            out["fantasyPts_perGame"] = (
                4.0 * null0(out.get("passTD_Rate", 0))
                + 6.0 * null0(out.get("rushTD_Rate", 0))
                + 6.0 * null0(out.get("recTD_Rate", 0))
                + 1.5 * null0(out.get(targets, pd.Series(0, index=out.index)))
            )

        # Cleanup
        out = safe_to_numeric(out)
        out.replace([np.inf, -np.inf], np.nan, inplace=True)
        out.fillna(0, inplace=True)
        return out

    # ---------------------------
    # Add Team Features (context/ranks)
    # ---------------------------
    def add_team_features(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()

        # Offensive pace (from PlaySelection/offPlays merges) or proxy
        pace_col = choose_existing_col(out, ["offplayspergame", "offPlaysPerGame", "Plays"])
        if pace_col:
            out["pace_rank"] = out[pace_col].rank(pct=True)
        else:
            out["pace_rank"] = 0.5

        # Turnover margin rank
        turndiff_col = choose_existing_col(out, ["turndiff", "TurnDiff"])
        if turndiff_col:
            out["turnover_margin_rank"] = out[turndiff_col].rank(pct=True)
        else:
            out["turnover_margin_rank"] = 0.5

        # Penalty margin rank
        pendiff_col = choose_existing_col(out, ["pendiff", "PenDiff"])
        if pendiff_col:
            out["penalty_margin_rank"] = out[pendiff_col].rank(pct=True)
        else:
            out["penalty_margin_rank"] = 0.5

        out = safe_to_numeric(out)
        out.replace([np.inf, -np.inf], np.nan, inplace=True)
        out.fillna(0, inplace=True)
        return out

    # ---------------------------
    # Add Matchup Features
    # ---------------------------
    def add_matchup_features(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if "opponent" not in out.columns:
            out["opponent"] = "UNK"

        # Create simple opponent aggregates: if team DEF columns present on team's rows,
        # use groupby on opponent to synthesize opponent context.
        opp_stats_candidates = [
            ("passydsallowed", "opp_passYdsAllowed"),
            ("rushydsallowed", "opp_rushYdsAllowed"),
            ("dvoa", "opp_DVOA"),
            ("sacks", "opp_sacks"),
            ("yds", "opp_totalYdsAllowed"),
            ("pa", "opp_pointsAllowed"),
        ]
        for base, opp_name in opp_stats_candidates:
            src = choose_existing_col(out, [base, base.capitalize(), base.upper()])
            if src:
                # mean per opponent of source column
                opp_vals = out.groupby("opponent")[src].transform("mean")
                out[opp_name] = opp_vals
            else:
                out[opp_name] = 0.0

        out = safe_to_numeric(out)
        out.replace([np.inf, -np.inf], np.nan, inplace=True)
        out.fillna(0, inplace=True)
        return out

    # ---------------------------
    # Data prep for training
    # ---------------------------
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        # Target y
        y_col = None
        lower_cols = {c.lower(): c for c in df.columns}
        for want in PREFERRED_TARGET_COLS:
            if want in lower_cols:
                y_col = lower_cols[want]
                break

        if y_col is None:
            # Fallback — use engineered fantasyPts_perGame if present; else zeros
            y_col = "fantasyPts_perGame" if "fantasyPts_perGame" in df.columns else None

        if y_col is None:
            y = pd.Series(np.zeros(len(df)), index=df.index)
        else:
            y = pd.to_numeric(df[y_col], errors="coerce").fillna(0)

        # Features X: numeric columns minus NON_FEATURE_COLS and y_col
        numeric_cols = [
            c for c in df.columns
            if c not in NON_FEATURE_COLS and c != y_col and pd.api.types.is_numeric_dtype(df[c])
        ]
        X = df[numeric_cols].copy()

        # Clean
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        X.fillna(0, inplace=True)

        return X, y, numeric_cols

    # ---------------------------
    # Training per position
    # ---------------------------
    def train_models(self, X: pd.DataFrame, y: pd.Series, position: str):
        # Keep only finite values
        mask = np.isfinite(X.values).all(axis=1) & np.isfinite(y.values)
        X = X[mask]
        y = y[mask]

        if len(X) < self.min_samples_to_train:
            print(f"⚠️ Not enough samples to train {position} model (have {len(X)})")
            return {}, None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )

        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc = scaler.transform(X_test)

        rf = RandomForestRegressor(
            n_estimators=300, max_depth=None, random_state=self.random_state, n_jobs=-1
        )
        gb = GradientBoostingRegressor(random_state=self.random_state)

        rf.fit(X_train_sc, y_train)
        gb.fit(X_train_sc, y_train)

        # Quick eval print (not required by API, but useful)
        for name, mdl in [("RF", rf), ("GB", gb)]:
            pred = mdl.predict(X_test_sc)
            print(
                f"{position} {name} -> R2={r2_score(y_test, pred):.3f}, MAE={mean_absolute_error(y_test, pred):.3f}"
            )

        return {"rf": rf, "gb": gb}, scaler

    def predict_ensemble(self, X: pd.DataFrame, models: Dict[str, object], scaler: Optional[StandardScaler]) -> np.ndarray:
        if not models:
            # Fallback: zero projections
            return np.zeros(len(X), dtype=float)

        Xt = X.copy()
        Xt.replace([np.inf, -np.inf], np.nan, inplace=True)
        Xt.fillna(0, inplace=True)

        if scaler is not None:
            Xt = scaler.transform(Xt.values)
        else:
            Xt = Xt.values

        preds = []
        if "rf" in models:
            preds.append(models["rf"].predict(Xt))
        if "gb" in models:
            preds.append(models["gb"].predict(Xt))

        if not preds:
            return np.zeros(len(X), dtype=float)

        # Average
        return np.mean(preds, axis=0)

    # ---------------------------
    # Ownership + Leverage
    # ---------------------------
    def predict_ownership(self, pos_df: pd.DataFrame, proj_values: np.ndarray) -> np.ndarray:
        """Heuristic ownership: blend projection rank and inverse-salary rank."""
        n = len(pos_df)
        if n == 0:
            return np.array([])

        # Ensure 1D
        proj = pd.Series(np.asarray(proj_values).reshape(-1))
        proj = proj.reindex(range(n)).fillna(proj.mean() if n else 0)

        # Salary series
        salary = pd.to_numeric(pos_df.get("salary", pd.Series([5000] * n)), errors="coerce").fillna(5000)

        proj_rank = proj.rank(pct=True)
        sal_rank = salary.rank(pct=True)

        base = 0.6 * proj_rank + 0.4 * (1 - sal_rank)
        # Scale to a realistic ownership band by position
        pos = pos_df["position"].iloc[0] if "position" in pos_df.columns and len(pos_df) else "UNK"
        scale = {"QB": 25, "RB": 30, "WR": 28, "TE": 20}.get(pos, 20)
        own = np.clip(base.values * scale, 1.0, 45.0)
        return own

    def calculate_leverage(self, proj_values: np.ndarray | pd.Series, ownership: np.ndarray) -> np.ndarray:
        proj = pd.Series(np.asarray(proj_values).reshape(-1))
        proj_pct = proj.rank(pct=True).values
        own_pct = pd.Series(ownership).rank(pct=True).values
        lev = (proj_pct - own_pct) * 100.0
        return lev

    # ---------------------------
    # Prediction generation
    # ---------------------------
    def generate_predictions(self, features: pd.DataFrame) -> pd.DataFrame:
        if features.empty:
            print("No features available for predictions")
            return pd.DataFrame()

        results = []

        for position in self.positions:
            pos_data = features[features["position"] == position].copy()
            if len(pos_data) == 0:
                continue

            # If no model for this position, train now (lazy)
            if position not in self.models or not self.models[position]:
                X, y, cols = self.prepare_training_data(pos_data)
                if X.empty:
                    continue
                models, scaler = self.train_models(X, y, position)
                self.models[position] = models
                self.scalers[position] = scaler
                self.feature_columns[position] = cols

            # Prepare inference matrix using training columns
            X_all, _, _ = self.prepare_training_data(pos_data)
            cols = self.feature_columns.get(position, [c for c in X_all.columns])
            cols = [c for c in cols if c in X_all.columns]
            if not cols:
                continue
            X_inf = X_all[cols]

            preds = self.predict_ensemble(X_inf, self.models[position], self.scalers.get(position))

            # Ownership & leverage
            ownership = self.predict_ownership(pos_data, preds)
            leverage = self.calculate_leverage(preds, ownership)

            # Emit rows
            for i, (idx, row) in enumerate(pos_data.iterrows()):
                name = row.get("name", f"{position}_{i}")
                team = row.get("team", "UNK")
                opp = row.get("opponent", "UNK")
                sal = int(pd.to_numeric(row.get("salary", 5000), errors="coerce") or 5000)

                proj = float(np.round(preds[i], 2)) if i < len(preds) else 0.0
                own = float(np.round(ownership[i], 2)) if i < len(ownership) else 0.0
                lev = float(np.round(leverage[i], 2)) if i < len(leverage) else 0.0

                # Reasonable value/floor/ceiling bands
                value = round(proj / max(1.0, sal / 1000.0), 3)
                ceiling = round(proj * 1.6, 2)
                floor = round(proj * 0.4, 2)

                results.append(
                    {
                        "player_id": row.get("player_id", f"{position}_{name}_{team}"),
                        "name": name,
                        "position": position,
                        "team": team,
                        "opponent": opp,
                        "salary": sal,
                        "projection": proj,
                        "ownership": own,
                        "leverage": lev,
                        "value": value,
                        "ceiling": ceiling,
                        "floor": floor,
                        "confidence": float(np.clip(np.random.beta(8, 2), 0.5, 0.95)),
                        "matchup": self.get_matchup_info(row),
                        "weather": self.get_weather_info(row),
                    }
                )

        if not results:
            print("No predictions generated - insufficient processed data")
            return pd.DataFrame()

        df_out = pd.DataFrame(results)

        # Remove exact duplicates by player+team+position (can happen with joins)
        df_out["dedup_key"] = (
            df_out["name"].astype(str).str.lower().str.strip()
            + "|"
            + df_out["team"].astype(str)
            + "|"
            + df_out["position"].astype(str)
        )
        df_out = df_out.drop_duplicates(subset=["dedup_key"]).drop(columns=["dedup_key"]).reset_index(drop=True)

        return df_out

    # ---------------------------
    # Stubs for extra info
    # ---------------------------
    def get_matchup_info(self, row: pd.Series) -> str:
        team = row.get("team", "UNK")
        opp = row.get("opponent", "UNK")
        return f"{team} vs {opp}"

    def get_weather_info(self, row: pd.Series) -> str:
        # Hook up your weather service here if you want live data.
        return "N/A"

    # ---------------------------
    # Full pipeline
    # ---------------------------
    def run_full_pipeline(self) -> pd.DataFrame:
        try:
            # Build & engineer features
            feats = self.create_features()
            if feats.empty:
                return pd.DataFrame()

            feats = self.engineer_features(feats)
            feats = self.add_team_features(feats)
            feats = self.add_matchup_features(feats)

            # Train per-position (lazy train also exists, but this warms up)
            self.models.clear()
            self.scalers.clear()
            self.feature_columns.clear()

            for pos in self.positions:
                pos_df = feats[feats["position"] == pos]
                if len(pos_df) < self.min_samples_to_train:
                    print(f"ℹ️ Skipping warm-up train for {pos} (only {len(pos_df)} rows)")
                    continue
                X, y, cols = self.prepare_training_data(pos_df)
                if X.empty:
                    continue
                models, scaler = self.train_models(X, y, pos)
                self.models[pos] = models
                self.scalers[pos] = scaler
                self.feature_columns[pos] = cols

            # Predict
            preds = self.generate_predictions(feats)

            # Clean to be JSON-safe right here (NaNs→0)
            preds = preds.replace([np.inf, -np.inf], np.nan).fillna(0)

            # Standardize types
            for col in ["salary", "projection", "ownership", "leverage", "value", "ceiling", "floor", "confidence"]:
                if col in preds.columns:
                    preds[col] = pd.to_numeric(preds[col], errors="coerce").fillna(0)

            return preds
        except Exception as e:
            print(f"CRITICAL ERROR initializing predictor: {e}")
            raise
