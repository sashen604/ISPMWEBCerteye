"""
Unified Risk Scoring & Categorization Service

Provides deterministic risk calculation for certificates across multiple dimensions:
- Certificate expiry (primary factor)
- Key strength (secondary factor)
- Self-signing status
- Algorithm strength

Risk scores are 0-100 with clear thresholds mapping to levels:
- CRITICAL (75-100): Immediate action required
- HIGH (50-74): Address within 1 week
- MEDIUM (25-49): Address within 1 month
- LOW (0-24): Routine monitoring
"""

from datetime import datetime
from django.utils import timezone
from typing import Dict, Optional, Any


class RiskScoringEngine:
    """
    Deterministic risk scoring engine for SSL certificates.
    
    All calculations are:
    - Deterministic (same inputs always produce same outputs)
    - Documented (every factor has clear explanation)
    - Non-editable in frontend (only admin API can change thresholds)
    """
    
    # Risk thresholds - can be configured via API (superadmin only)
    THRESHOLDS = {
        # Expiry thresholds (days remaining)
        'expired': 0,  # 0-1 days: add 100 points (CRITICAL)
        'critical_expiry': 7,  # < 7 days: add 90 points
        'high_expiry': 30,  # < 30 days: add 75 points
        'medium_expiry': 90,  # < 90 days: add 50 points
        
        # Key strength thresholds (bits)
        'weak_key': 2048,  # < 2048 bits: add 40 points
        'medium_key': 3072,  # < 3072 bits: add 15 points
        'strong_key': 4096,  # >= 4096 bits: add 0 points
        
        # Other risk factors
        'self_signed_penalty': 25,  # Self-signed certificate: add 25 points
    }
    
    # Weighted scoring model
    WEIGHTS = {
        'expiry': 0.5,
        'crypto': 0.35,
        'validity': 0.15,
    }
    
    @classmethod
    def calculate_risk_score(
        cls,
        valid_to: datetime,
        key_length: int,
        is_self_signed: bool = False,
        algorithm: Optional[str] = None,
    ) -> int:
        """
        Calculate risk score for a certificate (0-100).
        
        Scoring model - Expiry is PRIMARY factor:
        - Expired: 100
        - < 7 days: 90
        - < 30 days: 75
        - < 90 days: 50
        - >= 90 days: 0 (base)
        
        Then add secondary penalties (key strength, self-signing):
        - Key < 2048: +40
        - Key 2048-3071: 0 (standard key length)
        - Key >= 3072: 0 (strong)
        - Self-signed: +25
        
        Args:
            valid_to: Certificate expiration datetime
            key_length: RSA key length in bits
            is_self_signed: Whether certificate is self-signed
            algorithm: Signature algorithm (e.g., 'sha256WithRSAEncryption')
        
        Returns:
            Risk score (0-100), deterministic based on inputs
        """
        now = timezone.now()
        days_remaining = (valid_to - now).days
        expiry_score = cls.get_expiry_score(days_remaining)
        crypto_score = cls.get_crypto_score(
            key_length=key_length,
            is_self_signed=is_self_signed,
            algorithm=algorithm,
            crypto_findings=None,
        )
        validity_score = cls.get_validity_score(valid_to=valid_to)
        weighted_score = (
            cls.WEIGHTS['expiry'] * expiry_score
            + cls.WEIGHTS['crypto'] * crypto_score
            + cls.WEIGHTS['validity'] * validity_score
        )
        return cls._normalize_score(weighted_score)

    @classmethod
    def get_expiry_score(cls, days_remaining: int) -> int:
        """Convert remaining days to expiry risk sub-score (0-100)."""
        if days_remaining <= 0:
            return 100
        if days_remaining < 7:
            return 95
        if days_remaining < 30:
            return 80
        if days_remaining < 90:
            return 55
        if days_remaining < 180:
            return 25
        return 5

    @classmethod
    def get_crypto_score(
        cls,
        key_length: int,
        is_self_signed: bool = False,
        algorithm: Optional[str] = None,
        crypto_findings: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Convert crypto findings into a 0-100 crypto risk sub-score."""
        score = 0
        algorithm_text = (algorithm or "").lower()
        weak_algorithm_tokens = ("md5", "sha1")

        if key_length and key_length < 2048:
            score += 50
        elif key_length and key_length < 3072:
            score += 20

        if is_self_signed:
            score += 20

        if any(token in algorithm_text for token in weak_algorithm_tokens):
            score += 30

        if isinstance(crypto_findings, dict):
            issues = crypto_findings.get("issues", [])
            if isinstance(issues, list):
                score += min(len(issues) * 8, 40)
            if crypto_findings.get("is_weak_key"):
                score += 20
            if crypto_findings.get("is_weak_algorithm"):
                score += 25

        return cls._normalize_score(score)

    @classmethod
    def get_validity_score(
        cls,
        valid_to: datetime,
        valid_from: Optional[datetime] = None,
        validity_ok: Optional[bool] = None,
    ) -> int:
        """Return 100 when validity checks fail, otherwise 0."""
        if validity_ok is not None:
            return 100 if not validity_ok else 0

        now = timezone.now()
        if valid_to <= now:
            return 100
        if valid_from and valid_from > now:
            return 100
        return 0

    @classmethod
    def calculate_weighted_risk(
        cls,
        *,
        days_remaining: int,
        valid_to: datetime,
        key_length: int,
        is_self_signed: bool = False,
        algorithm: Optional[str] = None,
        crypto_findings: Optional[Dict[str, Any]] = None,
        valid_from: Optional[datetime] = None,
        validity_ok: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Compute weighted risk score and explain why.

        Formula:
            R = 0.5*expiry + 0.35*crypto + 0.15*validity
        """
        expiry_score = cls.get_expiry_score(days_remaining)
        crypto_score = cls.get_crypto_score(
            key_length=key_length,
            is_self_signed=is_self_signed,
            algorithm=algorithm,
            crypto_findings=crypto_findings,
        )
        validity_score = cls.get_validity_score(
            valid_to=valid_to,
            valid_from=valid_from,
            validity_ok=validity_ok,
        )
        weighted_value = (
            cls.WEIGHTS["expiry"] * expiry_score
            + cls.WEIGHTS["crypto"] * crypto_score
            + cls.WEIGHTS["validity"] * validity_score
        )
        total_score = cls._normalize_score(weighted_value)
        risk_level = cls.determine_risk_level(total_score)

        reasons = []
        if days_remaining <= 0:
            reasons.append("Certificate is already expired")
        elif days_remaining < 30:
            reasons.append(f"Certificate expires soon ({days_remaining} days remaining)")
        elif days_remaining < 90:
            reasons.append(f"Certificate has medium expiry exposure ({days_remaining} days remaining)")

        if crypto_score >= 70:
            reasons.append("Cryptographic posture is weak (algorithm/key/self-signed findings)")
        elif crypto_score >= 35:
            reasons.append("Cryptographic posture has moderate weaknesses")

        if validity_score == 100:
            reasons.append("Certificate validity check failed")
        else:
            reasons.append("Certificate validity window is currently valid")

        return {
            "weights": cls.WEIGHTS.copy(),
            "components": {
                "expiry": expiry_score,
                "crypto": crypto_score,
                "validity": validity_score,
            },
            "weighted_formula": (
                f"0.5*{expiry_score} + 0.35*{crypto_score} + 0.15*{validity_score}"
            ),
            "weighted_raw_score": round(weighted_value, 2),
            "total_score": total_score,
            "risk_level": risk_level,
            "risk_reasons": reasons,
        }

    @staticmethod
    def _normalize_score(value: float) -> int:
        return max(0, min(100, int(round(value))))
    
    @classmethod
    def determine_risk_level(cls, risk_score: int) -> str:
        """
        Map risk score to risk level (CRITICAL/HIGH/MEDIUM/LOW).
        
        Args:
            risk_score: Calculated risk score (0-100)
        
        Returns:
            Risk level: 'CRITICAL', 'HIGH', 'MEDIUM', or 'LOW'
            
        Mapping:
            - 76-100: CRITICAL (e.g., 90=expired<7d, 100=expired)
            - 51-75: HIGH (e.g., 75=expires<30d, 75+penalties)
            - 26-50: MEDIUM (e.g., 50=expires<90d)
            - 0-25: LOW (e.g., 0-25 base, 25=self-signed)
        """
        if risk_score > 75:
            return 'CRITICAL'
        elif risk_score > 50:
            return 'HIGH'
        elif risk_score > 25:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    @classmethod
    def get_risk_reasoning(
        cls,
        valid_to: datetime,
        key_length: int,
        is_self_signed: bool = False,
        algorithm: Optional[str] = None,
    ) -> Dict:
        """
        Generate detailed reasoning for risk score calculation.
        
        Returns explanation of all factors contributing to the score.
        Stored as audit trail for transparency.
        
        Args:
            valid_to: Certificate expiration datetime
            key_length: RSA key length in bits
            is_self_signed: Whether certificate is self-signed
            algorithm: Signature algorithm
        
        Returns:
            Dictionary with detailed breakdown of risk calculation:
            {
                'expiry_days': int,
                'expiry_penalty': int,
                'expiry_factor': str,
                'key_length': int,
                'key_penalty': int,
                'key_factor': str,
                'self_signed': bool,
                'self_signed_penalty': int,
                'algorithm': str,
                'algorithm_penalty': int,
                'algorithm_factor': str,
                'total_score': int,
                'risk_level': str,
                'risk_reasons': [str],  # Human-readable reasons
            }
        """
        now = timezone.now()
        days_remaining = (valid_to - now).days
        weighted = cls.calculate_weighted_risk(
            days_remaining=days_remaining,
            valid_to=valid_to,
            key_length=key_length,
            is_self_signed=is_self_signed,
            algorithm=algorithm,
        )
        weighted.update(
            {
                "expiry_days": days_remaining,
                "key_length": key_length,
                "self_signed": is_self_signed,
                "algorithm": algorithm or "Unknown",
            }
        )
        return weighted
    
    @classmethod
    def update_thresholds(cls, new_thresholds: Dict) -> None:
        """
        Update risk thresholds (superadmin only via API).
        
        This allows fine-tuning of risk calculation without code changes.
        All changes should be logged for audit trail.
        
        Args:
            new_thresholds: Dictionary with new threshold values
        """
        # Validate thresholds before updating
        valid_keys = set(cls.THRESHOLDS.keys())
        invalid_keys = set(new_thresholds.keys()) - valid_keys
        
        if invalid_keys:
            raise ValueError(f"Invalid threshold keys: {invalid_keys}")
        
        # Update thresholds
        cls.THRESHOLDS.update(new_thresholds)
    
    @classmethod
    def get_thresholds(cls) -> Dict:
        """
        Get current risk thresholds.
        
        Returns:
            Dictionary with all current threshold values
        """
        return cls.THRESHOLDS.copy()
