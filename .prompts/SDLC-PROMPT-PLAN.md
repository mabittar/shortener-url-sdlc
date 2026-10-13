# PLAN Prompt Template — URL Shortener

Use this after spec is approved to break it into tasks.

```
/plan "Implement based on [spec-name] specification"
```

## Example Prompts

### After Spec Phase 1 Approved
```
/plan "Break down POST /shorten spec into implementation tasks"
```

### After Spec Phase 2 Approved
```
/plan "Create task breakdown for redirect + analytics feature"
```

---

## What the /plan Skill Produces

1. **Alternative Analysis**: At least 2 approaches with trade-offs
2. **Solution Design**: Architecture flowchart (Mermaid)
3. **Refactoring Strategy**: If refactoring legacy code
4. **Task Breakdown**: 
   - Granular tasks (< 4h each, < 5 files per task)
   - Objective, Files, Steps, Acceptance Criteria, Rollback per task
   - Risk-ordered, isolated, reduced
5. **Commit Sequencing**: Keep build green at every step
6. **Dependency Graph**: What blocks what?

---

## Output Location

Saved to: `tasks/plans/YYYYMMDD-FEATURE_plan.md`

---

## Next Step After Plan Approved

```
/code "Execute tasks from [plan-name]"
```
