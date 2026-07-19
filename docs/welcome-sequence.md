# Welcome sequence (Sprint 3)

Five-email drip that fires after a lead confirms via `GET /leads/confirm`.
Delivered by SendGrid, driven by an external scheduler (Cloud Scheduler in
prod) hitting `POST /leads/sequence/tick`.

## Schedule

Days from confirmation:

| Step | Delay from previous | Cumulative day | SendGrid template env |
|-----:|--------------------:|---------------:|------------------------|
| 1    | 2                   | 2              | `SENDGRID_TPL_SEQ_1`  |
| 2    | 3                   | 5              | `SENDGRID_TPL_SEQ_2`  |
| 3    | 4                   | 9              | `SENDGRID_TPL_SEQ_3`  |
| 4    | 5                   | 14             | `SENDGRID_TPL_SEQ_4`  |
| 5    | 5                   | 19             | `SENDGRID_TPL_SEQ_5`  |

Interval constants live in `backend/app/api/leads.py::SEQUENCE_INTERVALS_DAYS`.
Edit them there — the tick endpoint reads the same list.

## Endpoint

```
POST /leads/sequence/tick
Header: X-Scheduler-Token: <SCHEDULER_TOKEN env var>

→ 200 {"processed": N, "completed": M}
→ 401 if header missing or wrong
→ 503 if SCHEDULER_TOKEN is unset (fail-closed — never accept anon)
```

Selects up to 100 due leads with `FOR UPDATE SKIP LOCKED`, sends the next
step for each, advances `sequence_step`, and reschedules `next_send_at`.
When `sequence_step` reaches 5, `next_send_at` is cleared and the lead is
done.

Idempotent to concurrent runs: two parallel workers won't send the same step
twice because of SKIP LOCKED. Idempotent to retries within a single run: the
`send_sequence_step` service is safe to call multiple times (SendGrid dedupes
templated sends within a short window), and we advance state whether the send
returned success or not — a permanent SendGrid failure (bad address,
suppressed) would otherwise wedge the queue.

## Prod (Cloud Scheduler)

Assumes the backend is deployed as Cloud Run service `tih-backend` with a
public URL. Set the SendGrid template IDs + scheduler token as env vars on the
service first:

```bash
gcloud run services update tih-backend \
  --set-env-vars \
    SENDGRID_API_KEY=$SENDGRID_API_KEY,\
SENDGRID_FROM_EMAIL=hello@theincurablehumanist.com,\
SENDGRID_FROM_NAME='Denise Rodriguez Dao',\
SENDGRID_TPL_CONFIRM=d-xxx,\
SENDGRID_TPL_MAGNET=d-xxx,\
SENDGRID_TPL_SEQ_1=d-xxx,\
SENDGRID_TPL_SEQ_2=d-xxx,\
SENDGRID_TPL_SEQ_3=d-xxx,\
SENDGRID_TPL_SEQ_4=d-xxx,\
SENDGRID_TPL_SEQ_5=d-xxx,\
SCHEDULER_TOKEN=$(openssl rand -hex 32)
```

Then create the scheduler job. Runs every 15 minutes — worst case a step is
15 min late.

```bash
BACKEND_URL=$(gcloud run services describe tih-backend --format='value(status.url)')
SCHEDULER_TOKEN=$(gcloud run services describe tih-backend \
  --format='value(spec.template.spec.containers[0].env)' | grep -o 'SCHEDULER_TOKEN=[^,]*' | cut -d= -f2)

gcloud scheduler jobs create http tih-welcome-sequence-tick \
  --schedule='*/15 * * * *' \
  --uri="$BACKEND_URL/leads/sequence/tick" \
  --http-method=POST \
  --headers="X-Scheduler-Token=$SCHEDULER_TOKEN" \
  --attempt-deadline=60s \
  --time-zone='UTC' \
  --location=us-central1
```

Cost: `$0.10/job/month` on Cloud Scheduler. Cloud Run within free tier.

## Local dev

`make tick` sends a single tick against the local backend.

```bash
export SCHEDULER_TOKEN=dev-tick-token
docker compose up -d backend  # rebuild if you changed leads.py
make tick
```

To test end-to-end without waiting 2 days: after confirming a lead, manually
bump `next_send_at`:

```sql
UPDATE lead_capture
SET next_send_at = NOW() - interval '1 minute', sequence_step = 0
WHERE email = 'your-test@example.com';
```

Then `make tick` will pick it up, send step 1, and reschedule `next_send_at`
for step 2 three days out. Bump again, tick again, etc.
