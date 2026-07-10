# WhatsApp Role Routing

Titan Nova loads the role router before `Gateway.js`. The router is a runtime overlay: it does not persist environment-derived role targets during Firebase root PUT operations, so the existing manual overwrite model remains unchanged.

## KALYAN mapping

| Role | Environment key | Behaviour |
|---|---|---|
| Entry Target | `KALYAN_ADMIN_GROUP` | KALYAN VIP entry cards are accepted only from this group. |
| Bookie Target | `KALYAN_ADMIN_GROUP` | Withdrawal, payment, bookie, and admin alert messages are routed here. |
| Schedule Target | `KALYAN_INTEL_GROUP` | KALYAN ANK, JODI, and PENEL scheduled intel is routed only here. |
| Result Target | `KALYAN_RESULT_GROUP` | KALYAN open/close declarations are routed only here. |
| Forward Target | `BOOKIE_LOAD_REPORT_GROUP` | Load report delivery is routed only here. |

Use WhatsApp group JIDs, not display names or invite links:

```dotenv
ROLE_ROUTER_ENABLED=1
KALYAN_ADMIN_GROUP=120363012345678901@g.us
KALYAN_INTEL_GROUP=120363012345678902@g.us
KALYAN_RESULT_GROUP=120363012345678903@g.us
BOOKIE_LOAD_REPORT_GROUP=120363012345678904@g.us
```

Multiple JIDs may be comma-separated. When a key is empty, that role keeps the existing Gateway behaviour.

## Safety behaviour

- Non-KALYAN markets keep their existing target behaviour.
- KALYAN entry cards received outside `KALYAN_ADMIN_GROUP` are ignored before the entry parser runs.
- Result messages do not fall back to Forward targets when the role router is configured.
- Duplicate forced deliveries are suppressed for 30 seconds.
- The strict auto-result lifecycle remains unchanged: close is still accepted only after a matching open exists.

## Deployment

The normal command loads the router automatically:

```bash
nova restart
```

For direct execution, use:

```bash
node --require ./gateway/roleRouter.js Gateway.js
```
