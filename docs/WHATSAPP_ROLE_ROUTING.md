# WhatsApp Role Routing

Titan Nova loads the role router before `Gateway.js`. The router is a runtime overlay: environment fallback values are not persisted during Firebase root PUT operations, so the existing manual overwrite model remains unchanged.

## KALYAN mapping

| Role | UI field / env fallback | Behaviour |
|---|---|---|
| Entry Target | `entryTargets` / `KALYAN_ADMIN_GROUP` | KALYAN VIP entry cards are accepted only from this group. |
| Bookie Target | `bookieTargets` / `KALYAN_ADMIN_GROUP` | Withdrawal, payment, bookie, and admin alert messages are routed here. |
| Schedule Target | `scheduleTargets` / `KALYAN_INTEL_GROUP` | KALYAN ANK, JODI, and PENEL scheduled intel is routed only here. |
| Result Target | `resultTargets` / `KALYAN_RESULT_GROUP` | KALYAN open/close declarations are routed only here. |
| Forward Target | `forwardTargets` / `BOOKIE_LOAD_REPORT_GROUP` | Load report delivery is routed only here. |

## UI control

Open the Gateway role-router UI after `nova restart`:

```text
http://127.0.0.1:3000/role_router
```

The page provides controls for:

- Enable/disable KALYAN role routing.
- Entry, Bookie, Schedule, Result, and Forward group JIDs.
- Detected WhatsApp groups from the Gateway target cache.
- Clearing saved UI targets to return to `.env` fallback values.

Saved UI values are stored under `marketRoleTargets/KALYAN` in Firebase and apply live to the running Gateway arrays. `.env` values remain fallback values when a UI field is empty.

## Environment fallback

Use WhatsApp group JIDs, not display names or invite links:

```dotenv
ROLE_ROUTER_ENABLED=1
KALYAN_ADMIN_GROUP=120363012345678901@g.us
KALYAN_INTEL_GROUP=120363012345678902@g.us
KALYAN_RESULT_GROUP=120363012345678903@g.us
BOOKIE_LOAD_REPORT_GROUP=120363012345678904@g.us
```

Multiple JIDs may be comma-separated. When a UI field and matching env key are both empty, that role keeps existing Gateway behaviour.

## Safety behaviour

- Non-KALYAN markets keep their existing target behaviour.
- KALYAN entry cards received outside the configured Entry Target are ignored before the entry parser runs.
- Result messages do not fall back to Forward targets when the role router is configured.
- Duplicate forced deliveries are suppressed for 30 seconds.
- The strict auto-result lifecycle remains unchanged: close is still accepted only after a matching open exists.

## Deployment

The normal command loads the router and UI automatically:

```bash
nova restart
```

For direct execution, use:

```bash
node --require ./gateway/roleRouter.js --require ./gateway/roleRouterUi.js Gateway.js
```
