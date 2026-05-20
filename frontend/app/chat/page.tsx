'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'
import { AnimatePresence, motion } from 'framer-motion'
import { Sparkles, X } from 'lucide-react'

import { useAuth } from '@/contexts/auth-context'
import { getChatScrollStorageKey, useChatScrollPersistence } from '@/app/lib/chatScrollPersistence'

import { DungeonExperience } from '@/app/chat/components/DungeonExperience'
import { DashboardSection } from '@/app/chat/components/DashboardSection'
import { LevelUpModal } from '@/app/chat/components/LevelUpModal'
import { MilestoneToastStack } from '@/app/chat/components/MilestoneToast'

import { FloatingConversationCard } from '@/app/chat/components/vibe/FloatingConversationCard'
import { VibeAmbientBackground } from '@/app/chat/components/vibe/VibeAmbientBackground'
import { VibeMessageThread } from '@/app/chat/components/vibe/VibeMessageThread'
import { VibeComposer } from '@/app/chat/components/vibe/chrome/VibeComposer'
import { VibeCornerControls } from '@/app/chat/components/vibe/chrome/VibeCornerControls'
import { VibeXpPill } from '@/app/chat/components/vibe/chrome/VibeXpPill'
import { VibeProjectsDrawer } from '@/app/chat/components/vibe/drawer/VibeProjectsDrawer'
import { VibeQuizModal } from '@/app/chat/components/vibe/overlays/VibeQuizModal'
import { VibeRoadmapLoading } from '@/app/chat/components/vibe/overlays/VibeRoadmapLoading'
import { VibeRoadmapStartModal } from '@/app/chat/components/vibe/overlays/VibeRoadmapStartModal'
import { VibeTaskFocusModal } from '@/app/chat/components/vibe/overlays/VibeTaskFocusModal'

import { useChatSession } from '@/app/chat/hooks/useChatSession'

function LoadingShell() {
    return (
        <div className="relative flex h-full min-h-0 min-w-0 flex-col items-center justify-center overflow-x-hidden overflow-y-hidden">
            <VibeAmbientBackground />
            <div className="relative z-10 flex flex-col items-center gap-3">
                <div className="h-10 w-10 animate-spin rounded-full border-2 border-teal-400/30 border-t-teal-400" />
                <p className="text-sm text-zinc-400">Loading…</p>
            </div>
        </div>
    )
}

