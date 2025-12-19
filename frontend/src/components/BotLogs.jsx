import React, { useEffect, useRef } from 'react';
import { Terminal, Clock } from 'lucide-react';

/**
 * BotLogs - Displays real-time logs in a terminal window.
 * Supports multiple instances with selection or merged view (simplified to basic list for now).
 * 
 * Props:
 * - logs: Array of log strings ["12:00:01 - Log message", ...]
 * - isRunning: boolean
 */
export default function BotLogs({ logs = [], isRunning }) {
    const scrollRef = useRef(null);

    // Auto-scroll to bottom on new logs
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="glass rounded-2xl overflow-hidden shadow-lg shadow-purple-900/10 border border-purple-500/10 mt-6">
            <div className="p-4 border-b border-white/5 flex items-center justify-between bg-black/40">
                <div className="flex items-center gap-2">
                    <Terminal size={18} className="text-primary" />
                    <h3 className="text-sm font-medium text-foreground">Live Execution Logs</h3>
                    {isRunning && (
                        <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-medium uppercase tracking-wider animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                            Live
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock size={12} />
                    <span>Server Time (UTC)</span>
                </div>
            </div>

            <div
                ref={scrollRef}
                className="h-[300px] overflow-y-auto p-4 bg-black/60 font-mono text-xs space-y-1 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
            >
                {logs && logs.length > 0 ? (
                    logs.map((log, index) => {
                        // Highlight key phases
                        let colorClass = "text-muted-foreground";
                        if (log.includes("Fetching Market Data")) colorClass = "text-blue-400";
                        else if (log.includes("Signal Generated")) colorClass = "text-purple-400";
                        else if (log.includes("Running Risk Checks")) colorClass = "text-orange-400";
                        else if (log.includes("Executing Order")) colorClass = "text-green-400 font-bold";
                        else if (log.includes("ERROR")) colorClass = "text-red-400 font-bold";
                        else if (log.includes("Warning")) colorClass = "text-yellow-400";

                        return (
                            <div key={index} className="break-all hover:bg-white/5 px-2 py-0.5 rounded transition-colors flex gap-2">
                                <span className="opacity-30 select-none min-w-[20px] text-right">{index + 1}</span>
                                <span className={colorClass}>{log}</span>
                            </div>
                        );
                    })
                ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground/30 italic">
                        No logs available. Start a bot to see live execution.
                    </div>
                )}
            </div>
        </div>
    );
}
