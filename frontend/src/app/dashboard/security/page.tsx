'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Shield, Key, Smartphone, History, AlertTriangle,
    Eye, EyeOff, Check, Copy, RefreshCw, Trash2
} from 'lucide-react';
import Sidebar from '@/components/layout/Sidebar';

interface ApiKey {
    id: string;
    name: string;
    exchange: string;
    last4: string;
    createdAt: string;
    lastUsed: string | null;
}

export default function SecurityPage() {
    const [showMfaSetup, setShowMfaSetup] = useState(false);
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [showPasswordChange, setShowPasswordChange] = useState(false);

    const [apiKeys] = useState<ApiKey[]>([
        {
            id: '1',
            name: 'Main Binance',
            exchange: 'binance',
            last4: 'x4Kj',
            createdAt: '2024-01-10',
            lastUsed: '2024-01-15',
        },
        {
            id: '2',
            name: 'Bybit Testnet',
            exchange: 'bybit',
            last4: 'mN8p',
            createdAt: '2024-01-12',
            lastUsed: null,
        },
    ]);

    const [sessions] = useState([
        { id: '1', device: 'Chrome on Windows', location: 'Paris, France', current: true, lastActive: 'Now' },
        { id: '2', device: 'Safari on iPhone', location: 'Paris, France', current: false, lastActive: '2 hours ago' },
    ]);

    return (
        <div className="flex h-screen bg-dark-100">
            <Sidebar />

            <main className="flex-1 overflow-auto">
                <div className="max-w-4xl mx-auto p-8">
                    {/* Header */}
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold flex items-center gap-3">
                            <Shield className="w-8 h-8 text-primary-500" />
                            Security Settings
                        </h1>
                        <p className="text-slate-400 mt-1">Manage your account security and API keys</p>
                    </div>

                    {/* Two-Factor Authentication */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="card mb-6"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-start gap-4">
                                <div className="p-3 rounded-xl bg-primary-500/20">
                                    <Smartphone className="w-6 h-6 text-primary-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold">Two-Factor Authentication</h2>
                                    <p className="text-slate-400 text-sm mt-1">
                                        Add an extra layer of security to your account
                                    </p>
                                    {mfaEnabled && (
                                        <span className="inline-flex items-center gap-1 px-2 py-1 mt-2 text-xs font-medium text-success bg-success/10 rounded-full">
                                            <Check className="w-3 h-3" />
                                            Enabled
                                        </span>
                                    )}
                                </div>
                            </div>

                            <button
                                onClick={() => setShowMfaSetup(!showMfaSetup)}
                                className={mfaEnabled ? 'btn-danger text-sm' : 'btn-primary text-sm'}
                            >
                                {mfaEnabled ? 'Disable 2FA' : 'Enable 2FA'}
                            </button>
                        </div>

                        {showMfaSetup && !mfaEnabled && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="mt-6 p-4 bg-dark-300 rounded-xl"
                            >
                                <p className="text-sm text-slate-300 mb-4">
                                    Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                                </p>
                                <div className="w-48 h-48 bg-white rounded-xl mx-auto mb-4 flex items-center justify-center">
                                    <span className="text-dark-100 text-xs">QR Code Placeholder</span>
                                </div>
                                <div className="flex gap-2 items-center justify-center mb-4">
                                    <span className="text-xs text-slate-400">Secret:</span>
                                    <code className="text-xs bg-dark-200 px-2 py-1 rounded">JBSWY3DPEHPK3PXP</code>
                                    <button className="p-1 hover:bg-dark-200 rounded">
                                        <Copy className="w-4 h-4 text-slate-400" />
                                    </button>
                                </div>
                                <input
                                    type="text"
                                    placeholder="Enter 6-digit code"
                                    className="input text-center text-lg tracking-widest font-mono mb-4"
                                    maxLength={6}
                                />
                                <button
                                    onClick={() => setMfaEnabled(true)}
                                    className="btn-primary w-full"
                                >
                                    Verify & Enable
                                </button>
                            </motion.div>
                        )}
                    </motion.div>

                    {/* Change Password */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="card mb-6"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-start gap-4">
                                <div className="p-3 rounded-xl bg-accent-500/20">
                                    <Key className="w-6 h-6 text-accent-400" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold">Password</h2>
                                    <p className="text-slate-400 text-sm mt-1">
                                        Change your account password
                                    </p>
                                </div>
                            </div>

                            <button
                                onClick={() => setShowPasswordChange(!showPasswordChange)}
                                className="btn-secondary text-sm"
                            >
                                Change Password
                            </button>
                        </div>

                        {showPasswordChange && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="mt-6 space-y-4"
                            >
                                <div>
                                    <label className="block text-sm text-slate-400 mb-2">Current Password</label>
                                    <input type="password" className="input" placeholder="••••••••" />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-2">New Password</label>
                                    <input type="password" className="input" placeholder="••••••••" />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-2">Confirm New Password</label>
                                    <input type="password" className="input" placeholder="••••••••" />
                                </div>
                                <button className="btn-primary">Update Password</button>
                            </motion.div>
                        )}
                    </motion.div>

                    {/* API Keys */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="card mb-6"
                    >
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-warning/20">
                                    <Key className="w-6 h-6 text-warning" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold">Exchange API Keys</h2>
                                    <p className="text-slate-400 text-sm">Manage your exchange connections</p>
                                </div>
                            </div>
                            <button className="btn-primary text-sm">Add API Key</button>
                        </div>

                        <div className="space-y-3">
                            {apiKeys.map((key) => (
                                <div key={key.id} className="flex items-center justify-between p-4 bg-dark-300 rounded-xl">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-lg bg-dark-200 flex items-center justify-center text-lg">
                                            {key.exchange === 'binance' ? '🔶' : '⚫'}
                                        </div>
                                        <div>
                                            <div className="font-medium">{key.name}</div>
                                            <div className="text-sm text-slate-400">
                                                ****{key.last4} • {key.exchange.charAt(0).toUpperCase() + key.exchange.slice(1)}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="text-right text-sm text-slate-400">
                                            <div>Created {key.createdAt}</div>
                                            <div>{key.lastUsed ? `Last used ${key.lastUsed}` : 'Never used'}</div>
                                        </div>
                                        <button className="p-2 hover:bg-dark-200 rounded-lg text-danger transition">
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-4 p-4 bg-warning/10 border border-warning/20 rounded-xl flex items-start gap-3">
                            <AlertTriangle className="w-5 h-5 text-warning flex-shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <div className="font-medium text-warning">Security Notice</div>
                                <p className="text-slate-300 mt-1">
                                    Never enable withdrawal permissions on your API keys. XOR Trading only needs read and trade access.
                                </p>
                            </div>
                        </div>
                    </motion.div>

                    {/* Active Sessions */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="card"
                    >
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-3 rounded-xl bg-success/20">
                                <History className="w-6 h-6 text-success" />
                            </div>
                            <div>
                                <h2 className="text-lg font-semibold">Active Sessions</h2>
                                <p className="text-slate-400 text-sm">Devices where you're logged in</p>
                            </div>
                        </div>

                        <div className="space-y-3">
                            {sessions.map((session) => (
                                <div key={session.id} className="flex items-center justify-between p-4 bg-dark-300 rounded-xl">
                                    <div>
                                        <div className="font-medium flex items-center gap-2">
                                            {session.device}
                                            {session.current && (
                                                <span className="text-xs px-2 py-0.5 bg-success/20 text-success rounded">
                                                    Current
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-sm text-slate-400">
                                            {session.location} • {session.lastActive}
                                        </div>
                                    </div>
                                    {!session.current && (
                                        <button className="text-sm text-danger hover:underline">
                                            Revoke
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>

                        <button className="mt-4 text-sm text-danger hover:underline">
                            Sign out all other sessions
                        </button>
                    </motion.div>
                </div>
            </main>
        </div>
    );
}
