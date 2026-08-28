# SDD ledger — plan: /Users/tomasvazquez/Develop/docs/superpowers/plans/2026-08-27-marca-mi-notebook.md
Task 1 fix round 1: implementer rewrote pyproject.toml/.env.example/config.py/database.py/app.py for Supabase Postgres + psycopg2 (commit 48f38d9). Implementer also corrected plan bug: PyPI package is `mercadopago`, not `mercado-pago`.
Ruling: accept `mercadopago` package name over plan's `mercado-pago` — plan text is wrong, `mercado-pago` doesn't exist on PyPI — cost if wrong: none, verified against PyPI.
Task 1 re-review round 1: dispatched, awaiting verdict.
Task 1 re-review round 1: FAIL — sqlalchemy still in pyproject.toml, supabase dep missing, DATABASE_URL missing from .env.example. database.py/config.py/app.py OK.
Task 1 fix round 2: dispatched to implementer.
Task 1 fix round 2: implementer hit spend limit mid-fix with all edits done but uncommitted; coordinator finished verification + commit b1d51b3.
Ruling: coordinator adjudicated re-review round 2 inline instead of dispatching — the three findings are mechanical (grep-verifiable: sqlalchemy removed, supabase>=2.0 added, DATABASE_URL in .env.example/config.py/database.py) and imports pass with example env — cost if wrong: a missed dep surfaces at Task 2's first uv run.
Ruling: implementer dispatches from here on use haiku (cheap tasks) or fable (session model) — sonnet-5 hit monthly spend limit — cost if wrong: none, model choice only.
Task 1: complete (commits f97fc49, 48f38d9, b1d51b3)
Task 2 review: spec PASS, quality NEEDS_CHANGES — CREATE TYPE not idempotent (critical), cwd-relative migration paths (important), bare except in seed_db (minor).
Ruling: rejected reviewer's suggested `CREATE TYPE IF NOT EXISTS` — Postgres doesn't support it; mandated DO-block duplicate_object idiom instead, and ON CONFLICT DO NOTHING seeds over try/except — cost if wrong: syntax error at first real migration run, immediately visible.
Task 2 fix round 1: dispatched.
Task 2 fix round 1: commit 6051ee1 — DO-block enums, Path(__file__)-relative migrations, ON CONFLICT (position_name) DO NOTHING seed (position_name is UNIQUE, valid target).
Ruling: coordinator adjudicated re-review inline — all three findings mechanically confirmed in the diff itself — cost if wrong: surfaces at first real startup, loud.
Task 2: complete (commits 642606b, 6051ee1)
Task 3 review: spec FAIL (1 critical), quality NEEDS_CHANGES.
Ruling: reviewer's critical (missing routes/__init__.py) is a false positive — file exists since Task 1 commit f97fc49, outside this task's diff — cost if wrong: none, verified with git log + ls.
Task 3 fix: coordinator applied one-line tie-break fix inline (ORDER BY amount_ars DESC, id ASC — earliest paid wins ties).
Ruling: N+1 query pattern (21 queries for 10 spots) parked — MVP scale with 5s polling makes it irrelevant; consolidate to one JOIN if load ever matters — cost if wrong: latency on /api/spots, visible in monitoring.
Ruling: minors parked — from_attributes harmless; absolute imports match the existing backend convention (config/database also absolute).
Task 3: complete (commits 189bb1d, tie-break fix)
Task 4 review: spec PASS, quality NEEDS_CHANGES — fake sanitization (critical), 200-only status check, unused base64 import, generic Exception.
Task 4 fix: coordinator applied inline (commit c652d1f) — basename+regex sanitization (verified against path traversal), accept 200/201, StorageUploadError class, switched `from ..config` relative import to absolute (matches backend convention; removed stray backend/__init__.py the implementer added). Import + sanitization check passed.
Ruling: fixed the relative-import bug beyond the review findings — `from ..config` would fail when Task 5 imports services.storage from backend/ cwd — cost if wrong: none, import test passes.
Task 4: complete (commits c956c12, c652d1f)
Task 5 review: spec FAIL, quality NEEDS_CHANGES — async route calls run_until_complete sync wrapper (crashes in running loop), orphaned pending_payment row if MP preference fails, no file validation on public money endpoint, dead uuid var.
Ruling: keep bid_id in response JSON despite brief showing only preference_id/checkout_url — harmless extra field the frontend can use — cost if wrong: none.
Task 5 fix round 1: dispatched.
Task 5 fix round 1: commit 71c7336 — verified in diff: await upload directly + sync wrapper deleted, orphan DELETE on MP failure, content-type/5MB validation, dead uuid removed.
Ruling: coordinator adjudicated re-review inline — all findings mechanically confirmed in the diff — cost if wrong: caught in Task 12 tests or E2E.
Task 5: complete (commits ba397a8, 71c7336)
Task 6 review (fable): spec FAIL, quality NEEDS_CHANGES. Locking core PASS (traps 1/2/4/6). Criticals: mail.py `from resend import Resend` ImportError (app can't boot — bug inherited from the PLAN's own snippet); external_reference never set to bid id + webhook reads nonexistent preference_id field → every webhook a no-op. Importants: MP fetch failure returns 200 (payment dropped, MP never retries), transaction_amount never validated, mismatch-branch payment never refunded, outbid email sent even when refund failed.
Ruling: plan defect — plan's mail.py snippet uses a nonexistent `Resend` class; mandated resend 2.x module API (resend.api_key + resend.Emails.send) — cost if wrong: import error, instantly visible.
Task 6 fix round 1: dispatched (7-point fix list incl. Task 5's create_preference signature change to carry bid_id as external_reference).
Task 6 fix round 1: commit 0278950 — findings 1-6 resolved per fable re-review, but the fix introduced 4 new defects (un-awaited request.body method object → all webhooks 400; int payment id vs VARCHAR column; loose "refunded in str(e)" heuristic; prev_payment NameError in handler).
Task 6 fix round 2: coordinator applied inline (commit e4b6a98) — async def + await request.json() with blocking engine calls via run_in_threadpool, str(payment id), "already refunded" exact-phrase match only, prev_payment fetched before try. App import + engine smoke test pass.
Ruling: re-review's minor residuals parked — int() truncation accepts centavo overpayment (harmless); duplicate-payment refund failure is log-only (rare; admin sees MP panel); refund-then-commit-failure window logged (MP rejects double full refunds) — cost if wrong: admin manually reconciles from logs.
Task 6: complete (commits a80e55d, 0278950, e4b6a98)
Task 7 review: spec FAIL, quality NEEDS_CHANGES — password taken as query param (leaks in URLs/logs), MP refund on reject left as TODO (bids marked refunded without refunding), plain == hash compare, deprecated utcnow. Token gen (secrets.token_urlsafe) and route protection PASS.
Task 7 fix round 1: dispatched (password → body model, implement refund with refund_failed fallback, compare_digest).
Task 7 fix round 1: commit 1af2971 — verified in diff: LoginRequest body model, real MP refund with already-refunded/refund_failed handling, compare_digest, timezone-aware datetimes.
Ruling: coordinator adjudicated re-review inline — all findings confirmed in diff — cost if wrong: caught in E2E (Task 14).
Task 7: complete (commits 594424e, 1af2971)
Task 8 review: spec PASS (1 critical conflict), quality APPROVED. Build independently verified.
Ruling: brief's Bid type included bidder_email but the privacy constraint and Task 3's actual API exclude it — spec (no email leaks) beats plan text; removed field inline, build passes (commit 187c280) — cost if wrong: a TS compile error in the admin page, trivial.
Task 8: complete (commits 31987f2, 187c280)
Task 9 review: spec FAIL, quality NEEDS_CHANGES — closSpot typo, manual multipart Content-Type (breaks boundary), login token never sent as session_token cookie (all admin calls would 401).
Task 9 fix: coordinator applied inline (commit 14be935) — closeSpot rename, axios auto-boundary, document.cookie set on login (samesite=lax, 24h, matching backend session TTL). Build passes.
Ruling: overlapping-poll/AbortController gap parked — 5s interval vs local API, overlap needs a >5s response; add stale-guard if ever observed — cost if wrong: transient flicker.
Task 9: complete (commits dbac107, 14be935)
Task 10 review: spec PASS, quality APPROVED — clean. Minors noted (no client-side file validation, empty onRefresh) match brief; backend validates.
Task 10: complete (commit c4f5b77)
Task 11 review: spec FAIL, quality NEEDS_CHANGES — no 401 auto-logout (stale in-memory sessions strand the UI), no confirm() on close/reject (irreversible money actions), token-prop confusion.
Task 11 fix round 1: dispatched.
Task 11 fix round 1: commit 77c555f — 401→onLogout in all three catch blocks, confirm() on close/reject, cookie-auth comment. Build passes. Coordinator adjudicated inline (11 matching added lines in diff).
Task 11: complete (commits 3c7b99f, 77c555f)
Task 12 review (fable): spec PASS w/ findings, quality NEEDS_CHANGES — 24/24 pass independently verified, but swap test never asserts persisted statuses (swapping 'paid'/'outbid_refunded' stays green — critical), mp_payment_id retry branch untested, 3 tautological assertions, dead mock_db fixture, TestRowLocking is SQL-string smoke only.
Ruling: mocked-cursor approach accepted for MVP (no live DB in env); true two-connection serialization test deferred to DB-gated CI — must be labeled honestly, not sold as locking coverage — cost if wrong: a locking regression ships undetected until E2E.
Task 12 fix round 1: dispatched.
Task 12 fix round 1: commit dc904b1 — status-UPDATE assertions, 2 retry-branch tests, tautologies tightened, dead fixture removed. 26/26 pass, independently re-run by coordinator.
Task 12: complete (commits 423467f, dc904b1)
Task 13: complete (no new commits)
Ruling: Task 13's brief is stale — every deliverable already exists in stronger form (bid_engine calls mp_service.create_refund for real at 5 sites vs the brief's log-only stub; mail wired with refund gating; AdminLogin wired to adminAPI; auth rides session_token cookie). Executing the brief verbatim would REGRESS refunds to a stub. Verified by grep — cost if wrong: none, the final whole-branch review covers integration.
Task 14: parked — manual E2E checklist requiring live Supabase Postgres + MP sandbox credentials that only the human has; no live services in this environment.
Ruling: hand Task 14's checklist to the user as the post-setup verification step — cost if wrong: none, it's inherently human-executed.
Task 15 review: coordinator reviewed inline (1.9KB diff) — implementer dropped DATABASE_URL from .env.example (regressing the Task 1 fix), set production URLs as local template defaults, and forced `npm run build` in a pnpm project. Fixed inline; JSON parses, app imports (commit follows 6cc92df).
Task 15: complete (commits 6cc92df + coordinator fix)
Final whole-branch review (fable): FIX_FIRST. Blockers: C1 cookie auth can't cross Vercel origins (admin dead), C2 CREATE INDEX not idempotent (every cold start after first crashes boot), C3 admin spots response shape mismatch, I1 pay-after-reject keeps money silently, I3 MP back_urls → blank pages, I4 no SPA rewrite (all non-root URLs 404 in prod). Plus I2 (no reject button for paid bids), I5 (in-memory sessions on serverless), I6 (unowned mail domain), I7 (mismatch branch lies about refund), I9 (webhook ignores closed spots), M1-M7.
Final fix pass: single dispatch (fable) covering C1-C3, I1-I9 (minus parked), M1-M3. Remaining minors M4-M7 to adjudicate after re-review.
Final fix pass: commit 66a182b — all 14 findings resolved (fable re-review verified each with evidence; fuzzed the HMAC tokens live).
Re-review residual: verify_session TypeError→500 on non-ASCII garbage token — coordinator fixed inline (byte-compare, commit 28604e1), verified with 7 garbage tokens incl. 'ñ'; 30/30 tests pass.
Ruling: remaining minors parked — M4 MERCADOPAGO_SANDBOX decorative (spec itself calls the USD toggle decorative; test credentials control sandbox), M5 WEBHOOK_SECRET now USED as the HMAC session key (no longer dead), M6 thermometer copy cosmetic, M7 on_event deprecation cosmetic, I8 bid-history table deferred to a UI polish pass — cost if wrong: cosmetic/UX only, no money or boot risk.
FINAL REVIEW: PASS (all blockers cleared). Branch complete at 28604e1: 30 commits, backend+frontend+tests+deploy config.
