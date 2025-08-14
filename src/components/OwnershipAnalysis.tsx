import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, AlertTriangle, Eye } from 'lucide-react';

interface OwnershipData {
  position: string;
  player: string;
  team: string;
  salary: number;
  projection: number;
  ownership: number;
  leverage: number;
  contrarian: boolean;
  stackWith: string[];
}

const OwnershipAnalysis: React.FC = () => {
  const [ownershipData, setOwnershipData] = useState<OwnershipData[]>([]);
  const [selectedView, setSelectedView] = useState('leverage');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch real ownership data from API
    fetch('/api/ownership')
      .then(response => response.json())
      .then(data => {
        if (data.high_leverage_players && data.contrarian_players) {
          const ownershipData = [
            ...data.high_leverage_players.map((p: any) => ({
              position: p.position,
              player: p.name,
              team: p.team,
              salary: p.salary,
              projection: p.projection,
              ownership: p.ownership,
              leverage: p.leverage,
              contrarian: p.ownership < 8,
              stackWith: [] // Would need additional API data for stack recommendations
            })),
            ...data.contrarian_players.map((p: any) => ({
              position: p.position,
              player: p.name,
              team: p.team,
              salary: p.salary,
              projection: p.projection,
              ownership: p.ownership,
              leverage: p.leverage,
              contrarian: true,
              stackWith: []
            }))
          ];
          
          // Remove duplicates
          const uniqueData = ownershipData.filter((item, index, self) => 
            index === self.findIndex(t => t.player === item.player)
          );
          
          setOwnershipData(uniqueData);
        } else {
          console.error('No ownership data available:', data.error);
          setOwnershipData([]);
        }
      })
      .catch(error => {
        console.error('Error fetching ownership data:', error);
        setOwnershipData([]);
      })
      .finally(() => {
      setLoading(false);
      });
  }, []);

  const getOwnershipTier = (ownership: number) => {
    if (ownership > 20) return { label: 'Chalk', color: 'text-red-400 bg-red-500/20' };
    if (ownership > 10) return { label: 'Popular', color: 'text-yellow-400 bg-yellow-500/20' };
    if (ownership > 5) return { label: 'Medium', color: 'text-blue-400 bg-blue-500/20' };
    return { label: 'Contrarian', color: 'text-green-400 bg-green-500/20' };
  };

  const getLeverageColor = (leverage: number) => {
    if (leverage > 12) return 'text-green-400';
    if (leverage > 8) return 'text-yellow-400';
    return 'text-red-400';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Ownership Analysis</h2>
          <p className="text-slate-400">Field ownership and leverage opportunities</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedView('leverage')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedView === 'leverage'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Leverage View
          </button>
          <button
            onClick={() => setSelectedView('contrarian')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedView === 'contrarian'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Contrarian Plays
          </button>
        </div>
      </div>

      {/* Ownership Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Ownership</p>
              <p className="text-2xl font-bold text-white">8.6%</p>
            </div>
            <Users className="w-8 h-8 text-blue-400" />
          </div>
          <div className="mt-2">
            <span className="text-green-400 text-sm">↓ 2.1% from last week</span>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">High Leverage</p>
              <p className="text-2xl font-bold text-white">12</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-400" />
          </div>
          <div className="mt-2">
            <span className="text-green-400 text-sm">Players &gt; 10% leverage</span>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Contrarian Plays</p>
              <p className="text-2xl font-bold text-white">8</p>
            </div>
            <Eye className="w-8 h-8 text-purple-400" />
          </div>
          <div className="mt-2">
            <span className="text-purple-400 text-sm">Low owned, high upside</span>
          </div>
        </div>

        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Chalk Alert</p>
              <p className="text-2xl font-bold text-white">3</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <div className="mt-2">
            <span className="text-red-400 text-sm">Players &gt; 20% owned</span>
          </div>
        </div>
      </div>

      {/* Ownership Table */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700">
          <h3 className="text-lg font-semibold text-white">
            {selectedView === 'leverage' ? 'High Leverage Opportunities' : 'Contrarian Plays'}
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Player</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Salary</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Projection</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Ownership</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Leverage</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Stack Options</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {ownershipData
                .filter(player => selectedView === 'leverage' ? player.leverage > 8 : player.contrarian)
                .sort((a, b) => selectedView === 'leverage' ? b.leverage - a.leverage : a.ownership - b.ownership)
                .map((player, index) => {
                  const ownershipTier = getOwnershipTier(player.ownership);
                  return (
                    <tr key={index} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white mr-3 ${
                            player.position === 'QB' ? 'bg-red-500' :
                            player.position === 'RB' ? 'bg-green-500' :
                            player.position === 'WR' ? 'bg-blue-500' : 'bg-yellow-500'
                          }`}>
                            {player.position}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-white">{player.player}</div>
                            <div className="text-sm text-slate-400">{player.team}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                        ${player.salary.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {player.projection.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-slate-700 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full" 
                              style={{ width: `${Math.min(player.ownership, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-slate-300">{player.ownership.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-medium ${getLeverageColor(player.leverage)}`}>
                          {player.leverage.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-wrap gap-1">
                          {player.stackWith.slice(0, 2).map((stackPlayer, idx) => (
                            <span key={idx} className="bg-slate-700 text-slate-300 px-2 py-1 rounded text-xs">
                              {stackPlayer}
                            </span>
                          ))}
                          {player.stackWith.length > 2 && (
                            <span className="text-slate-400 text-xs">+{player.stackWith.length - 2}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${ownershipTier.color}`}>
                          {ownershipTier.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ownership Distribution Chart */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-semibold text-white mb-4">Ownership Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">32</div>
            <div className="text-sm text-slate-400">Contrarian (&lt;5%)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">18</div>
            <div className="text-sm text-slate-400">Medium (5-10%)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">12</div>
            <div className="text-sm text-slate-400">Popular (10-20%)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-400">8</div>
            <div className="text-sm text-slate-400">Chalk (&gt;20%)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnershipAnalysis;