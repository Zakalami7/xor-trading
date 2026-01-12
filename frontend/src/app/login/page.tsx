'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Bot, Mail, Lock, Eye, EyeOff, ArrowRight, AlertCircle } from 'lucide-react';

export default function LoginPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [needsMfa, setNeedsMfa] = useState(false);

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        mfaCode: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password,
                    mfa_code: formData.mfaCode || undefined,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.headers.get('X-MFA-Required') === 'true') {
                    setNeedsMfa(true);
                    setIsLoading(false);
                    return;
                }
                throw new Error(data.detail || 'Login failed');
            }

            // Store tokens
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            // Redirect to dashboard
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-dark-100 flex items-center justify-center p-4">
            {/* Background */}
            <div className="fixed inset-0 -z-10">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-dark-100 to-accent-900/20" />
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md"
            >
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                            <Bot className="w-7 h-7 text-white" />
                        </div>
                        <span className="text-2xl font-bold">XOR Trading</span>
                    </Link>
                </div>

                {/* Card */}
                <div className="card">
                    <h1 className="text-2xl font-bold text-center mb-2">Welcome Back</h1>
                    <p className="text-slate-400 text-center mb-8">
                        Sign in to access your trading dashboard
                    </p>

                    {error && (
                        <div className="flex items-center gap-3 p-4 mb-6 rounded-xl bg-danger/10 border border-danger/20 text-danger">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-sm">{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Email</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="input pl-12"
                                    placeholder="you@example.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="input pl-12 pr-12"
                                    placeholder="••••••••"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {needsMfa && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                            >
                                <label className="block text-sm text-slate-400 mb-2">2FA Code</label>
                                <input
                                    type="text"
                                    value={formData.mfaCode}
                                    onChange={(e) => setFormData({ ...formData, mfaCode: e.target.value })}
                                    className="input text-center text-2xl tracking-widest font-mono"
                                    placeholder="000000"
                                    maxLength={6}
                                    autoFocus
                                />
                            </motion.div>
                        )}

                        <div className="flex items-center justify-between">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" className="w-4 h-4 rounded bg-dark-300 border-white/10" />
                                <span className="text-sm text-slate-400">Remember me</span>
                            </label>
                            <Link href="/forgot-password" className="text-sm text-primary-400 hover:text-primary-300 transition">
                                Forgot password?
                            </Link>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    Sign In
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <span className="text-slate-400">Don't have an account? </span>
                        <Link href="/register" className="text-primary-400 hover:text-primary-300 transition font-medium">
                            Create account
                        </Link>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-500 text-sm mt-8">
                    By signing in, you agree to our{' '}
                    <a href="#" className="text-slate-400 hover:text-white transition">Terms</a>
                    {' '}and{' '}
                    <a href="#" className="text-slate-400 hover:text-white transition">Privacy Policy</a>
                </p>
            </motion.div>
        </div>
    );
}
