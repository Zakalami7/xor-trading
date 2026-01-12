'use client';

import { useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';

interface TradingChartProps {
    symbol: string;
    data?: CandlestickData[];
    height?: number;
    showVolume?: boolean;
}

const defaultData: CandlestickData[] = [
    { time: '2024-01-01', open: 42000, high: 42500, low: 41800, close: 42300 },
    { time: '2024-01-02', open: 42300, high: 43000, low: 42100, close: 42800 },
    { time: '2024-01-03', open: 42800, high: 43200, low: 42600, close: 43100 },
    { time: '2024-01-04', open: 43100, high: 43500, low: 42900, close: 43400 },
    { time: '2024-01-05', open: 43400, high: 44000, low: 43200, close: 43800 },
    { time: '2024-01-06', open: 43800, high: 44200, low: 43500, close: 43700 },
    { time: '2024-01-07', open: 43700, high: 44500, low: 43600, close: 44200 },
    { time: '2024-01-08', open: 44200, high: 44800, low: 44000, close: 44600 },
    { time: '2024-01-09', open: 44600, high: 45000, low: 44300, close: 44800 },
    { time: '2024-01-10', open: 44800, high: 45200, low: 44500, close: 45000 },
];

export default function TradingChart({
    symbol,
    data = defaultData,
    height = 400,
    showVolume = true,
}: TradingChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            crosshair: {
                vertLine: {
                    color: '#6366f1',
                    width: 1,
                    style: 2,
                },
                horzLine: {
                    color: '#6366f1',
                    width: 1,
                    style: 2,
                },
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
        });

        chartRef.current = chart;

        // Add candlestick series
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderUpColor: '#10b981',
            borderDownColor: '#ef4444',
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        candlestickSeriesRef.current = candlestickSeries;
        candlestickSeries.setData(data);

        // Fit content
        chart.timeScale().fitContent();

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
            }
        };
    }, [height, data]);

    // Update data when it changes
    useEffect(() => {
        if (candlestickSeriesRef.current && data.length > 0) {
            candlestickSeriesRef.current.setData(data);
            chartRef.current?.timeScale().fitContent();
        }
    }, [data]);

    return (
        <div className="relative">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h3 className="text-lg font-semibold">{symbol}</h3>
                    <p className="text-sm text-slate-400">Price Chart</p>
                </div>
                <div className="flex gap-2">
                    {['1m', '5m', '15m', '1h', '4h', '1d'].map((tf) => (
                        <button
                            key={tf}
                            className={`px-3 py-1 text-sm rounded-lg transition ${tf === '1h'
                                    ? 'bg-primary-500 text-white'
                                    : 'bg-dark-300 text-slate-400 hover:bg-dark-400'
                                }`}
                        >
                            {tf}
                        </button>
                    ))}
                </div>
            </div>

            {/* Chart */}
            <div
                ref={chartContainerRef}
                className="rounded-xl overflow-hidden"
                style={{ height }}
            />

            {/* Price info */}
            <div className="flex items-center gap-6 mt-4 text-sm">
                <div>
                    <span className="text-slate-400">O:</span>
                    <span className="ml-1 font-mono">{data[data.length - 1]?.open}</span>
                </div>
                <div>
                    <span className="text-slate-400">H:</span>
                    <span className="ml-1 font-mono text-success">{data[data.length - 1]?.high}</span>
                </div>
                <div>
                    <span className="text-slate-400">L:</span>
                    <span className="ml-1 font-mono text-danger">{data[data.length - 1]?.low}</span>
                </div>
                <div>
                    <span className="text-slate-400">C:</span>
                    <span className="ml-1 font-mono">{data[data.length - 1]?.close}</span>
                </div>
            </div>
        </div>
    );
}
