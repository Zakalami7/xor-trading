'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Bot, ArrowLeft, ArrowRight, Check,
    TrendingUp, Grid3X3, DollarSign, Zap,
    Brain, Settings, Loader2
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import { strategiesApi, exchangesApi, botsApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { useEffect } from 'react';

type Step = 'strategy' | 'exchange' | 'params' | 'review';

const strategies = [
    { id: 'grid', name: 'Grid Trading', icon: Grid3X3, description: 'Profit from price oscillation', risk: 'Medium' },
    { id: 'dca', name: 'DCA', icon: DollarSign, description: 'Dollar cost averaging', risk: 'Low' },
    { id: 'scalping', name: 'Scalping', icon: Zap, description: 'High-frequency trading', risk: 'High' },
    { id: 'trend', name: 'Trend Following', icon: TrendingUp, description: 'Follow the trend', risk: 'Medium' },
    { id: 'ai', name: 'AI Signals', icon: Brain, description: 'AI-powered signals', risk: 'Medium' },
];

const exchanges = [
    { id: 'binance', name: 'Binance', logo: '🔶' },
    { id: 'bybit', name: 'Bybit', logo: '⚫' },
    { id: 'okx', name: 'OKX', logo: '⚪' },
];

export default function NewBotPage() {
    const router = useRouter();
    const [step, setStep] = useState<Step>('strategy');
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const [availableStrategies, setAvailableStrategies] = useState<any[]>([]);
    const [availableCredentials, setAvailableCredentials] = useState<any[]>([]);

    const [formData, setFormData] = useState({
        name: '',
        strategy_id: '',
        api_credential_id: '',
        symbol: 'BTCUSDT',
        position_size: 100,
        leverage: 1,
        exchange: '', // keep for UI selection
    });

    useEffect(() => {
        const fetchMeta = async () => {
            try {
                const [stratRes, credRes] = await Promise.all([
                    strategiesApi.list(),
                    exchangesApi.listCredentials()
                ]);
                setAvailableStrategies(stratRes.data.items || stratRes.data || []);
                setAvailableCredentials(credRes.data.items || credRes.data || []);
            } catch (error) {
                console.error('Failed to fetch metadata:', error);
                toast.error('Failed to load strategies or credentials');
            } finally {
                setFetching(false);
            }
        };
        fetchMeta();
    }, []);

    const steps: Step[] = ['strategy', 'exchange', 'params', 'review'];
    const currentIndex = steps.indexOf(step);

    const next = () => {
        if (currentIndex < steps.length - 1) {
            setStep(steps[currentIndex + 1]);
        }
    };

    const back = () => {
        if (currentIndex > 0) {
            setStep(steps[currentIndex - 1]);
        }
    };

    const createBot = async () => {
        if (!formData.name || !formData.strategy_id || !formData.api_credential_id) {
            toast.error('Please fill all required fields');
            return;
        }

        try {
            setLoading(true);
            const strategy = availableStrategies.find(s => s.id === formData.strategy_id);
            const credential = availableCredentials.find(c => c.id === formData.api_credential_id);

            await botsApi.create({
                name: formData.name,
                strategy_id: formData.strategy_id,
                api_credential_id: formData.api_credential_id,
                symbol: formData.symbol,
                exchange: credential.exchange,
                position_size: formData.position_size,
                leverage: formData.leverage,
                strategy_params: strategy.default_params || {},
                market_type: 'spot'
            });

            toast.success('Bot created successfully!');
            router.push('/dashboard');
        } catch (error: any) {
            console.error('Failed to create bot:', error);
            toast.error(error.response?.data?.detail || 'Failed to create bot');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-dark-100">
            <Sidebar />

            <main className="flex-1 overflow-auto">
                <div className="max-w-3xl mx-auto p-8">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold">Create New Bot</h1>
                        <p className="text-slate-400 mt-1">Set up your trading bot in less than 60 seconds</p>
                    </div>

                    {/* Progress */}
                    <div className="flex items-center gap-2 mb-8">
                        {steps.map((s, i) => (
                            <div key={s} className="flex items-center">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${i <= currentIndex ? 'bg-primary-500 text-white' : 'bg-dark-300 text-slate-400'
                                    }`}>
                                    {i < currentIndex ? <Check className="w-4 h-4" /> : i + 1}
                                </div>
                                {i < steps.length - 1 && (
                                    <div className={`w-16 h-0.5 mx-2 ${i < currentIndex ? 'bg-primary-500' : 'bg-dark-300'
                                        }`} />
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Step Content */}
                    <motion.div
                        key={step}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="card"
                    >
                        {step === 'strategy' && (
                            <div>
                                <h2 className="text-xl font-semibold mb-6">Select Strategy</h2>
                                <div className="grid gap-4">
                                    {availableStrategies.map((s) => (
                                        <button
                                            key={s.id}
                                            onClick={() => setFormData({ ...formData, strategy_id: s.id })}
                                            className={`p-4 rounded-xl border transition-all text-left flex items-center gap-4 ${formData.strategy_id === s.id
                                                ? 'border-primary-500 bg-primary-500/10'
                                                : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                                                }`}
                                        >
                                            <div className="w-12 h-12 rounded-xl bg-dark-300 flex items-center justify-center">
                                                <Bot className="w-6 h-6 text-primary-400" />
                                            </div>
                                            <div className="flex-1">
                                                <div className="font-medium">{s.name}</div>
                                                <div className="text-sm text-slate-400">{s.description}</div>
                                            </div>
                                            <div className={`text-sm px-3 py-1 rounded-full ${s.risk_level === 'low' ? 'bg-success/20 text-success' :
                                                s.risk_level === 'high' ? 'bg-danger/20 text-danger' :
                                                    'bg-warning/20 text-warning'
                                                }`}>
                                                {s.risk_level?.toUpperCase() || 'MEDIUM'} Risk
                                            </div>
                                        </button>
                                    ))}
                                    {availableStrategies.length === 0 && !fetching && (
                                        <div className="text-center py-8 text-slate-400 border border-dashed border-white/10 rounded-xl">
                                            No strategies available.
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {step === 'exchange' && (
                            <div>
                                <h2 className="text-xl font-semibold mb-6">Select Exchange</h2>
                                <div className="grid grid-cols-1 gap-4 mb-6">
                                    {availableCredentials.map((c) => (
                                        <button
                                            key={c.id}
                                            onClick={() => setFormData({ ...formData, api_credential_id: c.id, exchange: c.exchange })}
                                            className={`p-4 rounded-xl border text-left transition-all flex items-center gap-4 ${formData.api_credential_id === c.id
                                                ? 'border-primary-500 bg-primary-500/10'
                                                : 'border-white/10 hover:border-white/20'
                                                }`}
                                        >
                                            <div className="text-2xl">{c.exchange === 'binance' ? '🔶' : '⚫'}</div>
                                            <div className="flex-1">
                                                <div className="font-medium">{c.name}</div>
                                                <div className="text-xs text-slate-400 capitalize">{c.exchange} {c.is_testnet ? '(Testnet)' : '(Live)'}</div>
                                            </div>
                                            {formData.api_credential_id === c.id && <Check className="w-5 h-5 text-primary-500" />}
                                        </button>
                                    ))}
                                    {availableCredentials.length === 0 && !fetching && (
                                        <div className="text-center py-8 text-slate-400 border border-dashed border-white/10 rounded-xl">
                                            No API credentials found. Please add one in settings.
                                        </div>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-400 mb-2">Trading Pair</label>
                                    <select
                                        value={formData.symbol}
                                        onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                                        className="input"
                                    >
                                        <option value="BTCUSDT">BTC/USDT</option>
                                        <option value="ETHUSDT">ETH/USDT</option>
                                        <option value="SOLUSDT">SOL/USDT</option>
                                        <option value="BNBUSDT">BNB/USDT</option>
                                        <option value="PAXGUSDT">PAXG/USDT</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {step === 'params' && (
                            <div>
                                <h2 className="text-xl font-semibold mb-6">Configure Parameters</h2>

                                <div className="space-y-6">
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-2">Bot Name</label>
                                        <input
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            placeholder="My Trading Bot"
                                            className="input"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm text-slate-400 mb-2">Position Size (USDT)</label>
                                        <input
                                            type="number"
                                            value={formData.position_size}
                                            onChange={(e) => setFormData({ ...formData, position_size: +e.target.value })}
                                            className="input"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm text-slate-400 mb-2">Leverage</label>
                                        <input
                                            type="range"
                                            min="1"
                                            max="20"
                                            value={formData.leverage}
                                            onChange={(e) => setFormData({ ...formData, leverage: +e.target.value })}
                                            className="w-full"
                                        />
                                        <div className="text-center font-mono mt-2">{formData.leverage}x</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {step === 'review' && (
                            <div>
                                <h2 className="text-xl font-semibold mb-6">Review & Create</h2>

                                <div className="space-y-4 mb-6">
                                    <div className="flex justify-between py-3 border-b border-white/5">
                                        <span className="text-slate-400">Strategy</span>
                                        <span className="font-medium">{availableStrategies.find(s => s.id === formData.strategy_id)?.name}</span>
                                    </div>
                                    <div className="flex justify-between py-3 border-b border-white/5">
                                        <span className="text-slate-400">Exchange</span>
                                        <span className="font-medium uppercase">{formData.exchange}</span>
                                    </div>
                                    <div className="flex justify-between py-3 border-b border-white/5">
                                        <span className="text-slate-400">Symbol</span>
                                        <span className="font-medium font-mono">{formData.symbol}</span>
                                    </div>
                                    <div className="flex justify-between py-3 border-b border-white/5">
                                        <span className="text-slate-400">Position Size</span>
                                        <span className="font-medium">{formData.position_size} USDT</span>
                                    </div>
                                    <div className="flex justify-between py-3">
                                        <span className="text-slate-400">Leverage</span>
                                        <span className="font-medium">{formData.leverage}x</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </motion.div>

                    {/* Navigation */}
                    <div className="flex justify-between mt-6">
                        <button
                            onClick={back}
                            disabled={currentIndex === 0}
                            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
                        >
                            <ArrowLeft className="w-5 h-5" />
                            Back
                        </button>

                        {step === 'review' ? (
                            <button
                                onClick={createBot}
                                disabled={loading}
                                className="btn-primary flex items-center gap-2 disabled:opacity-50"
                            >
                                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Check className="w-5 h-5" />}
                                {loading ? 'Creating...' : 'Create Bot'}
                            </button>
                        ) : (
                            <button
                                onClick={next}
                                disabled={(!formData.strategy_id && step === 'strategy') || (!formData.api_credential_id && step === 'exchange')}
                                className="btn-primary flex items-center gap-2 disabled:opacity-50"
                            >
                                Continue
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
