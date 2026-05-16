# Initial Quiz And Placement Pipeline

This document explains the current BKT-based initial quiz flow, how the backend updates learner knowledge, and how that same knowledge state is reused later in the roadmap.

## Short Answer

The initial quiz flow is placement only:

1. After the learner chooses **beginning** vs **placement** (start mode), the backend starts either guided playback or BKT placement.
2. A sequence of AI-authored placement probes updates Bayesian Knowledge Tracing probabilities for roadmap skills

The system no longer brackets the learner with a midpoint search. It now chooses the next skill by expected information gain over durable skill probabilities.

## What Counts As The Initial Quiz

At session start, the backend generates a new roadmap from the user's goal. The learner then picks start mode (**beginning** or **placement**). The first quiz they see is a BKT-driven placement probe (or they enter guided mode with no prior profile quiz).

So the first quiz a learner sees is a placement probe when they choose placement.

## End-To-End Request Path

```mermaid
sequenceDiagram
    participant UI as ChatUI
    participant FE as AgentApiClient
    participant API as FastAPIAgentAPI
    participant ORCH as LearningOrchestrator
    participant KStore as KnowledgeStateStore
    participant KA as KnowledgeAgent
    participant QA as QuizAgent
    participant DB as Supabase

    UI->>FE: createAgentSession(query)
    FE->>API: POST /api/agent/sessions
    API->>ORCH: create_session(user_id, query)
    ORCH->>DB: create project/session/events
    ORCH->>KStore: seed project skill state
    ORCH-->>UI: awaiting_start_mode

    UI->>API: start_mode placement or beginning
    API->>ORCH: _handle_start_mode()
    Note over ORCH: beginning → guided skill; placement → binary placement + probe

    ORCH->>KStore: select_next_skill / refresh state
    KStore-->>ORCH: skill + posteriors
    ORCH->>KA: plan_placement_probe()
    KA-->>ORCH: focus + difficulty + intro
    ORCH->>QA: generate()
    QA-->>ORCH: MCQ + correct answer
    ORCH->>DB: create agent_quizzes row
    ORCH-->>UI: pending placement question

    UI->>API: submit placement answer
    API->>ORCH: _handle_knowledge_turn()
    ORCH->>KStore: apply_quiz_observation()
    KStore->>DB: update user_skill_knowledge
    KStore->>DB: update project_skill_knowledge
    ORCH->>DB: create agent_quiz_attempts row
    ORCH->>DB: create user_skill_observations row

    alt stop criteria met
        ORCH->>ORCH: finalize learning frontier
    else continue calibration
        ORCH->>KStore: select_next_skill()
    end
```

## Stage 1: BKT Skill-State Seeding

Before placement starts, the backend seeds durable skill state for every roadmap skill:

- `user_skill_knowledge`: global per-user skill priors
- `project_skill_knowledge`: project-local overlays used for the active roadmap

This happens through `KnowledgeStateStore.seed_project_skill_states()`.

For unseen skills, the backend assigns a prior based on roadmap order so easier skills start with a higher `p_know` than later skills. For returning users, existing global skill probabilities are reused and copied into the project overlay.

## How The Next Placement Question Is Chosen

The orchestration step lives in `QuizRuntimeMixin._next_placement_probe()`.

It now does four main things:

1. Refresh project skill summaries from durable BKT state
2. Ask `KnowledgeStateStore.select_next_skill()` for the most revealing skill
3. Ask `KnowledgeAgent.plan_placement_probe()` for the best concept and wording focus for that skill
4. Ask `QuizAgent.generate()` to turn that plan into a four-option question

### 1. BKT Skill Selection

`KnowledgeStateStore.select_next_skill()` looks at:

- the current project-local `p_know` for each skill
- skill uncertainty
- expected information gain
- proximity to the current inferred frontier
- recent placement history to avoid repetition

The selected skill comes back with:

- `project_p_know`
- `global_p_know`
- `confidence`
- `selection_score`
- `selection_reason`

### 2. Knowledge Agent Planning

`KnowledgeAgent.plan_placement_probe()` does not decide mastery.

Its job is now:

- choose the concept most worth testing inside the selected skill
- choose difficulty
- decide whether the prompt should feel more like a probe or a confirmatory check
- avoid repeated wording and repeated focus areas

### 3. Quiz Generation

`QuizAgent.generate()` still produces:

- `prompt`
- `options`
- `correct_option_index`
- `explanation`
- `focus`
- `concept_id`
- `difficulty`

The quiz itself is still AI-generated, but correctness is checked algorithmically against the persisted answer key.

## How The Answer Is Evaluated

The grading entry point is `PlacementFlowMixin._handle_knowledge_turn()`.

When the learner answers:

1. The orchestrator resolves the selected option
2. It computes correctness with `selected_index == quiz["correct_option_index"]`
3. It calls `KnowledgeStateStore.apply_quiz_observation()`
4. `BKTEngine` updates the posterior probability for the targeted skill
5. The backend persists:
   - the quiz attempt
   - the observation log
   - the updated global skill state
   - the updated project-local skill state
6. The orchestrator refreshes the cached knowledge summary in session state
7. The system either stops placement or asks the next most informative question

## What The BKT Layer Stores

The most important durable fields are:

- `p_know`
- `p_init`
- `p_learn`
- `p_guess`
- `p_slip`
- `observation_count`
- `correct_count`
- `incorrect_count`
- `last_quiz_id`
- `last_attempt_id`

These live in:

- `user_skill_knowledge`
- `project_skill_knowledge`
- `user_skill_observations`

## How The System Gauges Knowledge Level

The learner's knowledge level is now inferred from durable skill probabilities rather than a temporary bracket.

At a high level:

1. Each skill has a current `p_know`
2. Every scored quiz answer updates that posterior
3. The system treats the first skill below the mastery threshold as the current frontier
4. The next quiz targets whichever nearby skill is expected to reduce uncertainty the most

So the system is now using:

- roadmap ordering
- AI-authored probe questions
- algorithmic correctness checks
- Bayesian posterior updates
- expected information gain for next-skill selection

## Confidence, Frontier, And Stop Criteria

Placement keeps going until one of the stop conditions is met:

1. The question budget is exhausted
2. The frontier is considered stable enough under the current BKT confidence heuristic
3. All skills appear mastered for the current roadmap

Current stop reasons include:

- `budget_reached`
- `frontier_stable`
- `all_mastered`

## What Happens After Placement Ends

Once placement stops:

1. The current frontier skill becomes `state.knowledge_state.learning_frontier`
2. `TaskerAgent` decomposes that skill into 2-4 lesson topics
3. `ConversationAgent` starts teaching the first topic
4. Topic quizzes update the same BKT-backed skill probabilities

That means the BKT state survives beyond initial placement and continues to influence future roadmap quizzes.

## State Fields Worth Watching During Debugging

These are the most useful runtime fields now:

- `state.knowledge_state.current_probe`
- `state.knowledge_state.learning_frontier`
- `state.knowledge_state.skill_probabilities_summary`
- `state.knowledge_state.skills`
- `state.placement_state.question_budget_used`
- `state.placement_state.global_history`
- `state.placement_state.selection_policy`
- `state.placement_state.frontier_index`
- `state.active_quiz_id`

And the durable source of truth is in Supabase:

- `user_skill_knowledge`
- `project_skill_knowledge`
- `user_skill_observations`
- `agent_quizzes`
- `agent_quiz_attempts`

## Practical Summary

The current implementation gauges the learner's knowledge level like this:

- the knowledge-state store picks the most revealing skill using BKT
- the knowledge agent chooses the concept and framing for that skill
- the quiz agent generates the multiple-choice question and answer key
- the orchestrator checks correctness algorithmically
- the BKT engine updates durable mastery probabilities
- the updated probabilities drive the next quiz and later roadmap quizzes
