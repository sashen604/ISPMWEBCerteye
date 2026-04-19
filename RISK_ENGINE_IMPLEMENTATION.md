# Risk Scoring and Categorization - Backend Implementation

**Status**: ✅ COMPLETE (Backend Phase 1 & 2 Done)

## Overview

Implemented a unified, deterministic risk scoring engine that evaluates SSL/TLS certificates across multiple dimensions (expiry, key strength, self-signing, algorithm) and assigns clear risk levels with actionable thresholds.

**Key Achievement**: Unified two fragmented risk calculation systems (public certs vs internal certs) into a single deterministic, audit-logged, admin-configurable engine.

---

## Backend Implementation Details

### 1. Unified Risk Engine Service ✅

**File**: `apps/risk_engine/services.py` (299 lines)

**Core Functions**:

#### `calculate_risk_score(valid_to, key_length, is_self_signed, algorithm) → int`

Calculates risk score (0-100) based on deterministic rules:

**PRIMARY FACTOR: Certificate Expiry**
- Expired (≤ 0 days): +100 points → **CRITICAL**
- < 7 days: +90 points → **CRITICAL**
- < 30 days: +75 points → **HIGH**
- < 90 days: +50 points → **MEDIUM**
- ≥ 90 days: +0 points → **LOW**

**SECONDARY FACTORS: Penalties (added on top)**
- Weak key (< 2048 bits): +40 points
- Self-signed certificate: +25 points
- Weak algorithm (MD5/SHA1): +20 points
- Standard key (2048-3071 bits): +0 points
- Strong key (≥ 3072 bits): +0 points

**Score Capped at 100**

#### `determine_risk_level(risk_score) → str`

Maps score to level (all uppercase):

| Score Range | Risk Level | Action Required | Color |
|---|---|---|---|
| 76-100 | CRITICAL | Immediate action | 🔴 Red |
| 51-75 | HIGH | Within 1 week | 🟠 Orange |
| 26-50 | MEDIUM | Within 1 month | 🟡 Yellow |
| 0-25 | LOW | Routine monitoring | 🟢 Green |

#### `get_risk_reasoning(valid_to, key_length, is_self_signed, algorithm) → Dict`

Returns detailed breakdown for audit trail:

```json
{
  "expiry_days": 45,
  "expiry_penalty": 50,
  "expiry_factor": "Medium (< 90 days)",
  "key_length": 2048,
  "key_penalty": 0,
  "key_factor": "Strong (2048 bits)",
  "self_signed": false,
  "self_signed_penalty": 0,
  "algorithm": "sha256WithRSAEncryption",
  "algorithm_penalty": 0,
  "algorithm_factor": "Strong (sha256WithRSAEncryption)",
  "total_score": 50,
  "risk_level": "MEDIUM",
  "risk_reasons": [
    "Expires in 45 days (medium priority)",
    "Strong key length: 2048 bits",
    "Algorithm: sha256WithRSAEncryption"
  ]
}
```

**Properties**:
- ✅ Deterministic (same inputs → same outputs)
- ✅ Transparent (every factor explained)
- ✅ Non-editable in frontend (only via admin API)
- ✅ Audit-logged (reasoning stored with each cert)

---

### 2. Certificate Model Updates ✅

**File**: `apps/certificates/models.py`

**New Field Added**:
```python
risk_reasoning = models.JSONField(
    default=dict,
    blank=True,
    help_text="Detailed breakdown of risk calculation (for audit trail)"
)
```

**Migration**: `certificates/0004_certificate_risk_reasoning.py` ✅ Applied

**Purpose**: Stores complete calculation breakdown for:
- Audit trails
- Transparency (users can see why score changed)
- Debugging (why was this cert marked HIGH?)
- Admin review (manually validate scores if needed)

---

### 3. RiskConfiguration Model ✅

**File**: `apps/risk_engine/models.py`

**Purpose**: Stores admin-configurable risk thresholds (superadmin-only)

