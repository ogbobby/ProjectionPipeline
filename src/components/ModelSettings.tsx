import React, { useState } from 'react';
import { Settings, Database, Brain, TrendingUp, Save, RefreshCw } from 'lucide-react';

const ModelSettings: React.FC = () => {
  const [settings, setSettings] = useState({
    // Data Sources
    useNFLData: true,
    useFantasyPros: true,
    useRedZoneData: true,
    useWeatherData: true,
    useInjuryReports: true,
    
    // Model Parameters
    modelType: 'ensemble',
    lookbackWeeks: 8,
    weightRecency: 0.7,
    weatherImpact: 0.3,
    injuryDiscount: 0.15,
    
    // Ownership Prediction
    ownershipModel: 'gradient_boost',
    leverageThreshold: 8.0,
    contrarianThreshold: 5.0,
    
    // Lineup Optimization
    maxOwnership: 100,
    minProjection: 0,
    stackingBonus: 1.2,
    diversityPenalty: 0.1,
    
    // Risk Management
    maxExposure: 25,
    correlationLimit: 0.8,
    volatilityWeight: 0.2
  });

  const [isTraining, setIsTraining] = useState(false);
  const [lastUpdated, setLastUpdated] = useState('2024-01-15 14:30:00');

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const retrainModel = async () => {
    setIsTraining(true);
    // Simulate model training
    setTimeout(() => {
      setIsTraining(false);
      setLastUpdated(new Date().toLocaleString());
    }, 3000);
  };

  const saveSettings = () => {
    // In real app, this would save to backend
    console.log('Saving settings:', settings);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Model Settings</h2>
          <p className="text-slate-400">Configure your ML model parameters</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={retrainModel}
            disabled={isTraining}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isTraining ? 'animate-spin' : ''}`} />
            <span>{isTraining ? 'Training...' : 'Retrain Model'}</span>
          </button>
          <button
            onClick={saveSettings}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save Settings</span>
          </button>
        </div>
      </div>

      {/* Model Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Model Accuracy</p>
              <p className="text-2xl font-bold text-green-400">87.3%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
          <div className="mt-2">
            <span className="text-green-400 text-sm">↑ 2.1% from last week</span>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Data Points</p>
              <p className="text-2xl font-bold text-blue-400">45.2K</p>
            </div>
            <Database className="w-8 h-8 text-blue-400" />
          </div>
          <div className="mt-2">
            <span className="text-blue-400 text-sm">Last updated: {lastUpdated}</span>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Model Type</p>
              <p className="text-2xl font-bold text-purple-400">Ensemble</p>
            </div>
            <Brain className="w-8 h-8 text-purple-400" />
          </div>
          <div className="mt-2">
            <span className="text-purple-400 text-sm">XGBoost + Neural Net</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Sources */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Database className="w-5 h-5 mr-2" />
            Data Sources
          </h3>
          <div className="space-y-4">
            {[
              { key: 'useNFLData', label: 'NFL Official Data', description: 'Play-by-play, player stats' },
              { key: 'useFantasyPros', label: 'FantasyPros Data', description: 'Expert rankings, ownership' },
              { key: 'useRedZoneData', label: 'Red Zone Stats', description: 'Goal line opportunities' },
              { key: 'useWeatherData', label: 'Weather Data', description: 'Game conditions impact' },
              { key: 'useInjuryReports', label: 'Injury Reports', description: 'Player health status' }
            ].map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{label}</div>
                  <div className="text-xs text-slate-400">{description}</div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings[key as keyof typeof settings] as boolean}
                    onChange={(e) => handleSettingChange(key, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Model Parameters */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Brain className="w-5 h-5 mr-2" />
            Model Parameters
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Model Type</label>
              <select
                value={settings.modelType}
                onChange={(e) => handleSettingChange('modelType', e.target.value)}
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="ensemble">Ensemble (XGBoost + Neural Net)</option>
                <option value="xgboost">XGBoost Only</option>
                <option value="neural_net">Neural Network Only</option>
                <option value="linear">Linear Regression</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Lookback Weeks: {settings.lookbackWeeks}
              </label>
              <input
                type="range"
                min="4"
                max="16"
                value={settings.lookbackWeeks}
                onChange={(e) => handleSettingChange('lookbackWeeks', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Recency Weight: {settings.weightRecency.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.weightRecency}
                onChange={(e) => handleSettingChange('weightRecency', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Weather Impact: {settings.weatherImpact.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.weatherImpact}
                onChange={(e) => handleSettingChange('weatherImpact', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Ownership Prediction */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Ownership Prediction
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Ownership Model</label>
              <select
                value={settings.ownershipModel}
                onChange={(e) => handleSettingChange('ownershipModel', e.target.value)}
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
              >
                <option value="gradient_boost">Gradient Boosting</option>
                <option value="random_forest">Random Forest</option>
                <option value="neural_net">Neural Network</option>
                <option value="linear">Linear Model</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Leverage Threshold: {settings.leverageThreshold.toFixed(1)}%
              </label>
              <input
                type="range"
                min="5"
                max="15"
                step="0.5"
                value={settings.leverageThreshold}
                onChange={(e) => handleSettingChange('leverageThreshold', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Contrarian Threshold: {settings.contrarianThreshold.toFixed(1)}%
              </label>
              <input
                type="range"
                min="1"
                max="10"
                step="0.5"
                value={settings.contrarianThreshold}
                onChange={(e) => handleSettingChange('contrarianThreshold', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Risk Management */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            Risk Management
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Max Player Exposure: {settings.maxExposure}%
              </label>
              <input
                type="range"
                min="10"
                max="50"
                value={settings.maxExposure}
                onChange={(e) => handleSettingChange('maxExposure', parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Correlation Limit: {settings.correlationLimit.toFixed(2)}
              </label>
              <input
                type="range"
                min="0.5"
                max="1"
                step="0.05"
                value={settings.correlationLimit}
                onChange={(e) => handleSettingChange('correlationLimit', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Volatility Weight: {settings.volatilityWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.05"
                value={settings.volatilityWeight}
                onChange={(e) => handleSettingChange('volatilityWeight', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Stacking Bonus: {settings.stackingBonus.toFixed(2)}x
              </label>
              <input
                type="range"
                min="1"
                max="2"
                step="0.1"
                value={settings.stackingBonus}
                onChange={(e) => handleSettingChange('stackingBonus', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Training Progress */}
      {isTraining && (
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <h3 className="text-lg font-semibold text-white mb-4">Model Training Progress</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-slate-300">Processing data...</span>
              <span className="text-blue-400">33%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '33%' }}></div>
            </div>
            <p className="text-xs text-slate-400">
              Training ensemble model with {settings.lookbackWeeks} weeks of data...
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSettings;