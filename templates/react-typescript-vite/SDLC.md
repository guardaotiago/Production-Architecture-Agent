# SDLC Checklist — React + TypeScript + Vite

## Phase 1: Requirements & Planning
- [ ] PRD written with component breakdown
- [ ] User stories for each page/feature
- [ ] UI/UX wireframes or mockups
- [ ] Accessibility requirements defined (WCAG level)
- [ ] Browser/device support matrix defined
- [ ] Stakeholder sign-off

## Phase 2: Development & Git
- [ ] Vite project initialized with TypeScript
- [ ] ESLint + Prettier configured
- [ ] Component library chosen (or custom design system)
- [ ] State management approach decided (React Query, Zustand, Context)
- [ ] Routing set up (React Router)
- [ ] Pre-commit hooks installed (lint, format, type check)
- [ ] Git branching strategy documented

## Phase 3: CI/CD Pipeline
- [ ] GitHub Actions workflow: lint → type-check → test → build
- [ ] Build artifacts uploaded
- [ ] Preview deployments for PRs (Vercel/Netlify)
- [ ] Bundle size tracking
- [ ] Lighthouse CI for performance budgets

## Phase 4: QA Testing
- [ ] Unit tests with Vitest (components, hooks, utils)
- [ ] Integration tests for page-level flows
- [ ] E2E tests with Playwright (critical user journeys)
- [ ] Accessibility testing (axe-core)
- [ ] Visual regression tests (optional)
- [ ] Coverage ≥ 80%

## Phase 5: User Acceptance Testing
- [ ] UAT environment deployed (staging URL)
- [ ] Stakeholders briefed on test scope
- [ ] All user journeys manually verified
- [ ] Cross-browser testing completed
- [ ] Mobile responsiveness verified
- [ ] Sign-off obtained

## Phase 6: Production Deployment
- [ ] Production build optimized (code splitting, tree shaking)
- [ ] Environment variables configured
- [ ] CDN/hosting configured (Vercel, Cloudflare Pages, S3+CF)
- [ ] Custom domain + SSL
- [ ] Deployment runbook documented
- [ ] Rollback: redeploy previous build

## Phase 7: Monitoring & SRE
- [ ] Error tracking (Sentry)
- [ ] Analytics (Plausible, PostHog, or GA4)
- [ ] Core Web Vitals monitoring
- [ ] Uptime monitoring
- [ ] Alert on error rate spike