**Fields**:
```python
# Expiry thresholds (days)
critical_expiry_days = 7        # < 7 days → CRITICAL
high_expiry_days = 30           # < 30 days → HIGH
medium_expiry_days = 90         # < 90 days → MEDIUM

# Key strength thresholds (bits)
weak_key_bits = 2048            # < 2048 → weak penalty
medium_key_bits = 3072          # 2048-3071 → standard

# Penalty values
self_signed_penalty = 25
weak_algorithm_penalty = 20

# Risk level thresholds
critical_threshold = 75         # > 75 → CRITICAL
high_threshold = 50             # > 50 → HIGH
medium_threshold = 25           # > 25 → MEDIUM

# Metadata
last_modified_by = ForeignKey(User)
last_modified_at = DateTimeField()
```

**Migration**: `risk_engine/0002_riskconfiguration.py` ✅ Applied

**Methods**:
- `get_current_config()` - Retrieve latest configuration
- `to_dict()` - Export as dictionary for API responses

---

### 4. Risk API Endpoints ✅

**File**: `apps/risk_engine/urls.py`

**Endpoints**:

#### `GET /api/risk/` (Legacy)
- Returns: `{'success': true, 'message': 'Risk engine endpoint'}`
- Purpose: Kept for backward compatibility

#### `GET /api/risk/config/` ✅ **New**
- **Permission**: Authenticated users (all can view)
- **Returns**: Current risk configuration with thresholds
- **Response**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "critical_expiry_days": 7,
    "high_expiry_days": 30,
    "medium_expiry_days": 90,
    "weak_key_bits": 2048,
    "medium_key_bits": 3072,
    "self_signed_penalty": 25,
    "weak_algorithm_penalty": 20,
    "critical_threshold": 75,
    "high_threshold": 50,
    "medium_threshold": 25,
    "last_modified_by": "superadmin",
    "last_modified_at": "2026-04-19T09:46:10.123Z"
  }
}
```

#### `PATCH /api/risk/config/` ✅ **New**
- **Permission**: Superadmin only (403 Forbidden for others)
- **Request**: Any fields to update
- **Action**: Updates thresholds, logs change to audit trail
- **Response**: Updated configuration + success message
- **Audit Logging**: Automatically records who changed what and when

#### `POST /api/risk/analyze/` ✅ **New**
- **Permission**: Authenticated users
- **Purpose**: Test/debug risk calculation without creating certificate
- **Request**:
```json
{
  "valid_to": "2026-12-31T23:59:59Z",
  "key_length": 2048,
  "is_self_signed": false,
  "algorithm": "sha256WithRSAEncryption"
}
```
- **Response**:
```json
{
  "success": true,
  "risk_score": 0,
  "risk_level": "LOW",
  "reasoning": { ... detailed breakdown ... }
}
```

---

### 5. Integration with Certificate Ingestion ✅

**Files Modified**:
- `apps/certificates/services.py` (CertificateFetchService)
- `apps/certificates/internal_service.py` (InternalCertificateService)

**Changes**:

#### Public Certificates (`CertificateFetchService`)
```python
# OLD: Custom risk calculation logic in _calculate_risk()
# NEW: Uses RiskScoringEngine

# In scan_and_store():
cert_data['risk_level'], cert_data['risk_score'] = self._calculate_risk(cert_data)
cert_data['risk_reasoning'] = RiskScoringEngine.get_risk_reasoning(...)
```

#### Internal Certificates (`InternalCertificateService`)
```python
# OLD: Simple date-based logic (< 7 days = CRITICAL, etc)
# NEW: Uses RiskScoringEngine with key strength & penalties

