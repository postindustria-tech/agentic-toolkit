---
name: plugin-qa-skill-qa-audit
description: "This skill should be used when you need to \"audit a skill\", \"verify skill quality\", \"QA check skill\", \"validate skill file\", \"check for deprecated APIs\", \"verify code examples\". Performs comprehensive QA verification by checking every line of instruction, code example, and claim against official documentation. Produces structured audit reports with severity ratings."
version: 1.0.0
---

# Skill QA Auditor

Systematically verify plugin skill files against official documentation to ensure 100% correctness.

## Audit Workflow

Follow these steps sequentially to complete a comprehensive audit:

### 1. Read and Parse the Skill File

- Locate and read the skill file (typically `SKILL.md` or `skill.md`)
- Extract all verifiable items:
  - Import statements
  - Code examples (with line numbers)
  - API calls and method signatures
  - Configuration patterns
  - Best practice recommendations
  - Documentation links
  - Claims about functionality or behavior
- Identify the technology/framework and version

### 2. Research Official Documentation

For EACH code example, import, and API call:

- **WebSearch**: `"[tech] [API] documentation site:[official-domain] 2025 OR 2026"`
  - Focus on recent documentation (2025/2026)
  - Target official domains only
- **WebFetch**: Retrieve and analyze official documentation
  - Verify exact API signatures, parameters, and usage
  - Document findings with verification status and source URL

**Research Priority**: Official docs → GitHub examples/tests → Official blog → Package registries

### 3. Systematic Verification

Verify each category of content:

#### Code Examples

For every code block, verify:
- ✅ **Completeness**: All required imports present
- ✅ **Syntax**: No syntax errors
- ✅ **Executability**: Code would run without errors
- ✅ **Correctness**: APIs called with correct parameters
- ✅ **Currency**: No deprecated APIs used
- ✅ **Type hints**: Accurate if present
- ✅ **Error handling**: Appropriate for the use case

Document: ✅ VERIFIED or ❌ ISSUE FOUND

#### Import Statements

For every import, verify:
- Package name is correct
- Import path is current (not deprecated)
- Import exists in the package
- Installation notes if needed

Create verification table with source documentation.

#### API Calls

For every API call/method/function, verify:
- Find official API documentation
- Compare signatures (skill vs official)
- Verify parameters are correct
- Check for missing required parameters
- Note optional parameters that should be mentioned

Create verification table comparing skill vs official docs.

#### Documentation Links

For every URL/reference, verify:
- **WebFetch** to test link (HTTP status)
- Verify it points to claimed resource
- Ensure it covers stated topic
- Check it's current (not outdated)

Document status: ✅ Valid / ❌ Broken / ⚠️ Redirected

### 4. Identify Issues by Severity

Categorize all issues:

- **Critical**: Bugs, incorrect information, security vulnerabilities
- **High**: Deprecated APIs, incomplete code examples, broken imports
- **Medium**: Missing best practices, outdated links, incomplete documentation
- **Low**: Minor improvements, formatting issues

For each issue document:
- Severity level
- Location (section/line numbers)
- Current content
- Expected content
- Official documentation source
- Impact description

### 5. Produce Structured Audit Report

Save to: `.claude/skill-audits/{plugin-name}/{skill-name}/AUDIT_{YYYYMMDD_HHMMSS}.md`

## Audit Report Structure

### Required Sections

#### 1. Header & Overall Assessment

```markdown
# Skill QA Audit Report

**Skill**: [skill-name]
**File**: [path/to/skill.md]
**Audit Date**: YYYY-MM-DD HH:MM:SS
**Technology/Framework**: [tech name and version]
**Quality Rating**: X/10
**Status**: ✅ Approved / ⚠️ Approved with issues / ❌ Rejected

## Executive Summary

[1-2 paragraphs summarizing findings, quality, and overall assessment]
```

#### 2. Audit Scope

```markdown
## Audit Scope

- **Code Examples Verified**: X
- **Import Statements Verified**: X
- **API Calls Verified**: X
- **Documentation Links Verified**: X
- **Web Searches Performed**: X
- **Documentation Pages Reviewed**: X

### Issues Found by Severity
- **Critical**: X
- **High**: X
- **Medium**: X
- **Low**: X
```

#### 3. Verification Statistics

```markdown
## Verification Statistics

| Category | Total | Verified ✅ | Issues ❌ | Verification Rate |
|----------|-------|-------------|-----------|-------------------|
| Code Examples | X | X | X | XX% |
| Import Statements | X | X | X | XX% |
| API Calls | X | X | X | XX% |
| Documentation Links | X | X | X | XX% |
```

#### 4. Issues by Severity

List all issues from Critical → High → Medium → Low:

