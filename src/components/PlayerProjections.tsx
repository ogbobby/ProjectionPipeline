import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Star, Filter, Download } from 'lucide-react';

interface PlayerProjection {
  id: string;
  name: string;
  position: string;
  team: string;
  salary: number;
  projection: number;
  ownership: number;
  value: number;
  ceiling: number;
  floor: number;
  confidence: number;
  matchup: string;
  weather?: string;
}

const PlayerProjections: React.FC = () => {
  const [players, setPlayers] = useState<PlayerProjection[]>([]);
  const [filteredPlayers, setFilteredPlayers] = useState<PlayerProjection[]>([]);
  const [selectedPosition, setSelectedPosition] = useState('ALL');
  const [sortBy, setSortBy] = useState('projection');
  const [loading, setLoading] = useState(true);

  // Mock data - in real app, this would come from your Python backend
  useEffect(() => {
    // Fetch real data from API
    fetch('/api/predictions')
      .then(response => response.json())
      .then(data => {
        if (data.predictions) {
          const playerData = data.predictions.map((p: any) => ({
            id: p.player_id,
            name: p.name,
            position: p.position,
            team: p.team,
            salary: p.salary,
            projection: p.projection,
            ownership: p.ownership,
            value: p.value,
            ceiling: p.ceiling,
            floor: p.floor,
            confidence: p.confidence,
            matchup: p.matchup,
            weather: p.weather
          }));
          setPlayers(playerData);
          setFilteredPlayers(playerData);
        } else {
          console.error('No predictions data available:', data.error);
          setPlayers([]);
          setFilteredPlayers([]);
        }
      })
      .catch(error => {
        console.error('Error fetching predictions:', error);
        setPlayers([]);
        setFilteredPlayers([]);
      })
      .finally(() => {
      setLoading(false);
      });
  }, []);

  useEffect(() => {
    let filtered = players;
    
    if (selectedPosition !== 'ALL') {
      filtered = filtered.filter(player => player.position === selectedPosition);
    }

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'projection':
          return b.projection - a.projection;
        case 'value':
          return b.value - a.value;
        case 'ownership':
          return a.ownership - b.ownership;
        case 'ceiling':
          return b.ceiling - a.ceiling;
        default:
          return b.projection - a.projection;
      }
    });

    setFilteredPlayers(filtered);
  }, [players, selectedPosition, sortBy]);

  const positions = ['ALL', 'QB', 'RB', 'WR', 'TE'];

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
          <h2 className="text-2xl font-bold text-white">Player Projections</h2>
          <p className="text-slate-400">ML-powered fantasy point predictions</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
          <Download className="w-4 h-4" />
          <span>Export CSV</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-slate-300 font-medium">Filters:</span>
          </div>
          
          <select
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            {positions.map(pos => (
              <option key={pos} value={pos}>{pos}</option>
            ))}
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
          >
            <option value="projection">Sort by Projection</option>
            <option value="value">Sort by Value</option>
            <option value="ownership">Sort by Ownership</option>
            <option value="ceiling">Sort by Ceiling</option>
          </select>
        </div>
      </div>

      {/* Players Table */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Player</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Salary</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Projection</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Value</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Ownership</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Range</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Confidence</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">Matchup</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {filteredPlayers.map((player) => (
                <tr key={player.id} className="hover:bg-slate-700/30 transition-colors">
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
                        <div className="text-sm font-medium text-white">{player.name}</div>
                        <div className="text-sm text-slate-400">{player.team}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                    ${player.salary.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-white">{player.projection.toFixed(1)}</span>
                      {player.projection > 20 && <TrendingUp className="w-4 h-4 text-green-400 ml-1" />}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${
                      player.value > 2.5 ? 'text-green-400' : 
                      player.value > 2.0 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {player.value.toFixed(2)}x
                    </span>
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-300">
                    {player.floor.toFixed(1)} - {player.ceiling.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-12 bg-slate-700 rounded-full h-2 mr-2">
                        <div 
                          className={`h-2 rounded-full ${
                            player.confidence > 0.8 ? 'bg-green-500' :
                            player.confidence > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${player.confidence * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-slate-300">{(player.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-slate-300">{player.matchup}</div>
                    {player.weather && (
                      <div className="text-xs text-slate-400">{player.weather}</div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PlayerProjections;