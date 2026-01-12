import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
    id: string;
    email: string;
    username: string;
    full_name?: string;
    is_active: boolean;
    mfa_enabled: boolean;
}

interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isAuthenticated: boolean;

    setAuth: (user: User, accessToken: string, refreshToken: string) => void;
    setUser: (user: User) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            setAuth: (user, accessToken, refreshToken) => {
                localStorage.setItem('access_token', accessToken);
                localStorage.setItem('refresh_token', refreshToken);
                set({
                    user,
                    accessToken,
                    refreshToken,
                    isAuthenticated: true,
                });
            },

            setUser: (user) => set({ user }),

            logout: () => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                set({
                    user: null,
                    accessToken: null,
                    refreshToken: null,
                    isAuthenticated: false,
                });
            },
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user,
                isAuthenticated: state.isAuthenticated,
            }),
        }
    )
);

// Bot Store
interface Bot {
    id: string;
    name: string;
    symbol: string;
    status: string;
    strategy: string;
    pnl: number;
    pnlPercent: number;
}

interface BotState {
    bots: Bot[];
    selectedBot: Bot | null;
    isLoading: boolean;

    setBots: (bots: Bot[]) => void;
    selectBot: (bot: Bot | null) => void;
    updateBot: (id: string, updates: Partial<Bot>) => void;
    setLoading: (loading: boolean) => void;
}

export const useBotStore = create<BotState>((set) => ({
    bots: [],
    selectedBot: null,
    isLoading: false,

    setBots: (bots) => set({ bots }),
    selectBot: (bot) => set({ selectedBot: bot }),
    updateBot: (id, updates) =>
        set((state) => ({
            bots: state.bots.map((bot) =>
                bot.id === id ? { ...bot, ...updates } : bot
            ),
        })),
    setLoading: (loading) => set({ isLoading: loading }),
}));

// Dashboard Store
interface DashboardStats {
    totalPnl: number;
    totalPnlPercent: number;
    activeBots: number;
    openPositions: number;
    trades24h: number;
    winRate: number;
}

interface DashboardState {
    stats: DashboardStats | null;
    isLoading: boolean;
    lastUpdated: Date | null;

    setStats: (stats: DashboardStats) => void;
    setLoading: (loading: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
    stats: null,
    isLoading: false,
    lastUpdated: null,

    setStats: (stats) => set({ stats, lastUpdated: new Date() }),
    setLoading: (loading) => set({ isLoading: loading }),
}));
