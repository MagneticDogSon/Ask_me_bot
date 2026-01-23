"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface OptionButtonProps {
    label: string;
    onClick: () => void;
    selected: boolean;
    disabled: boolean;
    index: number;
}

export function OptionButton({ label, onClick, selected, disabled, index }: OptionButtonProps) {
    return (
        <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4, type: "spring" }}
            whileHover={!disabled ? { scale: 1.02, paddingLeft: "1.5rem" } : {}}
            whileTap={!disabled ? { scale: 0.98 } : {}}
            onClick={onClick}
            disabled={disabled}
            className={cn(
                "group relative w-full text-left p-4 md:p-6 rounded-xl md:rounded-2xl text-base md:text-xl font-medium transition-all duration-300 border overflow-hidden",
                selected
                    ? "bg-indigo-500/20 border-indigo-400 text-white shadow-[0_0_30px_rgba(99,102,241,0.3)]"
                    : "glass-panel border-white/10 text-slate-200 hover:bg-white/5"
            )}
        >
            {/* Background Gradient Slide */}
            <div className={cn(
                "absolute inset-0 bg-gradient-to-r from-indigo-600 to-purple-600 transition-transform duration-500 ease-out",
                selected ? "translate-x-0 opacity-100" : "-translate-x-full opacity-0"
            )} />

            {/* Content */}
            <div className="relative z-10 flex items-center justify-between">
                <span className="tracking-wide">{label}</span>

                {/* Selection Indicator */}
                <div className={cn(
                    "h-6 w-6 rounded-full border-2 flex items-center justify-center transition-all duration-300",
                    selected ? "border-white bg-white text-indigo-600 scale-100" : "border-white/30 scale-90 opacity-50 group-hover:border-white/60"
                )}>
                    {selected && (
                        <motion.svg
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-3.5 h-3.5"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <polyline points="20 6 9 17 4 12" />
                        </motion.svg>
                    )}
                </div>
            </div>
        </motion.button>
    );
}
