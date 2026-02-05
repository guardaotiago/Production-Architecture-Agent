# SDLC Checklist — Next.js + TypeScript

## Phase 1: Requirements & Planning
- [ ] PRD written with page/route breakdown
- [ ] User stories for each page and feature
- [ ] UI/UX wireframes or mockups
- [ ] SEO requirements defined
- [ ] API routes specification (if using API routes)
- [ ] Stakeholder sign-off

## Phase 2: Development & Git
- [ ] Next.js project initialized (App Router)
- [ ] TypeScript strict mode enabled
- [ ] ESLint + Prettier configured
- [ ] Component structure defined (app/, components/, lib/)
- [ ] State management approach decided
- [ ] Database/ORM set up (if applicable — Prisma, Drizzle)
- [ ] Pre-commit hooks installed
- [ ] Git branching strategy documented

## Phase 3: CI/CD Pipeline
- [ ] GitHub Actions: lint → type-check → test → build
- [ ] Vercel/hosting deployment preview for PRs
- [ ] Bundle analysis configured
- [ ] Lighthouse CI for performance budgets
- [ ] Dependency vulnerability scanning

## Phase 4: QA Testing
- [ ] Unit tests with Jest/Vitest (components, utils, API routes)
- [ ] Integration tests for page rendering (React Testing Library)
- [ ] E2E tests with Playwright (critical user journeys)
- [ ] API route testing
- [ ] Accessibility testing (axe-core)
- [ ] Coverage ≥ 80%

## Phase 5: User Acceptance Testing
- [ ] UAT environment deployed (Vercel preview)
- [ ] All pages and flows manually verified
- [ ] SEO validation (meta tags, OG images, sitemap)
- [ ] Cross-browser and mobile testing
- [ ] Performance audit (Core Web Vitals)
- [ ] Sign-off obtained

## Phase 6: Production Deployment
- [ ] Production build verified (next build passes)
- [ ] Environment variables configured in hosting
- [ ] Edge/serverless function regions configured
- [ ] Custom domain + SSL
- [ ] ISR/SSG caching strategy configured
- [ ] Deployment runbook documented
- [ ] Rollback: redeploy previous Vercel deployment

## Phase 7: Monitoring & SRE
- [ ] Error tracking (Sentry, Next.js instrumentation)
- [ ] Analytics (Vercel Analytics, PostHog)
- [ ] Core Web Vitals monitoring
- [ ] API route latency monitoring
- [ ] Uptime monitoring
- [ ] Alert on error rate or performance regression
