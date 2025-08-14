import React, { useState, useEffect } from 'react';
import { Target, DollarSign, TrendingUp, Shuffle, Download, Play } from 'lucide-react';

interface Player {
  id: string;
  name: string;
  position: string;
  team: string;
  salary: number;
  projection: number;
  ownership: number;
}

interface Lineup {
  QB: Player | null;
  RB1: Player | null;
  RB2: Player | null;
  WR1: Player | null;
  WR2: Player | null;
  WR3: Player | null;
  TE: Player | null;
  FLEX: Player | null;
  DST: Player | null;
}

interface StackOption {
  id: string;
  type: 'qb_wr' | 'qb_te' | 'game' | 'team';
  players: Player[];
  correlation: number;
  totalSalary: number;
  totalProjection: number;
  description: string;
}

const LineupBuilder: React.FC = () => {
  const [lineup, setLineup] = useState<Lineup>({
    QB: null,
    RB1: null,
    RB2: null,
    WR1: null,
    WR2: null,
    WR3: null,
    TE: null,
    FLEX: null,
    DST: null
  });

  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [selectedPosition, setSelectedPosition] = useState<keyof Lineup>('QB');
  const [stackOptions, setStackOptions] = useState<StackOption[]>([]);
  const [selectedStack, setSelectedStack] = useState<StackOption | null>(null);
  const [showStackBuilder, setShowStackBuilder] = useState(false);
  const [optimizationSettings, setOptimizationSettings] = useState({
    maxOwnership: 100,
    minProjection: 0,
    stackTeam: '',
    avoidChalk: false,
    enableStacking: true,
    stackType: 'qb_wr',
    stackBonus: 1.2,
    upsideMode: false,
    ceilingWeight: 0.5,
    contrarian: false
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock player data
    // Fetch real player data from API
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
            ownership: p.ownership
          }));
          setAvailablePlayers(playerData);
          
          // Fetch stack options
          return fetch('/api/stacks');
        } else {
          throw new Error(data.error || 'No predictions available');
        }
      })
      .then(response => response.json())
      .then(stackData => {
        if (stackData.stacks) {
          setStackOptions(stackData.stacks);
        } else {
          console.error('No stack data available:', stackData.error);
          setStackOptions([]);
        }
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setAvailablePlayers([]);
        setStackOptions([]);
      })
      .finally(() => {
      setLoading(false);
      });
  }, []);

  const generateStackOptions = (players: Player[]) => {
    const stacks: StackOption[] = [];
    
    // Group players by team
    const playersByTeam = players.reduce((acc, player) => {
      if (!acc[player.team]) acc[player.team] = [];
      acc[player.team].push(player);
      return acc;
    }, {} as Record<string, Player[]>);

    // Generate QB-WR stacks
    Object.entries(playersByTeam).forEach(([team, teamPlayers]) => {
      const qbs = teamPlayers.filter(p => p.position === 'QB');
      const wrs = teamPlayers.filter(p => p.position === 'WR');
      const tes = teamPlayers.filter(p => p.position === 'TE');
      
      qbs.forEach(qb => {
        // QB-WR stacks
        wrs.forEach(wr => {
          const correlation = 0.75 + Math.random() * 0.2; // 0.75-0.95
          stacks.push({
            id: `${qb.id}-${wr.id}`,
            type: 'qb_wr',
            players: [qb, wr],
            correlation,
            totalSalary: qb.salary + wr.salary,
            totalProjection: qb.projection + wr.projection,
            description: `${qb.name} + ${wr.name} (${team})`
          });
        });
        
        // QB-TE stacks
        tes.forEach(te => {
          const correlation = 0.65 + Math.random() * 0.2; // 0.65-0.85
          stacks.push({
            id: `${qb.id}-${te.id}`,
            type: 'qb_te',
            players: [qb, te],
            correlation,
            totalSalary: qb.salary + te.salary,
            totalProjection: qb.projection + te.projection,
            description: `${qb.name} + ${te.name} (${team})`
          });
        });
        
        // QB-WR-WR stacks (if multiple WRs available)
        if (wrs.length >= 2) {
          for (let i = 0; i < wrs.length - 1; i++) {
            for (let j = i + 1; j < wrs.length; j++) {
              const correlation = 0.6 + Math.random() * 0.15; // 0.6-0.75
              stacks.push({
                id: `${qb.id}-${wrs[i].id}-${wrs[j].id}`,
                type: 'team',
                players: [qb, wrs[i], wrs[j]],
                correlation,
                totalSalary: qb.salary + wrs[i].salary + wrs[j].salary,
                totalProjection: qb.projection + wrs[i].projection + wrs[j].projection,
                description: `${qb.name} + ${wrs[i].name} + ${wrs[j].name} (${team})`
              });
            }
          }
        }
      });
    });

    // Sort by correlation and projection
    stacks.sort((a, b) => (b.correlation * b.totalProjection) - (a.correlation * a.totalProjection));
    setStackOptions(stacks.slice(0, 20)); // Top 20 stacks
  };

  const setHighUpsideMode = () => {
    setOptimizationSettings({
      ...optimizationSettings,
      upsideMode: true,
      maxOwnership: 20, // Focus on lower owned players
      enableStacking: true,
      stackType: 'team', // Team stacks for correlation
      stackBonus: 1.5, // Higher correlation bonus
      ceilingWeight: 0.8, // Weight ceiling heavily
      contrarian: true
    });
  };

  const setCashGameMode = () => {
    setOptimizationSettings({
      ...optimizationSettings,
      upsideMode: false,
      maxOwnership: 100,
      enableStacking: false,
      stackBonus: 1.0,
      ceilingWeight: 0.2, // Focus on floor
      contrarian: false
    });
  };

  const applyStack = (stack: StackOption) => {
    const newLineup = { ...lineup };
    
    stack.players.forEach(player => {
      if (player.position === 'QB') {
        newLineup.QB = player;
      } else if (player.position === 'WR') {
        if (!newLineup.WR1) newLineup.WR1 = player;
        else if (!newLineup.WR2) newLineup.WR2 = player;
        else if (!newLineup.WR3) newLineup.WR3 = player;
        else newLineup.FLEX = player;
      } else if (player.position === 'TE') {
        if (!newLineup.TE) newLineup.TE = player;
        else newLineup.FLEX = player;
      } else if (player.position === 'RB') {
        if (!newLineup.RB1) newLineup.RB1 = player;
        else if (!newLineup.RB2) newLineup.RB2 = player;
        else newLineup.FLEX = player;
      }
    });
    
    setLineup(newLineup);
    setSelectedStack(stack);
    setShowStackBuilder(false);
  };

  const getTotalSalary = () => {
    return Object.values(lineup).reduce((total, player) => {
      return total + (player ? player.salary : 0);
    }, 0);
  };

  const getTotalProjection = () => {
    let baseProjection = Object.values(lineup).reduce((total, player) => {
      return total + (player ? player.projection : 0);
    }, 0);
    
    // Apply stacking bonus if applicable
    if (selectedStack && optimizationSettings.enableStacking) {
      const stackBonus = (selectedStack.correlation - 1) * optimizationSettings.stackBonus;
      baseProjection += baseProjection * stackBonus * 0.1; // 10% max bonus
    }
    
    return baseProjection;
  };

  const getAverageOwnership = () => {
    const playersInLineup = Object.values(lineup).filter(player => player !== null);
    if (playersInLineup.length === 0) return 0;
    return playersInLineup.reduce((total, player) => total + player!.ownership, 0) / playersInLineup.length;
  };

  const getStackInfo = () => {
    if (!selectedStack) return null;
    
    return {
      type: selectedStack.type,
      correlation: selectedStack.correlation,
      bonus: ((selectedStack.correlation - 1) * optimizationSettings.stackBonus * 0.1 * 100).toFixed(1)
    };
  };

  const addPlayerToLineup = (player: Player) => {
    const newLineup = { ...lineup };
    newLineup[selectedPosition] = player;
    setLineup(newLineup);
  };

  const removePlayerFromLineup = (position: keyof Lineup) => {
    const newLineup = { ...lineup };
    newLineup[position] = null;
    setLineup(newLineup);
  };

  const optimizeLineup = () => {
    // Call API to optimize lineup
    const constraints = {
      salary_cap: 50000,
      max_ownership: optimizationSettings.maxOwnership,
      min_projection: optimizationSettings.minProjection,
      enable_stacking: optimizationSettings.enableStacking,
      stack_type: optimizationSettings.stackType,
      upside_mode: optimizationSettings.upsideMode,
      ceiling_weight: optimizationSettings.ceilingWeight,
      contrarian: optimizationSettings.contrarian
    };

    fetch('/api/optimize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ constraints })
    })
    .then(response => response.json())
    .then(data => {
      if (data.lineup) {
        const optimizedLineup: Lineup = {
          QB: data.lineup.QB || null,
          RB1: data.lineup.RB1 || null,
          RB2: data.lineup.RB2 || null,
          WR1: data.lineup.WR1 || null,
          WR2: data.lineup.WR2 || null,
          WR3: data.lineup.WR3 || null,
          TE: data.lineup.TE || null,
          FLEX: data.lineup.FLEX || null,
          DST: data.lineup.DST || null
        };
        setLineup(optimizedLineup);
      } else {
        console.error('Optimization failed:', data.error);
      }
    })
    .catch(error => {
      console.error('Error optimizing lineup:', error);
    });
  };

  const positions: (keyof Lineup)[] = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'FLEX', 'DST'];

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
          <h2 className="text-2xl font-bold text-white">Lineup Builder</h2>
          <p className="text-slate-400">Build and optimize your DFS lineups</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={setHighUpsideMode}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
              optimizationSettings.upsideMode
                ? 'bg-orange-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>High Upside</span>
          </button>
          <button
            onClick={setCashGameMode}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
              !optimizationSettings.upsideMode
                ? 'bg-green-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            <DollarSign className="w-4 h-4" />
            <span>Cash Game</span>
          </button>
          <button
            onClick={() => setShowStackBuilder(!showStackBuilder)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Target className="w-4 h-4" />
            <span>Stacks</span>
          </button>
          <button
            onClick={optimizeLineup}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Shuffle className="w-4 h-4" />
            <span>Optimize</span>
          </button>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Stack Builder Modal */}
      {showStackBuilder && (
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Player Stacks</h3>
            <button
              onClick={() => setShowStackBuilder(false)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
            {stackOptions.map((stack) => (
              <div
                key={stack.id}
                className="bg-slate-700/30 rounded-lg p-4 hover:bg-slate-700/50 cursor-pointer transition-colors"
                onClick={() => applyStack(stack)}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    stack.type === 'qb_wr' ? 'bg-blue-500/20 text-blue-400' :
                    stack.type === 'qb_te' ? 'bg-green-500/20 text-green-400' :
                    stack.type === 'team' ? 'bg-purple-500/20 text-purple-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {stack.type.replace('_', '-').toUpperCase()}
                  </span>
                  <span className="text-sm text-slate-300">
                    {(stack.correlation * 100).toFixed(0)}% corr
                  </span>
                </div>
                
                <div className="text-sm font-medium text-white mb-1">
                  {stack.description}
                </div>
                
                <div className="flex justify-between text-xs text-slate-400">
                  <span>${stack.totalSalary.toLocaleString()}</span>
                  <span>{stack.totalProjection.toFixed(1)} pts</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lineup Display */}
        <div className="lg:col-span-2 space-y-4">
          {/* Lineup Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Salary</p>
                  <p className={`text-xl font-bold ${getTotalSalary() > 50000 ? 'text-red-400' : 'text-white'}`}>
                    ${getTotalSalary().toLocaleString()}
                  </p>
                </div>
                <DollarSign className="w-6 h-6 text-green-400" />
              </div>
              <div className="mt-1">
                <span className="text-slate-400 text-xs">/ $50,000</span>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Projection</p>
                  <p className="text-xl font-bold text-white">{getTotalProjection().toFixed(1)}</p>
                </div>
                <TrendingUp className="w-6 h-6 text-blue-400" />
              </div>
              <div className="mt-1">
                <span className="text-slate-400 text-xs">fantasy points</span>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Avg Ownership</p>
                  <p className="text-xl font-bold text-white">{getAverageOwnership().toFixed(1)}%</p>
                </div>
                <Target className="w-6 h-6 text-purple-400" />
              </div>
              <div className="mt-1">
                <span className="text-slate-400 text-xs">field ownership</span>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Stack Bonus</p>
                  <p className="text-xl font-bold text-white">
                    {selectedStack ? `+${getStackInfo()?.bonus}%` : '0%'}
                  </p>
                </div>
                <Play className="w-6 h-6 text-orange-400" />
              </div>
              <div className="mt-1">
                <span className="text-slate-400 text-xs">
                  {selectedStack ? selectedStack.type.replace('_', '-') : 'no stack'}
                </span>
              </div>
            </div>
          </div>

          {/* Stack Info */}
          {selectedStack && (
            <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 backdrop-blur-sm rounded-xl p-4 border border-purple-500/30">
              <div className="flex items-center space-x-2 mb-2">
                <Play className="w-5 h-5 text-purple-400" />
                <h4 className="text-lg font-semibold text-white">Active Stack</h4>
              </div>
              <p className="text-slate-300 mb-2">{selectedStack.description}</p>
              <div className="flex items-center space-x-4 text-sm">
                <span className="text-purple-400">
                  Correlation: {(selectedStack.correlation * 100).toFixed(0)}%
                </span>
                <span className="text-blue-400">
                  Bonus: +{getStackInfo()?.bonus}% projection
                </span>
                <button
                  onClick={() => setSelectedStack(null)}
                  className="text-red-400 hover:text-red-300 ml-auto"
                >
                  Remove Stack
                </button>
              </div>
            </div>
          )}

          {/* Lineup Slots */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">Current Lineup</h3>
            <div className="space-y-3">
              {positions.map((position) => {
                const player = lineup[position];
                return (
                  <div key={position} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-8 bg-slate-600 rounded flex items-center justify-center text-xs font-bold text-white">
                        {position}
                      </div>
                      {player ? (
                        <div>
                          <div className="text-sm font-medium text-white">{player.name}</div>
                          <div className="text-xs text-slate-400">{player.team} - ${player.salary.toLocaleString()}</div>
                        </div>
                      ) : (
                        <div className="text-sm text-slate-400">Select a player</div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {player && (
                        <>
                          <span className="text-sm text-slate-300">{player.projection.toFixed(1)} pts</span>
                          <button
                            onClick={() => removePlayerFromLineup(position)}
                            className="text-red-400 hover:text-red-300 text-sm"
                          >
                            Remove
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => setSelectedPosition(position)}
                        className={`px-3 py-1 rounded text-xs transition-colors ${
                          selectedPosition === position
                            ? 'bg-blue-600 text-white'
                            : 'bg-slate-600 text-slate-300 hover:bg-slate-500'
                        }`}
                      >
                        {player ? 'Change' : 'Add'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Player Selection */}
        <div className="space-y-4">
          {/* Optimization Settings */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-3">Optimization Settings</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300">Enable Stacking</span>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={optimizationSettings.enableStacking}
                    onChange={(e) => setOptimizationSettings({
                      ...optimizationSettings,
                      enableStacking: e.target.checked
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {optimizationSettings.enableStacking && (
                <>
                  <div>
                    <label className="block text-sm text-slate-300 mb-1">Stack Type</label>
                    <select
                      value={optimizationSettings.stackType}
                      onChange={(e) => setOptimizationSettings({
                        ...optimizationSettings,
                        stackType: e.target.value
                      })}
                      className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none text-sm"
                    >
                      <option value="qb_wr">QB-WR Stack</option>
                      <option value="qb_te">QB-TE Stack</option>
                      <option value="team">Team Stack</option>
                      <option value="game">Game Stack</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm text-slate-300 mb-1">
                      Stack Bonus: {optimizationSettings.stackBonus.toFixed(1)}x
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="2"
                      step="0.1"
                      value={optimizationSettings.stackBonus}
                      onChange={(e) => setOptimizationSettings({
                        ...optimizationSettings,
                        stackBonus: parseFloat(e.target.value)
                      })}
                      className="w-full"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm text-slate-300 mb-1">Max Ownership %</label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={optimizationSettings.maxOwnership}
                  onChange={(e) => setOptimizationSettings({
                    ...optimizationSettings,
                    maxOwnership: parseInt(e.target.value)
                  })}
                  className="w-full"
                />
                <span className="text-xs text-slate-400">{optimizationSettings.maxOwnership}%</span>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-1">Min Projection</label>
                <input
                  type="range"
                  min="0"
                  max="30"
                  value={optimizationSettings.minProjection}
                  onChange={(e) => setOptimizationSettings({
                    ...optimizationSettings,
                    minProjection: parseInt(e.target.value)
                  })}
                  className="w-full"
                />
                <span className="text-xs text-slate-400">{optimizationSettings.minProjection} pts</span>
              </div>
            </div>
          </div>

          {/* Available Players */}
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-3">
              Available {selectedPosition === 'FLEX' ? 'RB/WR/TE' : selectedPosition}s
            </h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {availablePlayers
                .filter(player => {
                  if (selectedPosition === 'FLEX') {
                    return ['RB', 'WR', 'TE'].includes(player.position);
                  }
                  if (selectedPosition.startsWith('RB')) return player.position === 'RB';
                  if (selectedPosition.startsWith('WR')) return player.position === 'WR';
                  return player.position === selectedPosition;
                })
                .sort((a, b) => b.projection - a.projection)
                .map((player) => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between p-2 bg-slate-700/30 rounded hover:bg-slate-700/50 cursor-pointer transition-colors"
                    onClick={() => addPlayerToLineup(player)}
                  >
                    <div>
                      <div className="text-sm font-medium text-white">{player.name}</div>
                      <div className="text-xs text-slate-400">
                        {player.team} - ${player.salary.toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-300">{player.projection.toFixed(1)}</div>
                      <div className="text-xs text-slate-400">{player.ownership.toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LineupBuilder;