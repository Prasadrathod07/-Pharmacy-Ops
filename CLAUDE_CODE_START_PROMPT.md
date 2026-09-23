# Claude Code Starter Prompt

You are the implementation engineer for this project.

Before doing anything:

1. Read `pharmacy_order_inventory_master_spec.md` completely.
2. Read `CLAUDE_CODE_IMPLEMENTATION_PROMPTS.md` completely.
3. Inspect the current repository.
4. Confirm that `.env` exists, but **do not print, echo, log, copy, or expose any secret value from it**.
5. Treat `pharmacy_order_inventory_master_spec.md` as the authoritative product and architecture specification.
6. Treat `CLAUDE_CODE_IMPLEMENTATION_PROMPTS.md` as the controlled execution plan.

Now execute **PROMPT 00 only** from `CLAUDE_CODE_IMPLEMENTATION_PROMPTS.md`.

Important rules:

- Do not begin PROMPT 01.
- Do not implement business features yet.
- Do not change MySQL to PostgreSQL or Supabase.
- Do not add authentication, payments, customer ecommerce, delivery tracking, AI/LLMs, microservices, Kafka, Kubernetes, or any other out-of-scope system.
- Never expose `.env` values.
- Preserve the master specification exactly unless a genuine technical conflict is found.
- If you find a conflict or blocker, stop and explain it instead of making a silent architecture change.
- At the end, provide the exact **PHASE COMPLETION REPORT** required by PROMPT 00.
