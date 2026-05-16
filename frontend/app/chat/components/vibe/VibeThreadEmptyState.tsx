'use client'

import { motion } from 'framer-motion'
import { MapPin } from 'lucide-react'

/** Empty thread before the first message (e.g. new topic). Compact, on-brand panel with geometric accents. */
export function VibeThreadEmptyState() {
    return (
        <div className="flex min-w-0 flex-1 flex-col items-center justify-center px-1 py-2">
            <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                className="relative w-full max-w-[17.5rem] overflow-hidden rounded-2xl border border-white/[0.09] bg-gradient-to-b from-zinc-900/55 to-zinc-950/65 px-4 pb-5 pt-4 shadow-[0_0_0_1px_rgba(255,255,255,0.03)_inset,0_18px_50px_-28px_rgba(0,0,0,0.85)] backdrop-blur-md sm:max-w-[18.5rem]"
            >
                {/* Geometric line art */}
                <svg
                    className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
                    viewBox="0 0 288 200"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    preserveAspectRatio="xMidYMid slice"
                    aria-hidden
                >
                    <defs>
                        <linearGradient id="vibe-thread-geo-a" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stopColor="rgb(167 139 250)" stopOpacity="0.55" />
                            <stop offset="55%" stopColor="rgb(45 212 191)" stopOpacity="0.35" />
                            <stop offset="100%" stopColor="rgb(94 234 212)" stopOpacity="0.2" />
                        </linearGradient>
                        <linearGradient id="vibe-thread-geo-b" x1="1" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="rgb(45 212 191)" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="rgb(139 92 246)" stopOpacity="0.25" />
                        </linearGradient>
                    </defs>
                    {/* Corner brackets */}
                    <path
                        d="M 24 52 V 28 H 52"
                        stroke="url(#vibe-thread-geo-a)"
                        strokeWidth="1.15"
                        strokeLinecap="round"
                    />
                    <path
                        d="M 264 52 V 28 H 236"
                        stroke="url(#vibe-thread-geo-a)"
                        strokeWidth="1.15"
                        strokeLinecap="round"
                    />
                    <path
                        d="M 24 148 V 172 H 52"
                        stroke="url(#vibe-thread-geo-b)"
                        strokeWidth="1.15"
                        strokeLinecap="round"
                    />
                    <path
                        d="M 264 148 V 172 H 236"
                        stroke="url(#vibe-thread-geo-b)"
                        strokeWidth="1.15"
                        strokeLinecap="round"
                    />
                    {/* Isometric shard */}
                    <path
                        d="M 88 156 L 144 124 L 200 156 L 144 188 Z"
                        stroke="url(#vibe-thread-geo-a)"
                        strokeWidth="0.9"
                        strokeLinejoin="round"
                        opacity="0.45"
                    />
                    <path d="M 144 124 L 144 188" stroke="url(#vibe-thread-geo-b)" strokeWidth="0.75" opacity="0.35" />
                    {/* Radiating hub */}
                    <circle cx="144" cy="78" r="4" fill="rgb(167 139 250)" fillOpacity="0.35" />
                    <circle cx="144" cy="78" r="1.5" fill="rgb(226 232 240)" fillOpacity="0.5" />
                    <path d="M 144 34 V 70" stroke="url(#vibe-thread-geo-a)" strokeWidth="0.85" strokeLinecap="round" opacity="0.5" />
                    <path d="M 144 86 V 112" stroke="url(#vibe-thread-geo-a)" strokeWidth="0.85" strokeLinecap="round" opacity="0.45" />
                    <path d="M 92 78 H 136" stroke="url(#vibe-thread-geo-b)" strokeWidth="0.85" strokeLinecap="round" opacity="0.4" />
                    <path d="M152 78 H 196" stroke="url(#vibe-thread-geo-b)" strokeWidth="0.85" strokeLinecap="round" opacity="0.4" />
                    <path d="M 118 56 L 136 70" stroke="url(#vibe-thread-geo-a)" strokeWidth="0.7" strokeLinecap="round" opacity="0.35" />
                    <path d="M 170 56 L 152 70" stroke="url(#vibe-thread-geo-a)" strokeWidth="0.7" strokeLinecap="round" opacity="0.35" />
                    <path d="M 118 100 L 136 86" stroke="url(#vibe-thread-geo-b)" strokeWidth="0.7" strokeLinecap="round" opacity="0.35" />
                    <path d="M 170 100 L 152 86" stroke="url(#vibe-thread-geo-b)" strokeWidth="0.7" strokeLinecap="round" opacity="0.35" />
                    {/* Diagonal scan */}
                    <path
                        d="M 12 188 L 98 12"
                        stroke="rgb(148 163 184)"
                        strokeOpacity="0.12"
                        strokeWidth="0.6"
                        strokeDasharray="4 7"
                    />
                    <path
                        d="M 190 12 L 276 188"
                        stroke="rgb(148 163 184)"
                        strokeOpacity="0.1"
                        strokeWidth="0.6"
                        strokeDasharray="5 8"
                    />
                </svg>

                <div className="relative z-[1] flex flex-col items-center text-center">
                    <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-2xl border border-violet-400/25 bg-gradient-to-br from-violet-500/25 to-teal-500/20 shadow-[0_8px_24px_-12px_rgba(139,92,246,0.5)]">
                        <MapPin className="h-[18px] w-[18px] text-teal-200/90" strokeWidth={2} />
                    </div>
                    <h2 className="text-[13px] font-semibold tracking-tight text-zinc-100 sm:text-sm">Start with a topic</h2>
                    <p className="mt-1.5 max-w-[13.5rem] text-[11px] leading-snug text-zinc-500 sm:text-xs">
                        Your thread starts here. Describe anything you want to learn below—lessons, path, and practice unlock from
                        your first message.
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                        <span className="h-px w-6 bg-gradient-to-r from-transparent to-teal-400/40" />
                        <span className="text-[10px] font-medium uppercase tracking-[0.2em] text-zinc-600">Ready when you are</span>
                        <span className="h-px w-6 bg-gradient-to-l from-transparent to-violet-400/40" />
                    </div>
                </div>
            </motion.div>
        </div>
    )
}
