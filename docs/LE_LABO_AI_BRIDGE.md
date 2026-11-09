# Le.Labo: provider shared in place

Owner request, 2026-11-09: use the same AI key as the tarot project in the private chef laboratory.

The production OPENAI_API_KEY is sensitive and non-exportable. The integration never reads or exports its value. A bounded server-to-server adapter uses it in its existing runtime. No new OpenAI credential or provider account is created.

Dependency map: owner-authenticated Sites recipe/catalogue route -> signed Le.Labo transport -> Vercel deployment protection -> dedicated HMAC handler -> atomic Redis replay/rate checks -> existing OpenAI key -> fixed Responses or Images API. Existing tarot and orchestration handlers are unchanged.

The Vercel automation bypass is provisioned for this server integration only, kept as a Sites secret and a runtime LE_LABO_BRIDGE_SECRET; it is also the HMAC signing secret. Never put it in a browser, URL, repository, report or log. Keep the existing all-deployment SSO policy. The caller only permits the canonical claudio-ebon.vercel.app origin; redirects fail closed.

HMAC covers method, path, timestamp, nonce and SHA-256 of the exact body. Timestamps expire in 120 seconds; Redis retains nonce fences for 360 seconds. Missing limiter means no paid call. Separate namespace le-labo:ai:v1; no catalogue/customer/recipe content enters Redis. Fixed UTC bucket ceilings: Responses 120/day and 30/hour; Images 20/day and 10/hour. Existing per-owner Sites limits also apply. These count attempts, not successful completions or budget guarantees; usage charges go to the existing OpenAI account.

Only gpt-6.1-sol structured Responses (store=false, max 14000 output tokens) and one JPEG from gpt-image-2.5-flare are accepted. No tools, arbitrary URLs, additional models, streaming, retries or account operations. Files must be inline PDF/image data. Maximum request/response JSON 4000000 bytes (below Vercel's function payload ceiling); large scanned pages/photos must be compressed before analysis. Images use medium quality and 75% JPEG compression to fit transport.

POST /api/laboratory-ai/health is signed and replay-fenced; it checks model access without generating paid content and returns only booleans. Error bodies from the provider are never forwarded because they can contain credential fragments. Health does not prove sufficient credit or successful generation. Verify an actual fictional structured recipe and image separately before declaring each capability operational.

Preserved: owner-only lab access, existing record isolation, human approval of prices/menu, unverified allergy status, drafts, original documents and existing photographs. The transport never changes records or sends messages. Provider results are validated by the lab's existing schemas.

Validation: tests/test_laboratory_ai.py covers HMAC expiry/tampering, replay/rate/outage closure, model and tool restrictions, inline files, safe errors and bounded image requests. Sites tests/ai-transport.test.mjs cross-checks the exact signature using Node's independent crypto implementation. Deployment and live verification results belong in the associated change log; do not infer live success from these mocked tests.

Rollback: revert the dedicated handler/config additions and the Sites transport commit, restore the preceding Sites version, then revoke the dedicated Vercel automation bypass and delete the Le.Labo environment variables. Do not rotate/delete the shared OpenAI key or existing Raffaello secrets.
