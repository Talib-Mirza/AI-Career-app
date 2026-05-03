'use client'

import { AnimatePresence, motion } from 'framer-motion'
import { PlusCircle, Sparkles, X } from 'lucide-react'

import { ProjectSidebar } from '@/app/chat/components/ProjectSidebar'
import type { AgentProjectSummary } from '@/types'

interface VibeProjectsDrawerProps {
    open: boolean
    onClose: () => void
    projects: AgentProjectSummary[]
    selectedProjectId: string | null
    busy: boolean
    onSelect: (id: string) => void
    onDelete: (id: string) => void
    onStartNew: () => void
    profileLevel: number
    profileXp: number
}

export function VibeProjectsDrawer({
    open,
    onClose,
    projects,
    selectedProjectId,
    busy,
    onSelect,
    onDelete,
    onStartNew,
    profileLevel,
    profileXp,
}: VibeProjectsDrawerProps) {
    return (
        <AnimatePresence>
            {open && (
                <>
                    <motion.button
                        type="button"
                        aria-label="Close drawer"
                        className="fixed inset-0 z-[60] bg-neutral-950/55 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />
                    <motion.aside
                        role="dialog"
                        aria-modal="true"
                        aria-label="Projects"
                        className="dark fixed inset-y-0 left-0 z-[70] flex w-[min(100%,20rem)] flex-col overflow-hidden border-r border-neutral-800 bg-neutral-900 shadow-2xl shadow-black/40"
                        initial={{ x: '-100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '-100%' }}
                        transition={{ type: 'spring', damping: 28, stiffness: 320 }}
                    >
                        <div
                            className="pointer-events-none absolute inset-0"
                            aria-hidden
                            style={{
                                background:
                                    'linear-gradient(165deg, rgb(23 23 23) 0%, rgb(17 24 39) 48%, rgb(12 10 24) 100%), radial-gradient(120% 80% at 0% 0%, rgba(59, 130, 246, 0.2) 0%, transparent 55%), radial-gradient(90% 60% at 100% 100%, rgba(147, 51, 234, 0.16) 0%, transparent 50%)',
                            }}
                        />
                        <div className="relative flex items-center justify-between border-b border-neutral-800 px-4 py-4">
                            <div className="flex items-center gap-2.5">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 shadow-sm">
                                    <Sparkles className="h-3.5 w-3.5 text-white" />
                                </div>
                                <div>
                                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-neutral-500">Workspace</p>
                                    <p className="text-sm font-semibold text-neutral-50">Projects</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={onClose}
                                className="rounded-full p-2 text-neutral-500 transition hover:bg-neutral-800 hover:text-neutral-200"
                                aria-label="Close"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                        <div className="relative border-b border-neutral-800 px-4 py-3">
                            <p className="text-[11px] text-neutral-500">
                                Level <span className="font-semibold text-blue-300">{profileLevel}</span>
                                <span className="mx-1.5 text-neutral-600">·</span>
                                <span className="text-neutral-300">{profileXp} XP</span>
                            </p>
                        </div>
                        <div className="relative px-3 py-3">
                            <button
                                type="button"
                                onClick={onStartNew}
                                disabled={busy}
                                className="flex w-full items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-3 py-2.5 text-sm font-semibold text-white shadow-md transition hover:from-blue-500 hover:to-purple-500 disabled:opacity-50"
                            >
                                <PlusCircle className="h-4 w-4" />
                                New project
                            </button>
                        </div>
                        <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-6">
                            <ProjectSidebar
                                projects={projects}
                                selectedProjectId={selectedProjectId}
                                busy={busy}
                                onSelect={onSelect}
                                onDelete={onDelete}
                                onStartNew={onStartNew}
                                compact
                            />
                        </div>
                    </motion.aside>
                </>
            )}
        </AnimatePresence>
    )
}
