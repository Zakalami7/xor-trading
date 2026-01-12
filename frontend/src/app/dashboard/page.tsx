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
import { authApi, botsApi, analyticsApi, strategiesApi } from '@/lib/api';
import toast from 'react-hot-toast';

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
    const [bots, setBots] = useState<BotData[]>([]);
    const [loading, setLoading] = useState(true);
    const [availableStrategies, setAvailableStrategies] = useState<any[]>([]);
    const [stats, setStats] = useState<DashboardStats>({
        totalPnl: 0,
        totalPnlPercent: 0,
        activeBots: 0,
        openPositions: 0,
        trades24h: 0,
        winRate: 0,
    });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [botsRes, dashboardRes, stratRes] = await Promise.all([
                botsApi.list(),
                analyticsApi.getDashboard(),
                strategiesApi.list()
            ]);

            const strategies = stratRes.data.items || stratRes.data || [];
            setAvailableStrategies(strategies);

            setBots((botsRes.data.items || []).map((b: any) => ({
                id: b.id,
                name: b.name,
                symbol: b.symbol,
                status: b.status,
                strategy: strategies.find((s: any) => s.id === b.strategy_id)?.name || b.strategy_id,
                pnl: b.total_pnl || 0,
                pnlPercent: b.total_pnl_percent || 0,
                trades: b.total_trades || 0,
                winRate: b.win_rate || 0,
            })));

            setStats({
                totalPnl: dashboardRes.data.pnl_24h || 0,
                totalPnlPercent: 0, // Backend doesn't provide 24h PnL % yet
                activeBots: dashboardRes.data.total_bots || 0,
                openPositions: dashboardRes.data.open_positions || 0,
                trades24h: dashboardRes.data.trades_24h || 0,
                winRate: 0, // Backend doesn't provide aggregate win rate yet
            });
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
            toast.error('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleAction = async (id: string, action: string) => {
        try {
            await botsApi.action(id, action);
            toast.success(`Bot ${action}ed successfully`);
            fetchData();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || `Failed to ${action} bot`);
        }
    };

    const deleteBot = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this bot?')) return;
        try {
            await botsApi.delete(id);
            toast.success('Bot deleted successfully');
            fetchData();
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to delete bot');
        }
    };

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
                            <button
                                onClick={fetchData}
                                disabled={loading}
                                className="btn-secondary text-sm flex items-center gap-2"
                            >
                                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
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
                                    {bots.length === 0 ? (
                                        <tr>
                                            <td colSpan={8} className="py-12 text-center text-slate-400">
                                                No bots found. Create your first bot to get started!
                                            </td>
                                        </tr>
                                    ) : (
                                        bots.map((bot) => (
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
                                                <td className={`py-4 text-right font-mono ${(bot.pnl || 0) >= 0 ? 'profit' : 'loss'}`}>
                                                    {(bot.pnl || 0) >= 0 ? '+' : ''}{(bot.pnl || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({(bot.pnlPercent || 0)}%)
                                                </td>
                                                <td className="py-4 text-right">{bot.trades || 0}</td>
                                                <td className="py-4 text-right">{bot.winRate || 0}%</td>
                                                <td className="py-4 text-right">
                                                    <div className="flex items-center justify-end gap-2">
                                                        {bot.status === 'running' ? (
                                                            <button
                                                                onClick={() => handleAction(bot.id, 'pause')}
                                                                title="Pause"
                                                                className="p-2 rounded-lg hover:bg-dark-300 transition text-warning"
                                                            >
                                                                <Pause className="w-4 h-4" />
                                                            </button>
                                                        ) : (
                                                            <button
                                                                onClick={() => handleAction(bot.id, bot.status === 'paused' ? 'resume' : 'start')}
                                                                title={bot.status === 'paused' ? 'Resume' : 'Start'}
                                                                className="p-2 rounded-lg hover:bg-dark-300 transition text-success"
                                                            >
                                                                <Play className="w-4 h-4" />
                                                            </button>
                                                        )}
                                                        {bot.status !== 'stopped' && bot.status !== 'created' && (
                                                            <button
                                                                onClick={() => handleAction(bot.id, 'stop')}
                                                                title="Stop"
                                                                className="p-2 rounded-lg hover:bg-dark-300 transition text-danger"
                                                            >
                                                                <Square className="w-4 h-4" />
                                                            </button>
                                                        )}
                                                        {(bot.status === 'stopped' || bot.status === 'created') && (
                                                            <button
                                                                onClick={() => deleteBot(bot.id)}
                                                                title="Delete"
                                                                className="p-2 rounded-lg hover:bg-dark-300 transition text-danger"
                                                            >
                                                                <Plus className="w-4 h-4 rotate-45" />
                                                            </button>
                                                        )}
                                                        <button
                                                            onClick={() => router.push(`/dashboard/bots/${bot.id}`)}
                                                            title="Settings"
                                                            className="p-2 rounded-lg hover:bg-dark-300 transition text-slate-400"
                                                        >
                                                            <Settings className="w-4 h-4" />
                                                        </button>

                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
