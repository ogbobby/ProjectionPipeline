import React from 'react';
import { TrendingUp, Target, Users, Zap, AlertTriangle, CheckCircle } from 'lucide-react';

const StrategyGuide: React.FC = () => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700 mb-6">
      <div className="flex items-center mb-4">
        <Zap className="w-6 h-6 text-orange-400 mr-2" />
        <h3 className="text-lg font-semibold text-white">High Upside DraftKings Strategy</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Player Selection */}
        <div className="space-y-3">
          <div className="flex items-center">
            <Target className="w-5 h-5 text-blue-400 mr-2" />
            <h4 className="font-semibold text-white">Player Selection</h4>
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Target players with <strong>high ceiling</strong> (25+ pts)</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Focus on <strong>low ownership</strong> (&lt;15%)</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Look for <strong>high leverage</strong> spots (8%+)</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Prioritize <strong>game script</strong> upside</span>
            </li>
          </ul>
        </div>

        {/* Stacking Strategy */}
        <div className="space-y-3">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-purple-400 mr-2" />
            <h4 className="font-semibold text-white">Stacking Strategy</h4>
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span><strong>QB-WR stacks</strong> for correlation</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span><strong>Team stacks</strong> in high total games</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span><strong>Game stacks</strong> for shootouts</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Avoid <strong>negative correlation</strong></span>
            </li>
          </ul>
        </div>

        {/* Risk Management */}
        <div className="space-y-3">
          <div className="flex items-center">
            <AlertTriangle className="w-5 h-5 text-yellow-400 mr-2" />
            <h4 className="font-semibold text-white">Risk Management</h4>
          </div>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Build <strong>multiple lineups</strong> (20-150)</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Vary <strong>player exposure</strong> (10-40%)</span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Balance <strong>ceiling vs floor</strong></span>
            </li>
            <li className="flex items-start">
              <CheckCircle className="w-4 h-4 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
              <span>Consider <strong>late swap</strong> strategy</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Quick Tips */}
      <div className="mt-6 p-4 bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-lg border border-orange-500/30">
        <div className="flex items-center mb-2">
          <Zap className="w-5 h-5 text-orange-400 mr-2" />
          <h4 className="font-semibold text-white">Pro Tips for GPPs</h4>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-300">
          <div>
            <strong className="text-orange-400">Contrarian Approach:</strong> Fade chalk players even if they're good plays
          </div>
          <div>
            <strong className="text-orange-400">Weather Leverage:</strong> Target players in good weather when others avoid
          </div>
          <div>
            <strong className="text-orange-400">Injury Pivots:</strong> Quick pivots when stars are ruled out
          </div>
          <div>
            <strong className="text-orange-400">Narrative Fades:</strong> Avoid obvious storyline plays
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategyGuide;