# User Stories

v1 scope only. Pronunciation feedback and progress-tracking are deferred to v2 (see
`SCAFFOLDING_GRILLING_CHECKPOINT.md`).

## US-01: Interactive CLI session

**As a** learner
**I want** to start a CLI session and have an ongoing conversation until I choose to exit
**So that** I get an interactive practice session without any setup beyond running one command

### Acceptance Criteria
- [x] `uv run product` starts an interactive prompt loop
- [x] conversation history is kept for the duration of the run (no persistence across runs)
- [x] typing an exit command (e.g. `exit` / `quit`) ends the session cleanly

## US-02: Conversation practice with the tutor agent

**As a** learner
**I want** to chat freely about Chinese and get inline grammar correction/explanation
**So that** I can practice conversation and learn from my mistakes as I go

### Acceptance Criteria
- [x] agent replies in European Portuguese (not Brazilian)
- [x] agent stays on-topic (Chinese learning); off-topic requests are redirected
- [x] when I write a Chinese sentence with a grammar mistake, the agent identifies it
- [x] the agent explains the correction, not just states it

## US-03: Vocab quiz drilling

**As a** learner
**I want** to ask to be quizzed on specific words or phrases
**So that** I can drill vocabulary I choose, on demand

### Acceptance Criteria
- [x] I can name the word(s)/phrase(s) to be quizzed on
- [x] the agent asks questions about the requested vocab (not unrelated vocab)
- [x] the agent correctly judges whether my answer is right or wrong
- [x] feedback is given in European Portuguese

## US-04: Orchestrator routes to the correct sub-agent

**As a** learner
**I want** the app to automatically send my message to the right mode (chat vs. quiz)
**So that** I don't have to manually switch modes myself

### Acceptance Criteria
- [x] a "quiz me on X" style message routes to the vocab quiz agent (US-03)
- [x] a free-form chat message routes to the tutor agent (US-02)
- [x] routing is handled by a keyword heuristic in the LangGraph orchestrator (no LLM classifier call for v1)

## US-05: Polish the tutor, quiz, and orchestrator for everyday robustness

**As a** learner
**I want** the app to keep behaving correctly through a full quiz session, handle blank input and backend
errors gracefully, and have its architecture documented
**So that** a normal session doesn't break on things like answering a quiz question, an accidental empty
message, or Ollama being unreachable

### Acceptance Criteria
- [x] once a quiz has started, my answers keep routing to the quiz agent (not the tutor) until it declares
      the drill complete, even when my answer text contains no quiz keyword
- [x] submitting an empty or whitespace-only message is a no-op (no agent call, no history entry, prompt
      shown again)
- [x] if the Ollama backend is unreachable, the CLI reports a clear one-line error for that turn and the
      session stays alive for the next input, instead of crashing
- [x] `product/README.md` documents the three-agent + orchestrator architecture and how to run the CLI
