# UAT Best Practices

A practical reference for running effective User Acceptance Testing sessions, communicating with stakeholders, and avoiding common pitfalls.

---

## 1. Running Effective UAT Sessions

### Before the Session
- **Define the scope clearly.** Testers should know exactly which features are in scope and which are not. A one-page scope summary prevents scope creep during testing.
- **Prepare the environment.** The UAT environment should mirror production as closely as possible. Verify stability with a smoke test before inviting anyone.
- **Pre-load test data.** Realistic, representative data helps testers exercise real workflows. Anonymize production data if using it.
- **Assign roles.** Designate a UAT coordinator to triage issues in real time, a technical contact for environment problems, and clear ownership for each feature area.

### During the Session
- **Walk through the first test case together.** This calibrates expectations for detail level, how to record results, and what constitutes a pass vs. fail.
- **Keep a live issue log.** A shared spreadsheet or board visible to all testers prevents duplicate reports and shows progress.
- **Time-box the session.** Two to three hours is the maximum productive window. Schedule breaks and a debrief at the end.
- **Encourage testers to go off-script.** Structured test cases catch expected scenarios; exploratory testing catches the unexpected ones.
- **Record blockers immediately.** If a tester is blocked, the coordinator should reassign them to another test case while the issue is investigated.

### After the Session
- **Debrief within 24 hours.** Capture fresh impressions while they are still vivid.
- **Classify every issue** using the Blocker / Major / Minor / Enhancement categories.
- **Share results transparently.** A summary sent to all participants builds trust and shows that feedback is valued.

---

## 2. Stakeholder Communication Templates

### 2.1 UAT Kickoff Email

```
Subject: UAT Session — [Project Name] — [Date]

Hi [Team / Stakeholder Names],

We are ready to begin User Acceptance Testing for [Project Name].

WHAT: We will be testing [brief scope description — e.g., the new invoice
management workflow and reporting dashboard].

WHEN: [Date], [Time] — [Time] ([Timezone])

WHERE: [Location / video link / environment URL]

WHAT TO BRING: Your laptop and any edge-case scenarios you want to
explore. Test accounts and credentials will be provided.

BEFORE THE SESSION: Please review the attached UAT plan so you are
familiar with the test cases assigned to you.

If you have questions or cannot attend, reply to this email by [deadline].

Thanks,
[Your Name]
```

### 2.2 UAT Feedback Form

Provide this template (or a digital equivalent) to every tester:

```
Test Case ID: UAT-___
Tester Name: _______________
Date: _______________

Steps Performed:
1.
2.
3.

Expected Result:


Actual Result:


Status:  [ ] PASS   [ ] FAIL   [ ] BLOCKED

If FAIL or BLOCKED:
  - Description of the issue:
  - Screenshots / screen recordings attached?  [ ] Yes  [ ] No
  - Severity:  [ ] Blocker  [ ] Major  [ ] Minor
  - Reproducible?  [ ] Always  [ ] Sometimes  [ ] Once

Additional Notes:

```

### 2.3 Stakeholder Sign-off Template

```
PROJECT: [Project Name]
UAT CYCLE: [Cycle Number / Date Range]

I confirm that:

  [x] All critical user journeys have been tested and verified.
  [x] No blocker-level issues remain unresolved.
  [x] The product meets the acceptance criteria defined in the PRD.
  [ ] The following known issues are accepted for post-launch fix:
      - [Issue ID]: [Brief description]
      - [Issue ID]: [Brief description]

Stakeholder Name: _______________
Role: _______________
Date: _______________
Signature: _______________
```

---

## 3. Common UAT Pitfalls

### Testing Too Late
UAT should not be the first time stakeholders see the product. If it is, expect a flood of feedback that belongs in earlier phases. Mitigation: include stakeholders in demos throughout development so UAT focuses on validation, not discovery.

### Wrong Testers
Developers testing their own work is not UAT. Stakeholders who will not use the product daily are poor proxies. Select testers who represent actual end users and understand the business workflows being tested.

### Unclear Scope
Without a written scope, testers will report issues on features that are not part of the release. This wastes time and creates frustration. Always distribute a scope document before testing begins.

