# Risk Scoring - Quick Reference

## Risk Scoring Formula

### Expiry-Based Baseline (Primary)
- **Expired (≤ 0 days)**: 100 → 🔴 CRITICAL
- **< 7 days**: 90 → 🔴 CRITICAL
- **< 30 days**: 75 → 🟠 HIGH
- **< 90 days**: 50 → 🟡 MEDIUM
- **≥ 90 days**: 0 → 🟢 LOW

### Penalties Added (Secondary)
- **Weak key (< 2048 bits)**: +40
- **Self-signed**: +25
- **Weak algorithm (MD5/SHA1)**: +20

### Level Mapping
| Score | Level | Action | Color |
|-------|-------|--------|-------|
| 76-100 | CRITICAL | Immediate | 🔴 |
| 51-75 | HIGH | Within week | 🟠 |
| 26-50 | MEDIUM | Within month | 🟡 |
| 0-25 | LOW | Monitor | 🟢 |

## Example Scores

| Certificate | Score | Reason | Level |
|---|---|---|---|
| Expired, 2048-bit RSA | 100 | Expired | CRITICAL 🔴 |
| Expires in 3 days, 2048-bit RSA | 90 | < 7 days | CRITICAL 🔴 |
| Expires in 20 days, 2048-bit RSA | 75 | < 30 days | HIGH 🟠 |
| Expires in 60 days, 2048-bit RSA | 50 | < 90 days | MEDIUM 🟡 |
| Expires in 200 days, 1024-bit RSA | 40 | Weak key | MEDIUM 🟡 |
| Expires in 200 days, 2048-bit RSA | 0 | Long valid | LOW 🟢 |
| Valid for 200 days, self-signed | 25 | Self-signed | LOW 🟢 |

## API Endpoints

### View Risk Configuration
```
GET /api/risk/config/
```
Returns current thresholds (all users)

### Update Risk Configuration
```
PATCH /api/risk/config/
```
Updates thresholds (superadmin only)

### Test Risk Calculation
```
POST /api/risk/analyze/
Body: {
  "valid_to": "2026-12-31T23:59:59Z",
  "key_length": 2048,
  "is_self_signed": false,
  "algorithm": "sha256WithRSAEncryption"
}
```

## Configuration Fields (Adjustable)

```
critical_expiry_days: 7       # < 7 days = CRITICAL
high_expiry_days: 30          # < 30 days = HIGH
medium_expiry_days: 90        # < 90 days = MEDIUM
weak_key_bits: 2048           # < 2048 = weak penalty
self_signed_penalty: 25       # Self-signed = +25
weak_algorithm_penalty: 20    # MD5/SHA1 = +20
critical_threshold: 75        # Score > 75 = CRITICAL
high_threshold: 50            # Score > 50 = HIGH
medium_threshold: 25          # Score > 25 = MEDIUM
```

## Files

- **Service**: `apps/risk_engine/services.py`
- **Config Model**: `apps/risk_engine/models.py`
- **API Views**: `apps/risk_engine/views.py`
- **API Routes**: `apps/risk_engine/urls.py`
- **Certificate Integration**: `apps/certificates/services.py`, `internal_service.py`

## Key Features

✅ **Deterministic** - Same inputs always produce same score
✅ **Transparent** - Full reasoning breakdown stored
✅ **Configurable** - Superadmin can adjust thresholds
✅ **Audited** - All config changes logged
✅ **Unified** - Same engine for public & internal certs
✅ **Penalties-Based** - Expiry is primary, others add penalties
✅ **Non-Editable** - Frontend cannot directly modify scores

## Next Phase: Frontend

Create components:
- `RiskBadge.jsx` - Display risk with emoji
- `RiskSummaryCards.jsx` - Risk stats
- `RiskDistributionChart.jsx` - Pie chart
- Integrate into certificate pages
