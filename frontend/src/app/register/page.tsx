'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Bot, Mail, Lock, User, Eye, EyeOff, ArrowRight, AlertCircle, Check } from 'lucide-react';

export default function RegisterPage() {
    const router = useRouter();
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const [formData, setFormData] = useState({
        email: '',
        username: '',
        fullName: '',
        password: '',
        confirmPassword: '',
        acceptTerms: false,
    });

    const passwordRequirements = [
        { met: formData.password.length >= 8, text: 'At least 8 characters' },
        { met: /[A-Z]/.test(formData.password), text: 'One uppercase letter' },
        { met: /[a-z]/.test(formData.password), text: 'One lowercase letter' },
        { met: /\d/.test(formData.password), text: 'One number' },
    ];

    const isPasswordValid = passwordRequirements.every(r => r.met);
    const passwordsMatch = formData.password === formData.confirmPassword && formData.confirmPassword.length > 0;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!isPasswordValid) {
            setError('Password does not meet requirements');
            return;
        }

        if (!passwordsMatch) {
            setError('Passwords do not match');
            return;
        }

        if (!formData.acceptTerms) {
            setError('Please accept the terms and conditions');
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.email,
                    username: formData.username,
                    full_name: formData.fullName,
                    password: formData.password,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Registration failed');
            }

            // Redirect to login
            router.push('/login?registered=true');
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-dark-100 flex items-center justify-center p-4 py-12">
            {/* Background */}
            <div className="fixed inset-0 -z-10">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-dark-100 to-accent-900/20" />
                <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
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
                    <h1 className="text-2xl font-bold text-center mb-2">Create Account</h1>
                    <p className="text-slate-400 text-center mb-8">
                        Start your algorithmic trading journey
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

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Username</label>
                                <input
                                    type="text"
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                                    className="input"
                                    placeholder="johndoe"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-slate-400 mb-2">Full Name</label>
                                <input
                                    type="text"
                                    value={formData.fullName}
                                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                                    className="input"
                                    placeholder="John Doe"
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

                            {/* Password requirements */}
                            <div className="mt-3 grid grid-cols-2 gap-2">
                                {passwordRequirements.map((req, i) => (
                                    <div key={i} className={`flex items-center gap-2 text-xs ${req.met ? 'text-success' : 'text-slate-500'}`}>
                                        <Check className={`w-3 h-3 ${req.met ? 'opacity-100' : 'opacity-30'}`} />
                                        {req.text}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Confirm Password</label>
                            <div className="relative">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="password"
                                    value={formData.confirmPassword}
                                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                                    className={`input pl-12 ${formData.confirmPassword && (passwordsMatch ? 'border-success' : 'border-danger')
                                        }`}
                                    placeholder="••••••••"
                                    required
                                />
                                {formData.confirmPassword && (
                                    <div className={`absolute right-4 top-1/2 -translate-y-1/2 ${passwordsMatch ? 'text-success' : 'text-danger'}`}>
                                        {passwordsMatch ? <Check className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                                    </div>
                                )}
                            </div>
                        </div>

                        <label className="flex items-start gap-3 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={formData.acceptTerms}
                                onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
                                className="w-5 h-5 mt-0.5 rounded bg-dark-300 border-white/10"
                            />
                            <span className="text-sm text-slate-400">
                                I agree to the{' '}
                                <a href="#" className="text-primary-400 hover:underline">Terms of Service</a>
                                {' '}and{' '}
                                <a href="#" className="text-primary-400 hover:underline">Privacy Policy</a>
                            </span>
                        </label>

                        <button
                            type="submit"
                            disabled={isLoading || !isPasswordValid || !passwordsMatch || !formData.acceptTerms}
                            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    Create Account
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <span className="text-slate-400">Already have an account? </span>
                        <Link href="/login" className="text-primary-400 hover:text-primary-300 transition font-medium">
                            Sign in
                        </Link>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
