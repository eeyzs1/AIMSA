# Genome State

## Purpose
Snapshot of the current evolvable configuration.
This is what gets mutated during evolution.

## Current Genome

### Harness Genome
```yaml
constraints:
  - id: C001
    rule: "every task must have acceptance criteria"
    source: "initial design"
    last_triggered: null
    trigger_count: 0

  - id: C002
    rule: "no agent self-certifies"
    source: "initial design"
    last_triggered: null
    trigger_count: 0

  - id: C003
    rule: "every mistake produces a new constraint"
    source: "initial design"
    last_triggered: null
    trigger_count: 0

  - id: C004
    rule: "external service failure must not crash the app"
    source: "evolution 1 - DB connection crash"
    last_triggered: "2026-04-16"
    trigger_count: 1

  - id: C005
    rule: "text processing must handle input without natural boundaries"
    source: "evolution 3 - chunking failure on long paragraphs"
    last_triggered: "2026-04-16"
    trigger_count: 1

  - id: C006
    rule: "all API endpoints must have rate limiting and configurable CORS"
    source: "evolution 11 - wildcard CORS and no rate limiting"
    last_triggered: "2026-04-18"
    trigger_count: 1

  - id: C007
    rule: "health checks must verify actual dependency connectivity"
    source: "evolution 9 - health check always returned healthy"
    last_triggered: "2026-04-18"
    trigger_count: 1

  - id: C008
    rule: "external service calls must have retry with backoff"
    source: "evolution 10 - LLM call had no retry"
    last_triggered: "2026-04-18"
    trigger_count: 1

workflows:
  - id: W001
    name: "base flow"
    steps: [define, plan, execute, verify, record]
    source: "initial design"

skills:
  - id: S001
    name: "self-verify"
    source: "initial design"

  - id: S002
    name: "task-decompose"
    source: "initial design"
```

### Agent Genome
```yaml
topology_rules:
  - "always add verifier"
  - "merge tightly coupled roles"
  - "split when context exceeds budget"

default_scope:
  max_context_lines: 60
  handoff_format: "structured YAML"
```

### Evolution Genome (Meta)
```yaml
fitness_weights:
  verification_pass_rate: 0.3
  task_completion_rate: 0.25
  error_recurrence_rate: 0.2
  time_to_completion: 0.15
  constraint_efficiency: 0.1

mutation_rate: 0.1
selection_threshold: "fitness must improve or complexity must decrease"
safety_constraints:
  - "never remove verification layer"
  - "never remove evolution system"
  - "mutation rate <= 30%"
  - "all mutations reversible"
```

## Genome Version
- Version: 3
- Last evolved: 2026-04-18
- Total mutations applied: 8
