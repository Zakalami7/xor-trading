import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'XOR Trading Platform',
    description: 'Professional algorithmic trading platform for cryptocurrency markets',
    keywords: ['trading', 'crypto', 'bot', 'algorithmic', 'bitcoin'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="dark">
            <body className="min-h-screen">
                {children}
            </body>
        </html>
    );
}
