# SPEC Prompt Template — URL Shortener

Use this when starting a new feature specification.

```
/spec "Feature: [name] | Effort: [Low/Medium/High] | Risk: [Low/Medium/High]"
```

## Example Prompts

### Phase 1: Core API
```
/spec "Implement POST /shorten endpoint with auto-generated short code (base62 encoding)"
```

### Phase 2: Redirect & Analytics
```
/spec "Implement GET /{short_url} redirect with click tracking"
```

### Phase 3: Custom URLs
```
/spec "Add support for custom short URL with uniqueness validation (max 16 chars)"
```

### Phase 4: Expiry & Deletion
```
/spec "Implement URL expiry after 1 month with soft delete"
```

### Phase 5: Redis Caching
```
/spec "Implement Redis cache layer for URL lookups (80/20 Pareto rule)"
```

---

## What the /spec Skill Produces

1. **Objective**: Business problem → Technical solution
2. **Functional Description**: Observable behavior
3. **Technical Flow**: Trigger → Validation → Processing → Persistence → Response
4. **Acceptance Criteria** (Gherkin): Success + Error scenarios
5. **Assumptions**: What must be true? How to validate?
6. **Technical Considerations**: Endpoints, Database, Cache, Security, Observability
7. **Solution Design** (Mermaid): Data flow diagram
8. **Definition of Done**: Test, Migration, Docs, Security, Performance

---

## Output Location

Saved to: `docs/specs/YYYYMMDD-FEATURE_spec.md`

---

## Next Step After Spec Approved

```
/plan "Implement based on [spec-name] specification"
```