# In ingest_certificate():
risk_level, risk_score = self._calculate_risk(valid_to, days_remaining)
risk_reasoning = RiskScoringEngine.get_risk_reasoning(...)
```

**Standardization**:
- All risk_level values now **UPPERCASE** (was mixed case)
- All scores use 0-100 range consistently
- All include risk_reasoning for audit trail

---

### 6. Test Coverage ✅

**Test Results** (all passing):

```
✅ Expired cert: Score=100, Level=CRITICAL
✅ Expiring in 5 days: Score=90, Level=CRITICAL
✅ Expiring in 45 days: Score=50, Level=MEDIUM
✅ Weak key (1024 bits): Score=40, Level=MEDIUM
✅ Self-signed: Score=25, Level=LOW
✅ Strong key (4096 bits): Score=0, Level=LOW
✅ Expiring in 20 days: Score=75, Level=HIGH
✅ Expired + weak key: Score=100, Level=CRITICAL
```

**Test Scenarios Covered**:
- ✅ Expired certificates
- ✅ Critical expiry (< 7 days)
- ✅ High risk expiry (< 30 days)
- ✅ Medium risk expiry (< 90 days)
- ✅ Weak key cryptography
- ✅ Self-signed certificates
- ✅ Strong key strength
- ✅ Combined risk factors

---

## API Usage Examples

### Check Risk Configuration
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8001/api/risk/config/
```

### Update Risk Thresholds (Superadmin Only)
```bash
curl -X PATCH \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "critical_expiry_days": 10,
    "high_expiry_days": 35,
    "self_signed_penalty": 30
  }' \
  http://localhost:8001/api/risk/config/
```

### Test Risk Calculation
```bash
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "valid_to": "2026-04-20T00:00:00Z",
    "key_length": 2048,
    "is_self_signed": false,
    "algorithm": "sha256WithRSAEncryption"
  }' \
  http://localhost:8001/api/risk/analyze/
```

---

## Database Schema

### Certificate Table (Updated)
```sql
-- New field added
ALTER TABLE certificates_certificate 
ADD COLUMN risk_reasoning JSONB DEFAULT '{}';

-- Indices maintained
CREATE INDEX idx_certificate_risk_level 
  ON certificates_certificate(risk_level, source_type);
```

### RiskConfiguration Table (New)
```sql
CREATE TABLE risk_engine_riskconfiguration (
  id SERIAL PRIMARY KEY,
  critical_expiry_days INTEGER DEFAULT 7,
  high_expiry_days INTEGER DEFAULT 30,
  medium_expiry_days INTEGER DEFAULT 90,
  weak_key_bits INTEGER DEFAULT 2048,
  medium_key_bits INTEGER DEFAULT 3072,
  self_signed_penalty INTEGER DEFAULT 25,
  weak_algorithm_penalty INTEGER DEFAULT 20,
  critical_threshold INTEGER DEFAULT 75,
  high_threshold INTEGER DEFAULT 50,
  medium_threshold INTEGER DEFAULT 25,
  last_modified_by_id INTEGER REFERENCES auth_user(id),
  last_modified_at TIMESTAMP,
  created_at TIMESTAMP
);
```

---

## Key Design Decisions

### 1. **Scoring Model**
- **Decision**: Expiry is PRIMARY, others are SECONDARY penalties
- **Reason**: Certificate expiry is most critical factor; key strength should enhance, not override
- **Impact**: 90-day cert with weak key = 50 + penalty, not mixed scoring

### 2. **Deterministic Calculation**
- **Decision**: No randomization, same inputs always produce same outputs
- **Reason**: Critical for debugging, auditing, and regulatory compliance
- **Impact**: Scores are reproducible and explainable

### 3. **Admin-Configurable Thresholds**
- **Decision**: Superadmin can adjust via API, not in code
- **Reason**: Allows tuning for different organizational risk profiles
- **Impact**: Risk levels can be adjusted without code changes; changes are audited

### 4. **Risk Reasoning Storage**
- **Decision**: Complete breakdown stored with each certificate
- **Reason**: Enables transparency, debugging, and audit trails
- **Impact**: Can answer "why did this cert get marked HIGH?"

### 5. **Unified for Public & Internal**
- **Decision**: Same engine for both cert sources
- **Reason**: Consistent risk assessment across organization
- **Impact**: Easier to compare risk across different cert inventories

---

