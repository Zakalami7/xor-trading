'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    Bot, TrendingUp, TrendingDown, DollarSign, Activity,
    Plus, Play, Pause, Square, Settings, BarChart3,
    Wallet, ArrowUpRight, ArrowDownRight, RefreshCw
} from 'lucide-react';
import Sidebar from '@/components/layout/Sidebar';

interface BotData {
    id: string;
    name: string;
    symbol: string;
    status: 'running' | 'paused' | 'stopped';
    strategy: string;
    pnl: number;
    pnlPercent: number;
    trades: number;
    winRate: number;
}

interface DashboardStats {
    totalPnl: number;
    totalPnlPercent: number;
    activeBots: number;
    openPositions: number;
    trades24h: number;
    winRate: number;
}

export default function DashboardPage() {
    const router = useRouter();
    const [stats, setStats] = useState<DashboardStats>({
        totalPnl: 12543.82,
        totalPnlPercent: 15.4,
        activeBots: 5,
        openPositions: 3,
        trades24h: 47,
        winRate: 68.5,
    });

    const [bots, setBots] = useState<BotData[]>([
        {
            id: '1',
            name: 'BTC Grid Bot',
            symbol: 'BTC/USDT',
            status: 'running',
            strategy: 'Grid Trading',
            pnl: 5420.50,
            pnlPercent: 8.2,
            trades: 124,
            winRate: 72.5,
        },
        {
            id: '2',
            name: 'ETH DCA Bot',
            symbol: 'ETH/USDT',
            status: 'running',
            strategy: 'DCA',
            pnl: 3215.00,
            pnlPercent: 12.1,
            trades: 45,
            winRate: 65.0,
        },
        {
            id: '3',
            name: 'SOL Scalper',
            symbol: 'SOL/USDT',
            status: 'paused',
            strategy: 'Scalping',
            pnl: -520.30,
            pnlPercent: -2.1,
            trades: 312,
            winRate: 58.2,
        },
    ]);

    return (
        <div className="flex h-screen bg-dark-100">
            <Sidebar />

            <main className="flex-1 overflow-auto">
                <div className="p-8">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h1 className="text-3xl font-bold">Dashboard</h1>
                            <p className="text-slate-400 mt-1">Welcome back! Here's your trading overview.</p>
                        </div>
                        <button
                            onClick={() => router.push('/dashboard/bots/new')}
                            className="btn-primary flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            New Bot
                        </button>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="stat-card"
                        >
                            <div className="flex items-center justify-between">
                                <div className="p-3 rounded-xl bg-primary-500/20">
                                    <DollarSign className="w-6 h-6 text-primary-400" />
                                </div>
                                <span className={`text-sm flex items-center gap-1 ${stats.totalPnl >= 0 ? 'profit' : 'loss'}`}>
                                    {stats.totalPnl >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                                    {stats.totalPnlPercent.toFixed(1)}%
                                </span>
                            </div>
                            <div className={`stat-value mt-4 ${stats.totalPnl >= 0 ? 'profit' : 'loss'}`}>
                                ${stats.totalPnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                            <div className="stat-label">Total PnL</div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="stat-card"
                        >
                            <div className="flex items-center justify-between">
                                <div className="p-3 rounded-xl bg-accent-500/20">
                                    <Bot className="w-6 h-6 text-accent-400" />
                                </div>
                                <span className="text-sm text-success flex items-center gap-1">
                                    <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
                                    Active
                                </span>
                            </div>
                            <div className="stat-value mt-4">{stats.activeBots}</div>
                            <div className="stat-label">Active Bots</div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="stat-card"
                        >
                            <div className="flex items-center justify-between">
                                <div className="p-3 rounded-xl bg-success/20">
                                    <Activity className="w-6 h-6 text-success" />
                                </div>
                            </div>
                            <div className="stat-value mt-4">{stats.trades24h}</div>
                            <div className="stat-label">Trades (24h)</div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            className="stat-card"
                        >
                            <div className="flex items-center justify-between">
                                <div className="p-3 rounded-xl bg-warning/20">
                                    <BarChart3 className="w-6 h-6 text-warning" />
                                </div>
                            </div>
                            <div className="stat-value mt-4">{stats.winRate}%</div>
                            <div className="stat-label">Win Rate</div>
                        </motion.div>
                    </div>

                    {/* Bots Table */}
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-semibold">Your Bots</h2>
                            <button className="btn-secondary text-sm flex items-center gap-2">
                                <RefreshCw className="w-4 h-4" />
                                Refresh
                            </button>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="text-left text-slate-400 text-sm border-b border-white/5">
                                        <th className="pb-4 font-medium">Bot</th>
                                        <th className="pb-4 font-medium">Symbol</th>
                                        <th className="pb-4 font-medium">Strategy</th>
                                        <th className="pb-4 font-medium">Status</th>
                                        <th className="pb-4 font-medium text-right">PnL</th>
                                        <th className="pb-4 font-medium text-right">Trades</th>
                                        <th className="pb-4 font-medium text-right">Win Rate</th>
                                        <th className="pb-4 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {bots.map((bot) => (
                                        <tr key={bot.id} className="border-b border-white/5 hover:bg-white/5 transition">
                                            <td className="py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center">
                                                        <Bot className="w-5 h-5 text-primary-400" />
                                                    </div>
                                                    <span className="font-medium">{bot.name}</span>
                                                </div>
                                            </td>
                                            <td className="py-4 font-mono text-sm">{bot.symbol}</td>
                                            <td className="py-4">
                                                <span className="px-3 py-1 rounded-full bg-dark-300 text-sm">
                                                    {bot.strategy}
                                                </span>
                                            </td>
                                            <td className="py-4">
                                                <span className={`flex items-center gap-2 ${bot.status === 'running' ? 'text-success' :
                                                    bot.status === 'paused' ? 'text-warning' : 'text-slate-400'
                                                    }`}>
                                                    <span className={`w-2 h-2 rounded-full ${bot.status === 'running' ? 'bg-success animate-pulse' :
                                                        bot.status === 'paused' ? 'bg-warning' : 'bg-slate-400'
                                                        }`} />
                                                    {bot.status.charAt(0).toUpperCase() + bot.status.slice(1)}
                                                </span>
                                            </td>
                                            <td className={`py-4 text-right font-mono ${bot.pnl >= 0 ? 'profit' : 'loss'}`}>
                                                {bot.pnl >= 0 ? '+' : ''}{bot.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({bot.pnlPercent}%)
                                            </td>
                                            <td className="py-4 text-right">{bot.trades}</td>
                                            <td className="py-4 text-right">{bot.winRate}%</td>
                                            <td className="py-4 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {bot.status === 'running' ? (
                                                        <button className="p-2 rounded-lg hover:bg-dark-300 transition text-warning">
                                                            <Pause className="w-4 h-4" />
                                                        </button>
                                                    ) : (
                                                        <button className="p-2 rounded-lg hover:bg-dark-300 transition text-success">
                                                            <Play className="w-4 h-4" />
                                                        </button>
                                                    )}
                                                    <button className="p-2 rounded-lg hover:bg-dark-300 transition text-danger">
                                                        <Square className="w-4 h-4" />
                                                    </button>
                                                    <button className="p-2 rounded-lg hover:bg-dark-300 transition text-slate-400">
                                                        <Settings className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
