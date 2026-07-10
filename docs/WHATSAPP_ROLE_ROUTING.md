# WhatsApp Role Routing

Titan Nova loads the role router before `Gateway.js`. `KALYAN_ADMIN_GROUP`, `KALYAN_INTEL_GROUP`, and `KALYAN_RESULT_GROUP` are WhatsApp group identifiers; they do **not** restrict routing to the KALYAN market.

## Global role mapping

| Role | UI field / env fallback | Behaviour |
|---|---|---|
| Entry Target | `entryTargets` / `KALYAN_ADMIN_GROUP` | All valid VIP market entry cards are accepted only from this group. |
| Bookie Target | `bookieTargets` / `KALYAN_ADMIN_GROUP` | Withdrawal, payment, bookie, and admin alerts are routed here. |
| Schedule Target | `scheduleTargets` / `KALYAN_INTEL_GROUP` | Daily ANK, JODI, and PENEL intel for every market is routed only here. |
| Result Target | `resultTargets` / `KALYAN_RESULT_GROUP` | Open/close declarations for every market are routed only here. |
| Forward Target | `forwardTargets` / `BOOKIE_LOAD_REPORT_GROUP` | Load report delivery is routed only here. |

## UI control

After `nova restart`, use either URL:

```text
http://127.0.0.1:5000/role_router
http://127.0.0.1:3000/role_router
```

The main master dashboard also shows a floating gear control above the bottom navigation. It opens the same role-router page through the Flask proxy.

The page provides controls for:

- Enable/disable global role routing.
- Entry, Bookie, Schedule, Result, and Forward group JIDs.
- Detected WhatsApp groups from the Gateway target cache.
- One-tap assignment of a detected group to a role.
- Clearing saved UI targets to return to `.env` fallback values.

Saved values use the dedicated Firebase path `titan_role_router/targets`. This path is outside `titan_master_data`, so the Flask Manual Overwrite root PUT cannot delete or roll back role-router settings. Old `marketRoleTargets/KALYAN` values are migrated automatically once.

## Environment fallback

Use WhatsApp group JIDs, not display names or invite links:

```dotenv
ROLE_ROUTER_ENABLED=1
KALYAN_ADMIN_GROUP=120363012345678901@g.us
KALYAN_INTEL_GROUP=120363012345678902@g.us
KALYAN_RESULT_GROUP=120363012345678903@g.us
BOOKIE_LOAD_REPORT_GROUP=120363012345678904@g.us
```

Multiple JIDs may be comma-separated. When a UI field is empty, the corresponding `.env` value is used. When both are empty, existing Gateway behaviour remains active for that role.

## Safety behaviour

- Entry cards from outside the configured Entry Target are ignored before parsing.
- Result messages do not fall back to Forward targets when Result Target is configured.
- Duplicate forced deliveries are suppressed for 30 seconds.
- Manual root overwrite mode remains unchanged.
- The strict auto-result lifecycle remains unchanged: close is accepted only after a matching open exists.

## Deployment

```bash
nova update
nova restart
```

For direct Gateway execution:

```bash
node --require ./gateway/roleRouter.js --require ./gateway/roleRouterUi.js Gateway.js
```
