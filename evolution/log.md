# Evolution Log

## Purpose
Track every evolutionary mutation — proposed, adopted, and rejected.
This is the fossil record of the system's self-improvement.

## Format
```
## Evolution [N]
- Date: [when]
- Trigger: [periodic|reactive|emergency|adaptive]
- Genome Level: [harness|agent|meta]
- Mutation Type: [ADD|REMOVE|STRENGTHEN|WEAKEN|MERGE|SPLIT|etc.]
- Target: [what was mutated]
- Before: [state before mutation]
- After: [state after mutation]
- Fitness Before: [score]
- Fitness After: [score]
- Verdict: [adopted|rejected|reverted]
- Reason: [why adopted or rejected]
```

## Evolution History

## Evolution 1
- Date: 2026-04-16
- Trigger: reactive (verification failure)
- Genome Level: harness
- Mutation Type: ADD
- Target: global exception handler in FastAPI main.py
- Before: unhandled DB connection errors caused 500 crashes
- After: global exception handler returns 503 with structured error message
- Fitness Before: verification_pass_rate ~60% (app crashed on DB failure)
- Fitness After: verification_pass_rate 100% (42/42 checks pass)
- Verdict: adopted
- Reason: DB unavailability should not crash the app; graceful degradation is a reliability requirement

## Evolution 2
- Date: 2026-04-16
- Trigger: reactive (potential runtime failure)
- Genome Level: harness
- Mutation Type: STRENGTHEN
- Target: Celery task async event loop handling
- Before: used asyncio.run() which fails if event loop exists
- After: explicit new_event_loop() + run_until_complete() + close() per task
- Fitness Before: potential runtime failure in edge cases
- Fitness After: deterministic event loop lifecycle per task
- Verdict: adopted
- Reason: Celery workers run in separate processes but defensive loop management prevents edge-case failures

## Evolution 3
- Date: 2026-04-16
- Trigger: reactive (verification failure)
- Genome Level: harness
- Mutation Type: STRENGTHEN
- Target: text chunking logic in document_tasks.py
- Before: only split on paragraph boundaries; single long paragraph never split
- After: force-split paragraphs exceeding chunk_size, with overlap
- Fitness Before: text chunking test failed (1/42)
- Fitness After: all 42/42 verification checks pass
- Verdict: adopted
- Reason: real documents often have long paragraphs without double-newline breaks; must handle this

## Evolution 4
- Date: 2026-04-16
- Trigger: reactive (missing configuration)
- Genome Level: harness
- Mutation Type: ADD
- Target: Streamlit secrets.toml configuration
- Before: no secrets.toml, frontend would use hardcoded localhost
- After: secrets.toml with Docker-internal service URL
- Fitness Before: frontend would fail in Docker Compose
- Fitness After: frontend correctly connects to backend service
- Verdict: adopted
- Reason: Docker Compose networking requires internal hostnames, not localhost