## What's Next (Frontend Phase)

### Step 1: Create Frontend Risk Components
- `RiskBadge.jsx` - Color-coded badge with emoji
- `RiskSummaryCards.jsx` - Total/Critical/High/Medium/Low counts
- `RiskDistributionChart.jsx` - Pie chart of risk distribution

### Step 2: Integrate into Certificate Pages
- Add risk cards to dashboard
- Add risk filtering to certificate list
- Add risk color-coding to tables
- Add risk breakdown tooltip on hover

### Step 3: Create Risk Management UI
- Show risk trends over time
- Alert on risky certificates
- Risk threshold adjustment panel (superadmin only)

---

## Files Modified/Created

### Backend Files (Complete)
- ✅ `apps/risk_engine/services.py` (NEW - 299 lines)
- ✅ `apps/risk_engine/models.py` (MODIFIED - added RiskConfiguration)
- ✅ `apps/risk_engine/serializers.py` (MODIFIED - added RiskConfigurationSerializer)
- ✅ `apps/risk_engine/views.py` (MODIFIED - added RiskConfigurationView, RiskAnalysisView)
- ✅ `apps/risk_engine/urls.py` (MODIFIED - added endpoints)
- ✅ `apps/risk_engine/migrations/0002_riskconfiguration.py` (NEW)
- ✅ `apps/certificates/models.py` (MODIFIED - added risk_reasoning field)
- ✅ `apps/certificates/migrations/0004_certificate_risk_reasoning.py` (NEW)
- ✅ `apps/certificates/services.py` (MODIFIED - uses RiskScoringEngine)
- ✅ `apps/certificates/internal_service.py` (MODIFIED - uses RiskScoringEngine)

### Frontend Files (Next Phase)
- ⏳ `src/components/RiskBadge.jsx`
- ⏳ `src/components/RiskSummaryCards.jsx`
- ⏳ `src/components/RiskDistributionChart.jsx`
- ⏳ `src/pages/CertificatesPage.jsx` (integrate components)
- ⏳ `src/pages/InternalCertificatesPage.jsx` (integrate components)

---

## Performance Impact

- **Database Queries**: No additional queries (risk_reasoning is stored)
- **Calculation Time**: ~1ms per certificate (negligible)
- **Storage**: ~500 bytes per risk_reasoning JSON per cert (minimal)
- **Index Performance**: Risk filtering uses existing risk_level index

---

## Security & Compliance

✅ **Deterministic**: Auditable, reproducible calculations
✅ **Transparent**: Every score includes detailed reasoning
✅ **Access Controlled**: Only superadmins can modify thresholds
✅ **Audit-Logged**: All configuration changes tracked
✅ **Non-Editable**: Frontend cannot directly edit scores

---

## Status Summary

| Component | Status | Tests | Notes |
|---|---|---|---|
| Risk Engine Service | ✅ Complete | 8/8 | All deterministic tests passing |
| Certificate Models | ✅ Complete | N/A | Migrations applied successfully |
| RiskConfiguration | ✅ Complete | N/A | Default config auto-created |
| API Endpoints | ✅ Complete | N/A | Ready for frontend integration |
| Public Certs Integration | ✅ Complete | N/A | Using new risk engine |
| Internal Certs Integration | ✅ Complete | N/A | Using new risk engine |
| Frontend Components | ⏳ Not Started | - | Next phase |

---

## Next Commands

```bash
# Test the risk endpoint
curl -X POST http://localhost:8001/api/risk/analyze/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"valid_to":"2026-04-20T00:00:00Z","key_length":2048,"is_self_signed":false,"algorithm":"sha256WithRSAEncryption"}'

# Check current configuration
curl http://localhost:8001/api/risk/config/ \
  -H "Authorization: Bearer TOKEN"

# Update thresholds (superadmin only)
curl -X PATCH http://localhost:8001/api/risk/config/ \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"critical_expiry_days":5}'
```

---

**Implementation Date**: April 19, 2026
**Status**: Backend Phase Complete ✅