export default function ChatPage() {
    const { user, loading, isDevUser, isAnonymous, ensureAnonymousSession } = useAuth()
    const [guestBootError, setGuestBootError] = useState<string | null>(null)
    const messagesScrollRef = useRef<HTMLDivElement>(null)
    const s = useChatSession(user, messagesScrollRef)

    useEffect(() => {
        if (loading) return
        if (user || isDevUser) return
        let cancelled = false
        void ensureAnonymousSession().then(res => {
            if (cancelled) return
            if (!res.ok) setGuestBootError(res.error || 'Could not start guest session.')
        })
        return () => {
            cancelled = true
        }
    }, [loading, user, isDevUser, ensureAnonymousSession])

    const chatScrollStorageKey = useMemo(
        () => getChatScrollStorageKey({ userId: user?.id, sessionId: s.session?.session_id, projectId: s.selectedProjectId }),
        [user?.id, s.session?.session_id, s.selectedProjectId]
    )
    useChatScrollPersistence(messagesScrollRef, {
        storageKey: chatScrollStorageKey,
        messagesLength: s.dungeonPhase === 'hidden' ? s.messages.length : s.dungeonMessages.length,
        busy: s.busy,
        sessionActive: Boolean(s.session?.session_id),
    })

    if (loading) {
        return <LoadingShell />
    }

    if (guestBootError) {
        return (
            <div className="relative flex h-full min-h-0 min-w-0 flex-col items-center justify-center overflow-x-hidden overflow-y-hidden p-6">
                <VibeAmbientBackground />
                <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="relative z-10 w-full max-w-sm rounded-3xl border border-white/10 bg-zinc-950/70 p-8 text-center shadow-2xl backdrop-blur-xl"
                >
                    <h1 className="text-xl font-semibold text-zinc-50">Couldn&apos;t start session</h1>
                    <p className="mt-2 text-sm text-zinc-500">{guestBootError}</p>
                    <p className="mt-3 text-xs text-zinc-600">
                        Enable <strong>Anonymous sign-ins</strong> in the Supabase dashboard (Authentication → Providers →
                        Anonymous).
                    </p>
                    <button
                        type="button"
                        onClick={() => {
                            setGuestBootError(null)
                            void ensureAnonymousSession().then(res => {
                                if (!res.ok) setGuestBootError(res.error || 'Could not start guest session.')
                            })
                        }}
                        className="mt-6 inline-flex w-full items-center justify-center rounded-2xl border border-white/15 py-3 text-sm font-semibold text-zinc-200 hover:bg-white/5"
                    >
                        Retry
                    </button>
                </motion.div>
            </div>
        )
    }

    if (!user && !isDevUser) {
        return <LoadingShell />
    }

    const level = s.profile?.current_level ?? 1
    const xp = s.profile?.xp ?? 0

    return (
        <div className="relative flex h-full min-h-0 min-w-0 flex-col overflow-x-hidden overflow-y-hidden">
            <VibeAmbientBackground />
            <VibeCornerControls onOpenDrawer={() => s.setDrawerOpen(true)} onOpenDashboard={() => s.setIsDashboardOpen(true)} />
            {s.profile ? <VibeXpPill level={level} xp={xp} /> : null}

            {isAnonymous ? (
                <div className="pointer-events-none fixed left-1/2 top-[4.25rem] z-30 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 sm:top-5 sm:left-auto sm:right-[4.5rem] sm:translate-x-0">
                    <div className="pointer-events-auto rounded-xl border border-white/10 bg-zinc-950/80 px-3 py-2 text-center shadow-lg backdrop-blur-md sm:text-left">
                        <p className="text-[11px] leading-snug text-zinc-400">
                            Browsing as a guest (limits apply).{' '}
                            <Link href="/auth/signup" className="font-semibold text-teal-300 hover:text-teal-200">
                                Save your progress
                            </Link>
                        </p>
                    </div>
                </div>
            ) : null}

            <VibeRoadmapLoading visible={s.isRoadmapLoading} query={s.roadmapCreationQuery} />

            <div className="relative z-10 flex min-h-0 min-w-0 flex-1 items-center justify-center overflow-x-hidden px-4 py-3 sm:py-4">
                <FloatingConversationCard className="h-[min(100%,calc(100dvh-7rem))] max-h-[min(calc(100dvh-7rem),52rem)] min-h-[12rem] w-[min(96vw,60rem)] sm:w-[min(94vw,64rem)]">
                    <AnimatePresence mode="wait">
                        {s.dungeonPhase === 'hidden' ? (
                            <motion.div
                                key="chat-lecture"
                                className="flex min-h-0 min-w-0 w-full flex-1 flex-col"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0, filter: 'blur(8px)' }}
                                transition={{ duration: 0.3 }}
                            >
                                <div className="shrink-0 border-b border-white/[0.06] px-5 pb-3 pt-4">
                                    <h2 className="text-center text-3xl font-semibold tracking-tight text-zinc-50 sm:text-[2.1rem]">
                                        {String(
                                            s.currentTopic?.title ||
                                                s.currentSkill?.title ||
                                                s.currentDomain?.title ||
                                                'Lecture'
                                        )}
                                    </h2>
                                </div>
                                <VibeMessageThread
                                    messages={s.messages}
                                    busy={s.busy}
                                    showDungeonButton={s.showDungeonButton}
                                    showQuizReadyButton={s.showQuizReadyButton}
                                    quizReadyButtonLabel={s.quizReadyButtonLabel}
                                    onDungeon={() => void s.handleDungeonStart()}
                                    onQuizReady={() => void s.handleQuizReadyFromButton()}
                                    scrollContainerRef={messagesScrollRef}
                                />
                                <VibeComposer
                                    value={s.input}
                                    onChange={s.setInput}
                                    onSubmit={s.handleSubmit}
                                    placeholder={s.placeholder}
                                    disabled={s.isStartModeOverlayOpen || Boolean(s.pendingQuestion)}
                                    busy={s.busy}
                                />
                            </motion.div>
                        ) : (
                            <motion.div
                                key="chat-dungeon"
                                className="flex min-h-0 min-w-0 w-full flex-1 flex-col overflow-hidden px-1 pt-1"
                                initial={{ opacity: 0, scale: 0.96, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: 6 }}
                                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                            >
                                <DungeonExperience
                                    phase={s.dungeonPhase}
                                    scenarioTitle={s.session?.state?.dungeon?.scenario_title ?? null}
                                    messages={s.dungeonMessages}
                                    busy={s.busy}
                                    input={s.dungeonInput}
                                    onInputChange={s.setDungeonInput}
                                    onSubmit={s.handleDungeonSubmit}
                                    onAbort={() => void s.handleDungeonAbort()}
                                    showAbort={!s.dungeonResolved && s.dungeonPhase === 'active'}
                                    outcome={s.dungeonOutcome}
                                    onDismiss={() => void s.handleDungeonDismissFromOutcome()}
                                    theme="vibe"
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </FloatingConversationCard>
            </div>

            {s.pendingQuestion && !s.isQuizOverlayOpen && (
                <button
                    type="button"
                    onClick={s.reopenQuizOverlay}
                    disabled={s.busy}
                    className="fixed bottom-20 left-5 z-30 rounded-full border border-amber-400/40 bg-amber-950/80 px-4 py-2 text-xs font-medium text-amber-100 shadow-lg backdrop-blur-md transition hover:bg-amber-900/80 disabled:opacity-50 sm:bottom-6"
                >
                    Quiz waiting — open
                </button>
            )}

            <VibeProjectsDrawer
                open={s.drawerOpen}
                onClose={() => s.setDrawerOpen(false)}
                projects={s.projects}
                selectedProjectId={s.selectedProjectId}
                busy={s.busy}
                onSelect={id => void s.loadProject(id)}
                onDelete={id => void s.handleDeleteProject(id)}
                onStartNew={s.beginNewProject}
                profileLevel={level}
                profileXp={xp}
            />

            <VibeRoadmapStartModal
                visible={s.isStartModeOverlayOpen}
                roadmapLabel={s.roadmapRevealLabel || 'Your learning path'}
                busy={s.busy}
                onStartAtBeginning={() => void s.handleStartModeSelection('beginning')}
                onTakePlacementTest={() => void s.handleStartModeSelection('placement')}
            />

            <VibeTaskFocusModal
                visible={Boolean(s.taskReveal)}
                topicTitle={s.taskReveal?.topicTitle || ''}
                skillTitle={s.taskReveal?.skillTitle || ''}
                domainTitle={s.taskReveal?.domainTitle}
                actionLabel={s.isFocusConfirm ? 'Get started' : 'Continue'}
                onComplete={s.isFocusConfirm ? () => void s.handleFocusConfirm() : () => s.setTaskReveal(null)}
            />

            {s.showQuizOverlay && s.quizOverlayQuestion ? (
                <VibeQuizModal
                    question={s.quizOverlayQuestion}
                    busy={s.busy}
                    submitting={s.quizSubmitting}
                    selectedIndex={s.overlaySelectedIndex}
                    nextReady={s.nextReady}
                    error={null}
                    outcomeFeedback={s.quizOutcomeFeedback}
                    onSelectIndex={s.handleQuizChoice}
                    onSubmit={() => void s.handleQuizSubmit()}
                    onNext={s.handleNextQuestion}
                    onOutcomeContinue={s.handleQuizFeedbackContinue}
                    onClose={s.dismissQuizOverlay}
                />
            ) : null}

            <DashboardSection
                profile={s.profile}
                isOpen={s.isDashboardOpen}
                onClose={() => s.setIsDashboardOpen(false)}
            />

            {s.levelUpModal != null ? <LevelUpModal level={s.levelUpModal} onClose={() => s.setLevelUpModal(null)} /> : null}

            <MilestoneToastStack
                milestones={s.milestones}
                onDismiss={id => s.setMilestones(prev => prev.filter(m => m.id !== id))}
            />

            <AnimatePresence>
                {s.error && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="fixed bottom-5 left-1/2 z-[100] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 rounded-2xl border border-red-500/30 bg-zinc-950/95 p-4 shadow-xl backdrop-blur-md"
                    >
                        <p className="text-sm font-medium text-red-400">Error</p>
                        <p className="mt-1 text-xs text-zinc-400">
                            {typeof s.error === 'string' ? s.error : 'Something went wrong.'}
                        </p>
                        {isAnonymous &&
                        typeof s.error === 'string' &&
                        (s.error.includes('Guest accounts') || s.error.includes('guest')) ? (
                            <Link
                                href="/auth/signup"
                                className="mt-3 inline-block text-xs font-semibold text-teal-400 hover:text-teal-300"
                            >
                                Create a free account to continue →
                            </Link>
                        ) : null}
                        <button
                            type="button"
                            onClick={() => s.setError(null)}
                            className="absolute right-3 top-3 text-zinc-500 hover:text-zinc-300"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
