'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Bot, TrendingUp, Shield, Zap, BarChart3, ArrowRight } from 'lucide-react';

export default function HomePage() {
    return (
        <div className="min-h-screen bg-dark-100 overflow-hidden">
            {/* Animated background */}
            <div className="fixed inset-0 -z-10">
                <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-dark-100 to-accent-900/20" />
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl animate-pulse-slow" />
            </div>

            {/* Header */}
            <header className="fixed top-0 w-full z-50 glass">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-xl font-bold">XOR Trading</span>
                    </div>

                    <nav className="hidden md:flex items-center gap-8">
                        <a href="#features" className="text-slate-400 hover:text-white transition">Features</a>
                        <a href="#strategies" className="text-slate-400 hover:text-white transition">Strategies</a>
                        <a href="#pricing" className="text-slate-400 hover:text-white transition">Pricing</a>
                    </nav>

                    <div className="flex items-center gap-4">
                        <Link href="/login" className="text-slate-400 hover:text-white transition">
                            Login
                        </Link>
                        <Link href="/register" className="btn-primary text-sm">
                            Get Started
                        </Link>
                    </div>
                </div>
            </header>

            {/* Hero */}
            <section className="pt-32 pb-20 px-6">
                <div className="max-w-7xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8">
                            <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
                            <span className="text-sm text-slate-300">Live trading available</span>
                        </div>

                        <h1 className="text-5xl md:text-7xl font-bold mb-6">
                            Trade Smarter with
                            <br />
                            <span className="gradient-text">AI-Powered Bots</span>
                        </h1>

                        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
                            Institutional-grade algorithmic trading for cryptocurrency markets.
                            Lower latency, smarter execution, better returns.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Link href="/dashboard" className="btn-primary flex items-center gap-2">
                                Launch Dashboard
                                <ArrowRight className="w-5 h-5" />
                            </Link>
                            <Link href="#demo" className="btn-secondary">
                                Watch Demo
                            </Link>
                        </div>
                    </motion.div>

                    {/* Stats */}
                    <motion.div
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20"
                    >
                        {[
                            { value: '<10ms', label: 'Execution Speed' },
                            { value: '99.9%', label: 'Uptime' },
                            { value: '$50M+', label: 'Volume Traded' },
                            { value: '10K+', label: 'Active Bots' },
                        ].map((stat, i) => (
                            <div key={i} className="card text-center">
                                <div className="text-3xl font-bold gradient-text">{stat.value}</div>
                                <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* Features */}
            <section id="features" className="py-20 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-4xl font-bold mb-4">Why Choose XOR?</h2>
                        <p className="text-slate-400 max-w-xl mx-auto">
                            Built for professional traders who demand the best performance.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: Zap,
                                title: 'Ultra-Low Latency',
                                description: 'Sub-10ms execution with our Rust-powered engine. Faster than any competitor.',
                            },
                            {
                                icon: Shield,
                                title: 'Bank-Grade Security',
                                description: 'Zero-trust architecture with encrypted API keys. No withdrawal permissions.',
                            },
                            {
                                icon: TrendingUp,
                                title: 'Smart Strategies',
                                description: 'Grid, DCA, Scalping, and AI-powered strategies ready to deploy.',
                            },
                            {
                                icon: BarChart3,
                                title: 'Advanced Analytics',
                                description: 'Real-time PnL, drawdown tracking, and performance metrics.',
                            },
                            {
                                icon: Bot,
                                title: 'No-Code Builder',
                                description: 'Create and deploy bots in under 60 seconds. No coding required.',
                            },
                            {
                                icon: Shield,
                                title: 'Risk Management',
                                description: 'Institutional-grade risk controls with automatic kill switch.',
                            },
                        ].map((feature, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: i * 0.1 }}
                                viewport={{ once: true }}
                                className="card glass-hover group cursor-pointer"
                            >
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                                    <feature.icon className="w-6 h-6 text-primary-400" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                <p className="text-slate-400">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="py-20 px-6">
                <div className="max-w-4xl mx-auto">
                    <div className="card bg-gradient-to-r from-primary-600/20 to-accent-600/20 text-center p-12">
                        <h2 className="text-4xl font-bold mb-4">Ready to Start Trading?</h2>
                        <p className="text-slate-300 mb-8">
                            Join thousands of traders already using XOR to automate their strategies.
                        </p>
                        <Link href="/register" className="btn-primary inline-flex items-center gap-2">
                            Create Free Account
                            <ArrowRight className="w-5 h-5" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-6 border-t border-white/5">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <Bot className="w-6 h-6 text-primary-500" />
                        <span className="font-semibold">XOR Trading</span>
                    </div>
                    <div className="text-slate-400 text-sm">
                        © 2024 XOR Trading Platform. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
}
