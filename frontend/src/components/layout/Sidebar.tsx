'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Bot, LayoutDashboard, Wallet, Activity, Settings,
    BarChart3, History, Shield, LogOut, PlusCircle
} from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Bots', href: '/dashboard/bots', icon: Bot },
    { name: 'Positions', href: '/dashboard/positions', icon: Activity },
    { name: 'Orders', href: '/dashboard/orders', icon: History },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    { name: 'Wallet', href: '/dashboard/wallet', icon: Wallet },
];

const bottomNavigation = [
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
    { name: 'Security', href: '/dashboard/security', icon: Shield },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="w-64 h-screen bg-dark-200 border-r border-white/5 flex flex-col">
            {/* Logo */}
            <div className="p-6">
                <Link href="/" className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                        <Bot className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-xl font-bold">XOR Trading</span>
                </Link>
            </div>

            {/* Create Bot Button */}
            <div className="px-4 mb-4">
                <Link href="/dashboard/bots/new" className="btn-primary w-full flex items-center justify-center gap-2 text-sm">
                    <PlusCircle className="w-5 h-5" />
                    Create Bot
                </Link>
            </div>

            {/* Main Navigation */}
            <nav className="flex-1 px-4">
                <div className="space-y-1">
                    {navigation.map((item) => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={clsx(
                                    'sidebar-link',
                                    isActive && 'active'
                                )}
                            >
                                <item.icon className="w-5 h-5" />
                                {item.name}
                            </Link>
                        );
                    })}
                </div>
            </nav>

            {/* Bottom Navigation */}
            <div className="p-4 border-t border-white/5">
                <div className="space-y-1 mb-4">
                    {bottomNavigation.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={clsx(
                                    'sidebar-link',
                                    isActive && 'active'
                                )}
                            >
                                <item.icon className="w-5 h-5" />
                                {item.name}
                            </Link>
                        );
                    })}
                </div>

                <button className="sidebar-link w-full text-danger hover:bg-danger/10">
                    <LogOut className="w-5 h-5" />
                    Logout
                </button>
            </div>

            {/* User Info */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-accent-500" />
                    <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">John Trader</div>
                        <div className="text-xs text-slate-400 truncate">john@example.com</div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
