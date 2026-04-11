# Workflow Patterns

Five common patterns from the [Anthropic Skills Guide](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf).

---

## Pattern 1: Sequential Workflow Orchestration

**Use when:** Multi-step processes in a specific order.

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)
```

**Key techniques:** Explicit step ordering, dependencies between steps, validation at each stage, rollback instructions for failures.

---

## Pattern 2: Conditional Workflows

**Use when:** Tasks with branching logic and decision points.

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Step A
   - Step B

3. Editing workflow:
   - Step X
   - Step Y
```

---

## Pattern 3: Iterative Refinement

**Use when:** Output quality improves with iteration.

```markdown
## Iterative Report Creation

### Initial Draft
1. Fetch data
2. Generate first draft
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues (missing sections, formatting, data errors)

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key techniques:** Explicit quality criteria, validation scripts, know when to stop iterating.

---

## Pattern 4: Context-Aware Tool Selection

**Use when:** Same outcome, different tools depending on context.

```markdown
## Smart File Storage

### Decision Tree
1. Check file type and size
2. Determine best storage:
   - Large files (>10MB): Cloud storage
   - Collaborative docs: Notion/Docs
   - Code files: GitHub
   - Temporary files: Local storage

### Execute Storage
Based on decision:
- Call appropriate tool
- Apply service-specific metadata
- Generate access link

### Explain to User
Explain why that approach was chosen (transparency).
```

**Key techniques:** Clear decision criteria, fallback options, transparency about choices.

---

## Pattern 5: Domain-Specific Intelligence

**Use when:** Skill adds specialized knowledge beyond tool access.

```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Process transaction
  - Apply fraud checks
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key techniques:** Domain expertise embedded in logic, compliance before action, comprehensive audit trail.

---

## Parallel Workflows

**Use when:** Independent tasks that can run simultaneously.

```markdown
These steps can be done in parallel:
- [ ] Run unit tests
- [ ] Run linting
- [ ] Build documentation

Wait for all to complete before:
- Deploy to staging
```