```markdown
## Issues by Severity

### Critical Issues

#### Issue 1: [Title]
- **Location**: Line XX, [section name]
- **Current**: [what the skill currently says/shows]
- **Expected**: [what it should be]
- **Reason**: [why this is wrong]
- **Source**: [official documentation URL]
- **Impact**: [description of impact]

[Repeat for each critical issue]

### High Priority Issues
[Same structure]

### Medium Priority Issues
[Same structure]

### Low Priority Issues
[Same structure]
```

#### 5. Detailed Verification Tables

##### Import Verification

```markdown
## Import Verification

| Import Statement | Status | Package | Documentation |
|-----------------|--------|---------|---------------|
| `from x import y` | ✅ | package-name | [link] |
| `import z` | ❌ | Issue: deprecated | [link] |
```

##### API Call Verification

```markdown
## API Call Verification

| API Call | Location | Skill Signature | Official Signature | Status | Documentation |
|----------|----------|-----------------|-------------------|--------|---------------|
| `func(a, b)` | Line XX | `func(a, b)` | `func(a, b, c=None)` | ⚠️ Missing param | [link] |
```

##### Code Example Verification

For each example, create detailed assessment:

```markdown
### Code Example X (Lines XX-XX)

**Location**: [Section name]

**Code**:
```python
[actual code from skill]
```

**Verification Checklist**:
- ✅ Completeness: All imports present
- ✅ Syntax: Valid Python syntax
- ❌ Executability: Missing import for `datetime`
- ✅ Correctness: API called correctly
- ⚠️ Currency: Uses deprecated `method_old()` instead of `method_new()`
- ✅ Type Hints: Accurate
- ⚠️ Error Handling: Should include try/except for network calls

**Official Documentation**: [link]
**Status**: ❌ Needs fixes
```

##### Link Verification

```markdown
## Documentation Link Verification

| URL | HTTP Status | Target | Status | Notes |
|-----|-------------|--------|--------|-------|
| https://... | 200 OK | API docs | ✅ Valid | Current version |
| https://... | 404 | - | ❌ Broken | Page not found |
| https://... | 301 | Redirected | ⚠️ Redirect | Update to new URL |
```

#### 6. Best Practices Alignment

```markdown
## Best Practices Alignment

### Framework Best Practices
- ✅ Uses recommended patterns for [X]
- ❌ Missing error handling for [Y]
- ⚠️ Could improve [Z]

### Code Quality
- **Type Hints**: [Assessment]
- **Error Handling**: [Assessment]
- **Async Patterns**: [Assessment if applicable]
- **Security**: [Assessment]
```

#### 7. Recommendations

```markdown
## Recommendations

### Must Fix (Before Approval)
1. [Issue description] - [Location]
2. [Issue description] - [Location]

### Should Fix (High Priority)
1. [Issue description] - [Location]
2. [Issue description] - [Location]

### Nice to Have (Medium/Low Priority)
1. [Improvement suggestion] - [Location]
2. [Improvement suggestion] - [Location]
```

#### 8. Documentation Sources

```markdown
## Documentation Sources

1. [Official Documentation Title] - https://...
2. [API Reference] - https://...
3. [GitHub Examples] - https://...
[Continue numbering all sources used]
```

#### 9. Quality Metrics & Final Recommendation

```markdown
## Quality Metrics

| Metric | Score (out of 10) |
|--------|-------------------|
| Code Correctness | X/10 |
| API Accuracy | X/10 |
| Documentation Quality | X/10 |
| Completeness | X/10 |
| Currency (Up-to-date) | X/10 |
| Best Practices | X/10 |
| **Overall Quality** | **X/10** |

## Final Recommendation

**Status**: ✅ Approved / ⚠️ Approved with fixes / ❌ Rejected

**Reasoning**:
[Detailed explanation of the final recommendation based on findings]

**Next Steps**:
1. [Action item]
2. [Action item]
3. [Action item]
```

## Audit Completion Standards

An audit is complete when:

- ✅ **100% coverage** - Every code example, import, API call, link verified
- ✅ **Official sources** - All verifications backed by official documentation (2025/2026)
- ✅ **Specific citations** - Exact line references, URLs, and sources included
- ✅ **Severity categorized** - All issues labeled Critical/High/Medium/Low with actionable fixes
- ✅ **Comprehensive report** - Structured report with clear recommendation
- ✅ **Strict standards** - Even minor issues flagged; 100% correctness is the goal
- ✅ **Honest assessment** - Uncertain items marked and documented with reasons

## Tips for Effective Audits

1. **Be thorough**: Don't skip examples or assume correctness
2. **Use recent docs**: Prioritize 2025/2026 documentation over older sources
3. **Document everything**: Include source URLs for all verifications
4. **Be specific**: Reference exact line numbers and sections
5. **Test links**: Actually fetch URLs to verify they work
6. **Compare signatures**: Don't assume APIs match - verify exact parameters
7. **Check imports**: Verify full import paths, not just module names
8. **Consider context**: Security implications, error handling, edge cases