### No Exit Criteria
If you do not define what "done" looks like, UAT drags on indefinitely. Agree on exit criteria up front: what percentage of test cases must pass, what severity levels block release, and who has final sign-off authority.

### Treating All Feedback Equally
Not every issue is a blocker. Without a triage process, teams either fix everything (delaying the release) or ignore everything (shipping broken software). Use the severity classification consistently.

### Insufficient Environment Parity
If the UAT environment differs significantly from production (different data, missing integrations, different configurations), test results are unreliable. Invest time in environment parity — it pays for itself in fewer production surprises.

---

## 4. Managing Feedback and Prioritization

### The Triage Process
1. **Collect** all feedback in a single location (issue tracker, shared spreadsheet, or the UAT plan itself).
2. **Deduplicate** — multiple testers often report the same issue differently.
3. **Classify** each unique issue:
   - **Blocker**: The feature does not work at all, or produces incorrect results that would cause real harm. Release cannot proceed.
   - **Major**: The feature works but with significant friction or a poor user experience. Should be fixed before release if schedule allows.
   - **Minor**: Cosmetic issues, typos, or minor inconveniences. Can ship and fix in the next iteration.
   - **Enhancement**: A new idea or improvement suggestion. Out of scope for this release — add to the product backlog.
4. **Assign** each blocker and major issue to a developer with a target resolution date.
5. **Re-test** fixed issues before moving to sign-off.

### Prioritization Principles
- Fix blockers first, always.
- For majors, ask: "Would a real user abandon the workflow because of this?" If yes, treat it as a blocker.
- Do not let the volume of minor issues distract from resolving blockers.
- Record enhancement requests. Stakeholders feel heard when they see their ideas logged, even if they are deferred.

---

## 5. UAT Environment Best Practices

### Environment Checklist
- [ ] Infrastructure mirrors production (same OS, runtime versions, database engine)
- [ ] Configuration uses production-equivalent settings (feature flags, rate limits, timeouts)
- [ ] Test data is representative and sufficient for all test cases
- [ ] All third-party integrations are connected (use sandboxed or staging endpoints where available)
- [ ] SSL / TLS is configured (tests should reflect real security behavior)
- [ ] Monitoring and logging are active (helps diagnose failures quickly)
- [ ] Environment is isolated from development — no code deployments during UAT without notification

### Data Management
- Use anonymized copies of production data when possible. Synthetic data often misses edge cases that real data exposes.
- Pre-seed the environment with data that covers both happy paths and known edge cases.
- Document any data setup steps so the environment can be rebuilt if it becomes corrupted during testing.

### Access Control
- Create dedicated test accounts for each tester. Do not share credentials.
- Ensure testers have the correct permissions for the roles they are testing.
- Remove test accounts after UAT completes.

---

## 6. Handling Disagreements Between Stakeholders

Disagreements during UAT are normal and healthy. They surface when different stakeholders have different expectations, priorities, or interpretations of requirements.

### Prevention
- Ensure the PRD and acceptance criteria are reviewed and agreed upon before UAT begins. Most disagreements stem from ambiguous requirements.
- Involve all key stakeholders in the UAT planning phase so there are no surprises about scope.

### Resolution Framework
1. **Restate the requirement.** Go back to the PRD and read the relevant user story or acceptance criterion aloud. Often the written requirement resolves the disagreement.
2. **Identify the user impact.** Frame the discussion around the end user, not internal preferences. Ask: "What would the user expect to happen here?"
3. **Use data if available.** Analytics, support tickets, or user research can break subjective deadlocks.
4. **Escalate with a time limit.** If the group cannot agree in 10 minutes, escalate to the product owner or project sponsor. Do not let one disagreement stall the entire session.
5. **Document the decision.** Record what was decided, who decided it, and the rationale. This prevents the same disagreement from recurring.

### When Stakeholders Reject the Feature
If a stakeholder believes the implementation does not match the requirement, and the team disagrees:
- Log it as a formal issue with the stakeholder's name and rationale.
- The product owner makes the final call on whether it is a blocker or accepted as-is.
- If deferred, include it explicitly in the sign-off template under "known issues accepted for post-launch fix."
