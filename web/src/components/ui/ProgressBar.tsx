"use client";

import { motion } from "framer-motion";

interface ProgressBarProps {
    current: number;
    total: number;
}

export function ProgressBar({ current, total }: ProgressBarProps) {
    const progress = ((current + 1) / total) * 100;

    return (
        <div className="w-full space-y-2">
            <div className="flex justify-between text-xs font-medium uppercase tracking-widest text-slate-400">
                <span>Прогресс</span>
                <span>{Math.round(progress)}%</span>
            </div>
            <div className="relative h-2 w-full bg-slate-800/50 rounded-full overflow-hidden backdrop-blur-sm border border-white/5">
                <motion.div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%]"
                    initial={{ width: 0 }}
                    animate={{
                        width: `${progress}%`,
                        backgroundPosition: ["0% 0%", "100% 0%"]
                    }}
                    transition={{
                        width: { duration: 0.6, ease: "circOut" },
                        backgroundPosition: { duration: 2, repeat: Infinity, ease: "linear" }
                    }}
                />
                {/* Glow */}
                <motion.div
                    className="absolute top-0 h-full w-4 bg-white/50 blur-[4px]"
                    style={{ left: `${progress}%`, x: "-100%" }}
                />
            </div>
        </div>
    );
}
