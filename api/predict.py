#!/usr/bin/env python3
"""
NFL DFS Prediction API
Integrates with the existing scrapers to build ML models for fantasy football predictions
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Add the scripts directory to path to import our scrapers
current_dir = os.path.dirname(__file__)
scripts_dir = os.path.join(current_dir, '..', 'scripts')
sys.path.append(scripts_dir)

try:
    from nflpyStats import GetQBData, GetRBData, GetWRData, GetTEData, GetDepthCharts
    from playerStatScraper import redZonePassing, redZoneRushing, redZoneReceiving, PosPtsperWeek, boomBust
    from teamScrapers import TurnDiff, PenDiff, TeamScoring, targetDistro, Schedule2025, teamDEFData, advancedDEFData
    print("Successfully imported all scrapers")
except ImportError as e:
    print(f"Error importing scrapers: {e}")
    print(f"Scripts directory: {scripts_dir}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

class NFLDFSPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_columns = {}
        self.positions = ['QB', 'RB', 'WR', 'TE']
        self.current_week = self.get_current_week()
        
    def get_current_week(self):
        """Determine current NFL week"""
        now = datetime.now()
        if now.month >= 9 or (now.month == 8 and now.day >= 15):
            week_start = datetime(now.year, 9, 1)
            weeks_passed = (now - week_start).days // 7
            return min(max(1, weeks_passed + 1), 18)
        return 1
    
    def load_data(self):
        """Load and combine data from all sources"""
        print("Loading real NFL data from scrapers...")
        
        all_players = pd.DataFrame()
        team_data = pd.DataFrame()
        target_data = pd.DataFrame()
        def_data = pd.DataFrame()
        schedule = pd.DataFrame()
        
        try:
            print("Loading QB data...")
            qb_data = GetQBData()
            if not qb_data.empty:
                print(f"Loaded {len(qb_data)} QB records")
                all_players = pd.concat([all_players, qb_data], ignore_index=True)
            else:
                print("No QB data returned")
        except Exception as e:
            print(f"Error loading QB data: {e}")
        
        try:
            print("Loading RB data...")
            rb_data = GetRBData()
            if not rb_data.empty:
                print(f"Loaded {len(rb_data)} RB records")
                all_players = pd.concat([all_players, rb_data], ignore_index=True)
            else:
                print("No RB data returned")
        except Exception as e:
            print(f"Error loading RB data: {e}")
        
        try:
            print("Loading WR data...")
            wr_data = GetWRData()
            if not wr_data.empty:
                print(f"Loaded {len(wr_data)} WR records")
                all_players = pd.concat([all_players, wr_data], ignore_index=True)
            else:
                print("No WR data returned")
        except Exception as e:
            print(f"Error loading WR data: {e}")
        
        try:
            print("Loading TE data...")
            te_data = GetTEData()
            if not te_data.empty:
                print(f"Loaded {len(te_data)} TE records")
                all_players = pd.concat([all_players, te_data], ignore_index=True)
            else:
                print("No TE data returned")
        except Exception as e:
            print(f"Error loading TE data: {e}")
        
        print(f"Total player records loaded: {len(all_players)}")
        
        # Load team data
        try:
            print("Loading team scoring data...")
            team_scoring_2024 = TeamScoring(2024)
            team_scoring_2023 = TeamScoring(2023)
            if not team_scoring_2024.empty and not team_scoring_2023.empty:
                team_data = pd.concat([team_scoring_2024, team_scoring_2023], ignore_index=True)
                print(f"Loaded {len(team_data)} team scoring records")
        except Exception as e:
            print(f"Error loading team data: {e}")
        
        try:
            print("Loading target distribution data...")
            target_data_2024 = targetDistro(2024)
            target_data_2023 = targetDistro(2023)
            if not target_data_2024.empty and not target_data_2023.empty:
                target_data = pd.concat([target_data_2024, target_data_2023], ignore_index=True)
                print(f"Loaded {len(target_data)} target distribution records")
        except Exception as e:
            print(f"Error loading target data: {e}")
        
        try:
            print("Loading defensive data...")
            def_data_2024 = teamDEFData(2024)
            def_data_2023 = teamDEFData(2023)
            if not def_data_2024.empty and not def_data_2023.empty:
                def_data = pd.concat([def_data_2024, def_data_2023], ignore_index=True)
                print(f"Loaded {len(def_data)} defensive records")
        except Exception as e:
            print(f"Error loading defensive data: {e}")
        
        try:
            print("Loading 2025 schedule...")
            schedule = Schedule2025()
            if not schedule.empty:
                print(f"Loaded {len(schedule)} schedule records")
        except Exception as e:
            print(f"Error loading schedule: {e}")
        
        return all_players, team_data, target_data, def_data, schedule
    
    def engineer_features(self, df, team_data, target_data, def_data, schedule):
        """Create features for ML model"""
        if df.empty:
            print("No player data to engineer features from")
            return pd.DataFrame()
            
        print("Engineering features from real data...")
        features = df.copy()
        
        # Ensure we have the required columns
        if 'fantasy_points_ppr' not in features.columns:
            print("Error: fantasy_points_ppr column not found in data")
            return pd.DataFrame()
        
        # Clean and standardize data
        features = features.dropna(subset=['fantasy_points_ppr'])
        features['fantasy_points'] = features['fantasy_points_ppr']
        
        # Position encoding
        if 'position' in features.columns:
            position_dummies = pd.get_dummies(features['position'], prefix='pos')
            features = pd.concat([features, position_dummies], axis=1)
        
        # Team encoding
        if 'recent_team' in features.columns:
            team_dummies = pd.get_dummies(features['recent_team'], prefix='team')
            features = pd.concat([features, team_dummies], axis=1)
        
        # Generate salary estimates based on performance
        features['salary'] = self.estimate_salary(features)
        features['salary_per_k'] = features['salary'] / 1000
        
        # Performance features
        features['total_yards'] = (features.get('passing_yards', 0).fillna(0) + 
                                 features.get('rushing_yards', 0).fillna(0) + 
                                 features.get('receiving_yards', 0).fillna(0))
        
        features['total_tds'] = (features.get('passing_tds', 0).fillna(0) + 
                               features.get('rushing_tds', 0).fillna(0) + 
                               features.get('receiving_tds', 0).fillna(0))
        
        # Touch-based metrics
        features['touches'] = (features.get('carries', 0).fillna(0) + 
                             features.get('targets', 0).fillna(0))
        
        features['yards_per_touch'] = features['total_yards'] / np.maximum(features['touches'], 1)
        features['td_rate'] = features['total_tds'] / np.maximum(features['touches'], 1)
        
        # Add team strength features
        features = self.add_team_features(features, team_data, def_data)
        
        # Add matchup features
        features = self.add_matchup_features(features, schedule)
        
        # Rolling averages for players with multiple games
        if 'player_id' in features.columns:
            for col in ['fantasy_points', 'targets', 'carries', 'total_tds', 'total_yards']:
                if col in features.columns:
                    features[f'{col}_avg_3'] = features.groupby('player_id')[col].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
                    features[f'{col}_trend'] = features.groupby('player_id')[col].pct_change(periods=2).fillna(0)

        # Final cleanup: remove inf and NaN
        features = features.replace([np.inf, -np.inf], np.nan).fillna(0)

        print(f"Feature engineering complete. Shape: {features.shape}")
        return features
    
    def estimate_salary(self, df):
        """Estimate DFS salary based on performance and position"""
        salary = np.zeros(len(df))
        
        for pos in self.positions:
            if 'position' not in df.columns:
                continue
                
            pos_mask = df['position'] == pos
            if pos_mask.sum() == 0:
                continue
                
            pos_data = df[pos_mask]
            fantasy_points = pos_data['fantasy_points_ppr']
            
            # Position-specific salary ranges
            if pos == 'QB':
                base_salary = 6000
                max_salary = 9500
            elif pos == 'RB':
                base_salary = 4500
                max_salary = 9000
            elif pos == 'WR':
                base_salary = 4000
                max_salary = 8500
            else:  # TE
                base_salary = 3500
                max_salary = 7500
            
            # Scale salary based on fantasy points percentile within position
            if len(fantasy_points) > 1:
                fp_percentile = fantasy_points.rank(pct=True)
                pos_salary = base_salary + (max_salary - base_salary) * fp_percentile
            else:
                pos_salary = pd.Series([base_salary + 1000] * len(fantasy_points))
            
            # Add some variation
            pos_salary += np.random.normal(0, 200, len(pos_salary))
            pos_salary = np.clip(pos_salary, base_salary - 500, max_salary + 500)
            
            salary[pos_mask] = pos_salary.astype(int)
        
        return salary
    
    def add_team_features(self, features, team_data, def_data):
        """Add team-level features"""
        if team_data.empty or 'recent_team' not in features.columns:
            print("No team data available or missing team column")
            return features
            
        print("Adding team features...")
        
        # Safely merge team offensive data
        try:
            if 'Team' in team_data.columns:
                # Get numeric columns for aggregation
                numeric_cols = team_data.select_dtypes(include=[np.number]).columns.tolist()
                if 'Team' in numeric_cols:
                    numeric_cols.remove('Team')
                
                if numeric_cols:
                    team_agg = team_data.groupby('Team')[numeric_cols].mean().reset_index()
                    features = features.merge(
                        team_agg, 
                        left_on='recent_team', 
                        right_on='Team', 
                        how='left',
                        suffixes=('', '_team')
                    )
        except Exception as e:
            print(f"Error adding team offensive features: {e}")
        
        # Safely add defensive features
        try:
            if not def_data.empty and 'Tm' in def_data.columns:
                numeric_def_cols = def_data.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_def_cols:
                    def_agg = def_data.groupby('Tm')[numeric_def_cols].mean().reset_index()
                    features = features.merge(
                        def_agg,
                        left_on='recent_team',
                        right_on='Tm',
                        how='left',
                        suffixes=('', '_def')
                    )
        except Exception as e:
            print(f"Error adding defensive features: {e}")
        
        return features
    
    def add_matchup_features(self, features, schedule):
        """Add matchup and game script features"""
        # Add basic week-based features
        if 'week' in features.columns:
            features['week_in_season'] = features['week']
            features['is_playoff_week'] = (features['week'] >= 15).astype(int)
            features['early_season'] = (features['week'] <= 4).astype(int)
        else:
            features['week_in_season'] = self.current_week
            features['is_playoff_week'] = 0
            features['early_season'] = 0
        
        # Add rest and weather features (simplified)
        features['days_rest'] = 7
        features['dome_game'] = 0
        features['cold_weather'] = 0
        
        return features
    
    def prepare_training_data(self, features):
        """Prepare data for training"""
        if features.empty:
            return pd.DataFrame(), pd.Series(), []
            
        # Remove non-feature columns
        exclude_cols = [
            'player_id', 'player_display_name', 'recent_team', 'position', 
            'week', 'season', 'Team', 'Tm', 'fantasy_points_ppr'
        ]
        
        feature_cols = [col for col in features.columns 
                       if col not in exclude_cols and col != 'fantasy_points']
        
        # Only keep numeric columns
        numeric_cols = []
        for col in feature_cols:
            if features[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                numeric_cols.append(col)
        
        if not numeric_cols:
            print("No numeric feature columns found")
            return pd.DataFrame(), pd.Series(), []
        
        X = features[numeric_cols].fillna(0)
        y = features['fantasy_points']
        
        print(f"Training data shape: X={X.shape}, y={y.shape}")
        print(f"Feature columns: {len(numeric_cols)}")
        # Ensure numeric and clean values
        X = features[numeric_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

        return X, y, numeric_cols
    
    def train_models(self, X, y, position):
        """Train ensemble of models for a position"""
        if len(X) < 10:
            print(f"Insufficient data for {position}: {len(X)} samples")
            return {}, StandardScaler()
            
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X = pd.DataFrame(X).replace([np.inf, -np.inf], np.nan).fillna(0)
        y = pd.Series(y).replace([np.inf, -np.inf], np.nan).fillna(0)
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        models = {}
        
        try:
            # Random Forest
            rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
            rf.fit(X_train, y_train)
            rf_pred = rf.predict(X_test)
            rf_mae = mean_absolute_error(y_test, rf_pred)
            rf_r2 = r2_score(y_test, rf_pred)
            print(f"{position} RF - MAE: {rf_mae:.2f}, R2: {rf_r2:.3f}")
            models['rf'] = rf
        except Exception as e:
            print(f"Error training RF for {position}: {e}")
        
        try:
            # Gradient Boosting
            gb = GradientBoostingRegressor(n_estimators=50, random_state=42)
            gb.fit(X_train, y_train)
            gb_pred = gb.predict(X_test)
            gb_mae = mean_absolute_error(y_test, gb_pred)
            gb_r2 = r2_score(y_test, gb_pred)
            print(f"{position} GB - MAE: {gb_mae:.2f}, R2: {gb_r2:.3f}")
            models['gb'] = gb
        except Exception as e:
            print(f"Error training GB for {position}: {e}")
        
        return models, scaler
    
    def predict_ensemble(self, X, models, scaler, position):
        """Make ensemble predictions"""
        if not models:
            # Return average historical performance if no models
            return np.full(len(X), 12.0)  # Average fantasy points
        
        predictions = []
        
        # Get predictions from available models
        if 'rf' in models:
            rf_pred = models['rf'].predict(X)
            predictions.append(rf_pred)
        
        if 'gb' in models:
            gb_pred = models['gb'].predict(X)
            predictions.append(gb_pred)
        
        if predictions:
            # Average the predictions
            ensemble_pred = np.mean(predictions, axis=0)
        else:
            ensemble_pred = np.full(len(X), 12.0)
        
        return ensemble_pred
    
    def predict_ownership(self, features, projections):
        """Predict ownership based on projections and other factors"""
        ownership = np.zeros(len(features))

        # Ensure projections is a DataFrame
        if not isinstance(projections, pd.DataFrame):
            projections = pd.DataFrame({'projection': np.asarray(projections)}, index=features.index)

        # Force alignment to features index
        projections = projections.reindex(features.index)

        for pos in self.positions:
            if 'position' not in features.columns:
                continue

            pos_mask = features['position'] == pos
            if pos_mask.sum() == 0:
                continue

            pos_features = features[pos_mask].copy()
            pos_projections = projections.loc[pos_mask, 'projection']

            # Salary and projection ranks within position
            if 'salary' in pos_features.columns:
                salary_rank = pos_features['salary'].rank(pct=True)
            else:
                salary_rank = pd.Series(np.random.uniform(0.3, 0.7, len(pos_features)), index=pos_features.index)

            proj_rank = pd.Series(pos_projections).rank(pct=True)

            # Base ownership model
            base_ownership = proj_rank * 0.6 + (1 - salary_rank) * 0.4

            # Scale to reasonable ownership range
            pos_ownership = base_ownership * np.random.uniform(15, 30, len(base_ownership))
            pos_ownership = np.clip(pos_ownership, 1, 40)

            # Safety check for length mismatch
            if pos_ownership.shape[0] != pos_mask.sum():
                print(f"⚠️ Mismatch for {pos}: "
                      f"pos_ownership={pos_ownership.shape[0]}, mask sum={pos_mask.sum()}")
                # Trim or pad
                if pos_ownership.shape[0] > pos_mask.sum():
                    pos_ownership = pos_ownership[:pos_mask.sum()]
                else:
                    pos_ownership = np.pad(pos_ownership,
                                           (0, pos_mask.sum() - pos_ownership.shape[0]),
                                           mode='constant')

            ownership[pos_mask] = pos_ownership

        return ownership
    
    # def predict_ownership(self, features, projections):
    #     """Predict ownership based on projections and other factors"""
    #     ownership = np.zeros(len(features))
        
    #     for pos in self.positions:
    #         if 'position' not in features.columns:
    #             continue
                
    #         pos_mask = features['position'] == pos
    #         if pos_mask.sum() == 0:
    #             continue
                
    #         pos_features = features[pos_mask].copy()
            
    #         # Get projections for this position
    #         if hasattr(projections, '__getitem__'):
    #             # If projections is an array/list, get the corresponding indices
    #             pos_indices = np.where(pos_mask)[0]
    #             pos_projections = projections[pos_indices] if len(projections) > max(pos_indices) else projections
    #         else:
    #             pos_projections = projections
            
    #         # Salary and projection ranks within position
    #         if 'salary' in pos_features.columns:
    #             salary_rank = pos_features['salary'].rank(pct=True)
    #         else:
    #             salary_rank = pd.Series(np.random.uniform(0.3, 0.7, len(pos_features)))
                
    #         # Ensure pos_projections is the right length
    #         if len(pos_projections) != len(pos_features):
    #             pos_projections = np.full(len(pos_features), np.mean(pos_projections) if len(pos_projections) > 0 else 12.0)
                
    #         proj_rank = pd.Series(pos_projections).rank(pct=True)
            
    #         # Base ownership model
    #         base_ownership = proj_rank * 0.6 + (1 - salary_rank) * 0.4
            
    #         # Scale to reasonable ownership range
    #         pos_ownership = base_ownership * np.random.uniform(15, 30, len(base_ownership))
    #         pos_ownership = np.clip(pos_ownership, 1, 40)
            
    #         ownership[pos_mask] = pos_ownership
        
    #     return ownership
    def calculate_leverage(self, proj_values, ownership):
        """Calculate leverage scores"""
        if isinstance(proj_values, pd.DataFrame):
            # Assume the main projection column is named 'projection'
            if 'projection' in proj_values.columns:
                proj_values = proj_values['projection']
            else:
                proj_values = proj_values.iloc[:, 0]  # take first column

        proj_pct = pd.Series(proj_values).rank(pct=True)
        own_pct = pd.Series(ownership).rank(pct=True)
        leverage = proj_pct - own_pct
        return leverage * 100
    
    # def calculate_leverage(self, projections, ownership):
    #     """Calculate leverage scores"""
    #     # Ensure we're working with arrays/lists, not DataFrames
    #     if hasattr(projections, 'values'):
    #         proj_values = projections.values
    #     else:
    #         proj_values = projections
            
    #     if hasattr(ownership, 'values'):
    #         own_values = ownership.values
    #     else:
    #         own_values = ownership
        
    #     proj_pct = pd.Series(proj_values).rank(pct=True)
    #     own_pct = pd.Series(own_values).rank(pct=True)
        
    #     leverage = (proj_pct - own_pct) * 100
    #     return leverage.values
    
    def run_full_pipeline(self):
        """Run the complete prediction pipeline"""
        print("Starting NFL DFS prediction pipeline...")
        
        # Load real data
        df, team_data, target_data, def_data, schedule = self.load_data()
        
        if df.empty:
            print("No player data loaded - cannot generate predictions")
            return pd.DataFrame()
        
        # Engineer features
        features = self.engineer_features(df, team_data, target_data, def_data, schedule)
        
        if features.empty:
            print("Feature engineering failed - cannot generate predictions")
            return pd.DataFrame()
        
        # Train models by position
        print("Training models by position...")
        for position in self.positions:
            pos_data = features[features['position'] == position].copy()
            if len(pos_data) < 10:
                print(f"Skipping {position} - insufficient data ({len(pos_data)} records)")
                continue
                
            X, y, feature_cols = self.prepare_training_data(pos_data)
            if X.empty:
                continue
                
            self.feature_columns[position] = feature_cols
            models, scaler = self.train_models(X, y, position)
            self.models[position] = models
            self.scalers[position] = scaler
        
        # Generate predictions
        print("Generating predictions...")
        predictions = self.generate_predictions(features)
        
        return predictions
    
    def generate_predictions(self, features):
        """Generate predictions for all players"""
        if features.empty:
            print("No features available for predictions")
            return pd.DataFrame()

        results = []

        for position in self.positions:
            pos_data = features[features['position'] == position].copy()
            if len(pos_data) == 0:
                continue
            
            if position not in self.models or not self.models[position]:
                print(f"No trained model for {position}")
                continue
            
            X, _, _ = self.prepare_training_data(pos_data)
            if X.empty:
                continue

            # Ensure same features as training
            if position in self.feature_columns:
                available_features = [col for col in self.feature_columns[position] if col in X.columns]
                if not available_features:
                    continue
                X = X[available_features]

            # Make predictions
            projections = self.predict_ensemble(X, self.models[position], self.scalers[position], position)

            # Ensure projections is a Series aligned to pos_data
            if not isinstance(projections, pd.Series):
                projections = pd.Series(projections, index=pos_data.index)

            ownership = self.predict_ownership(pos_data, projections)
            leverage = self.calculate_leverage(projections, ownership)
            leverage = np.nan_to_num(leverage) #added to remove nan values in leverage in json

            for i, (idx, row) in enumerate(pos_data.iterrows()):
                result = {
                    'player_id': row.get('player_id', f"{position}_{i}"),
                    'name': row.get('player_display_name', f"Player {i}"),
                    'position': position,
                    'team': row.get('recent_team', 'UNK'),
                    'salary': int(row.get('salary', 5000)),
                    'projection': round(projections.iloc[i], 1),
                    'ownership': round(ownership[i], 1),   # ownership is a NumPy array, still fine
                    'leverage': round(leverage[i], 1),     # leverage is also NumPy
                    'value': round(projections.iloc[i] / (row.get('salary', 5000) / 1000), 2),
                    'ceiling': round(projections.iloc[i] * 1.6, 1),
                    'floor': round(projections.iloc[i] * 0.4, 1),
                    'confidence': round(min(0.9, max(0.5, np.random.beta(8, 2))), 2),
                    'matchup': self.get_matchup_info(row),
                    'weather': self.get_weather_info(row)
                }
                results.append(result)

        if not results:
            print("No predictions generated - insufficient processed data")
            return pd.DataFrame()

        return pd.DataFrame(results)
    
    """ def generate_predictions(self, features):
        #Generate predictions for all players
        if features.empty:
            print("No features available for predictions")
            return pd.DataFrame()
            
        results = []
        
        for position in self.positions:
            pos_data = features[features['position'] == position].copy()
            if len(pos_data) == 0:
                continue
            
            if position not in self.models or not self.models[position]:
                print(f"No trained model for {position}")
                continue
            
            X, _, _ = self.prepare_training_data(pos_data)
            if X.empty:
                continue
                
            # Ensure same features as training
            if position in self.feature_columns:
                available_features = [col for col in self.feature_columns[position] if col in X.columns]
                if not available_features:
                    continue
                X = X[available_features]
            
            # Make predictions
            projections = self.predict_ensemble(X, self.models[position], self.scalers[position], position)
            # If projections is a DataFrame, flatten to Series

            # Ensure projections is a Series with correct index
            if isinstance(projections, np.ndarray):
                projections = pd.Series(projections, index=pos_data.index)
            elif isinstance(projections, pd.DataFrame) and projections.shape[1] == 1:
                projections = projections.iloc[:, 0]  # Flatten DataFrame to Series
            #if isinstance(projections, pd.DataFrame) and projections.shape[1] == 1:
            #    projections = projections.iloc[:, 0]
            # Ensure projections is a DataFrame and aligned to pos_data
            #if not isinstance(projections, pd.DataFrame):
            #    projections = pd.DataFrame({'projection': np.asarray(projections)}, index=pos_data.index)
            #else:
            #    projections = projections.reindex(pos_data.index)
            ownership = self.predict_ownership(pos_data, projections)
            leverage = self.calculate_leverage(projections, ownership)
            
            # Create results
            for i, (idx, row) in enumerate(pos_data.iterrows()):
                result = {
                    'player_id': row.get('player_id', f"{position}_{i}"),
                    'name': row.get('player_display_name', f"Player {i}"),
                    'position': position,
                    'team': row.get('recent_team', 'UNK'),
                    'salary': int(row.get('salary', 5000)),
                    #'projection': round(projections[i], 1),
                    'projection': round(projections.iloc[i], 1),
                    #'ownership': round(ownership[i], 1),
                    'ownership': round(ownership[i], 1),
                    #'leverage': round(leverage[i], 1),
                    'leverage': round(leverage[i], 1),
                    'value': round(projections[i] / (row.get('salary', 5000) / 1000), 2),
                    'ceiling': round(projections[i] * 1.6, 1),
                    'floor': round(projections[i] * 0.4, 1),
                    'confidence': round(min(0.9, max(0.5, np.random.beta(8, 2))), 2),
                    'matchup': self.get_matchup_info(row),
                    'weather': self.get_weather_info(row)
                }
                results.append(result)
        
        if not results:
            print("No predictions generated - insufficient processed data")
            return pd.DataFrame()
            
        return pd.DataFrame(results) """
    
    def get_matchup_info(self, player_row):
        """Get matchup information for a player"""
        team = player_row.get('recent_team', 'UNK')
        # Simple opponent mapping - in real implementation would use schedule data
        opponents = {
            'BUF': 'MIA', 'MIA': 'BUF', 'KC': 'DEN', 'DEN': 'KC',
            'SF': 'SEA', 'SEA': 'SF', 'PHI': 'DAL', 'DAL': 'PHI',
            'BAL': 'PIT', 'PIT': 'BAL', 'GB': 'MIN', 'MIN': 'GB'
        }
        opponent = opponents.get(team, 'TBD')
        return f"vs {opponent}"
    
    def get_weather_info(self, player_row):
        """Get weather information for a player's game"""
        weather_options = ['Clear', 'Cloudy', 'Light Rain', None]
        return np.random.choice(weather_options)
    
    def optimize_lineup(self, players_df, salary_cap=50000, max_ownership=100):
        """Simple greedy lineup optimization"""
        if players_df.empty:
            return {}
            
        positions_needed = {
            'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'FLEX': 1, 'DST': 1
        }
        
        # Filter players by ownership if specified
        if max_ownership < 100:
            players_df = players_df[players_df['ownership'] <= max_ownership].copy()
        
        # Calculate value (projection per $1000 salary)
        players_df['value'] = players_df['projection'] / (players_df['salary'] / 1000)
        
        lineup = {}
        remaining_salary = salary_cap
        
        # Fill core positions first
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_players = players_df[players_df['position'] == pos].copy()
            pos_players = pos_players[pos_players['salary'] <= remaining_salary]
            
            if len(pos_players) == 0:
                continue
                
            needed = positions_needed.get(pos, 1)
            if pos == 'RB':
                needed = 2
            elif pos == 'WR':
                needed = 3
            else:
                needed = 1
            
            # Sort by value and take top players
            pos_players = pos_players.sort_values('value', ascending=False)
            
            for i in range(min(needed, len(pos_players))):
                player = pos_players.iloc[i]
                if player['salary'] <= remaining_salary:
                    key = f"{pos}{i+1}" if needed > 1 else pos
                    lineup[key] = player.to_dict()
                    remaining_salary -= player['salary']
                    # Remove player from available pool
                    players_df = players_df[players_df['player_id'] != player['player_id']]
        
        # Fill FLEX with best remaining RB/WR/TE
        flex_players = players_df[players_df['position'].isin(['RB', 'WR', 'TE'])].copy()
        flex_players = flex_players[flex_players['salary'] <= remaining_salary]
        
        if len(flex_players) > 0:
            flex_players = flex_players.sort_values('value', ascending=False)
            flex_player = flex_players.iloc[0]
            lineup['FLEX'] = flex_player.to_dict()
            remaining_salary -= flex_player['salary']
        
        # Add DST (simplified)
        lineup['DST'] = {
            'player_id': 'dst_1',
            'name': 'Bills DST',
            'position': 'DST',
            'team': 'BUF',
            'salary': 3200,
            'projection': 8.5,
            'ownership': 6.2
        }
        
        return lineup

def main():
    """Main execution function"""
    predictor = NFLDFSPredictor()
    
    predictions_df = predictor.run_full_pipeline()
    
    if not predictions_df.empty:
        print(f"\nGenerated {len(predictions_df)} predictions")
        print("\nTop 5 Projections by Position:")
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_players = predictions_df[predictions_df['position'] == pos].nlargest(5, 'projection')
            if not pos_players.empty:
                print(f"\n{pos}:")
                for _, player in pos_players.iterrows():
                    print(f"  {player['name']} ({player['team']}) - {player['projection']} pts, ${player['salary']}, {player['ownership']}% owned")
    else:
        print("No predictions generated - check data sources")
    
    return predictions_df

if __name__ == "__main__":
    main()