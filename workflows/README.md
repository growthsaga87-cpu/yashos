# workflows/ — The Instruction Layer

Markdown SOPs (Standard Operating Procedures). Each workflow briefs the agent on
how to accomplish one objective — written in plain language, the way you'd brief
a teammate.

## Each workflow should define

1. **Objective** — what success looks like.
2. **Required inputs** — what the agent needs before starting.
3. **Tools to use** — which scripts in `tools/` to run, in what sequence.
4. **Expected outputs** — where deliverables go (usually a cloud service).
5. **Edge cases & failure handling** — known quirks, rate limits, retries.

Keep workflows current: when you discover a better method or a new constraint,
update the relevant workflow so the system gets more robust over time.
(Don't create or overwrite workflows without the user's say-so.)

## Template — `workflows/<name>.md`

```markdown
# Workflow: <Name>

## Objective
<One sentence on the goal.>

## Required Inputs
- <input 1>
- <input 2>

## Steps
1. Read inputs / validate.
2. Run `tools/<script>.py --arg ...`
3. Transform / verify the result.
4. Deliver output to <destination>.

## Outputs
- <where the final deliverable lives>

## Edge Cases & Notes
- <rate limits, timing quirks, gotchas learned over time>
```
