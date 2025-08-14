import React, { useState } from 'react';
import { TrendingUp, Users, Target, BarChart3, Settings, Play } from 'lucide-react';
import PlayerProjections from './components/PlayerProjections';
import OwnershipAnalysis from './components/OwnershipAnalysis';
import LineupBuilder from './components/LineupBuilder';
import ModelSettings from './components/ModelSettings';

function App() {
  const [activeTab, setActiveTab] = useState('projections');

  const tabs = [
    { id: 'projections', label: 'Player Projections', icon: TrendingUp },
    { id: 'ownership', label: 'Ownership Analysis', icon: Users },
    { id: 'lineup', label: 'Lineup Builder', icon: Target },
    { id: 'settings', label: 'Model Settings', icon: Settings },
  ];

  const renderActiveComponent = () => {
    switch (activeTab) {
      case 'projections':
        return <PlayerProjections />;
      case 'ownership':
        return <OwnershipAnalysis />;
      case 'lineup':
        return <LineupBuilder />;
      case 'settings':
        return <ModelSettings />;
      default:
        return <PlayerProjections />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">NFL DFS Predictor</h1>
                <p className="text-sm text-slate-400">Machine Learning Fantasy Football</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm font-medium">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span>Live Data</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-slate-800/30 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderActiveComponent()}
      </main>
    </div>
  );
}

export default App;