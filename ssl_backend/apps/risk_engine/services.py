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

from datetime import datetime, timedelta
from django.utils import timezone
from typing import Dict, Tuple, Optional


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
    
    # Risk level mapping thresholds
    RISK_LEVEL_THRESHOLDS = {
        'CRITICAL': 75,  # 75-100
        'HIGH': 50,  # 50-74
        'MEDIUM': 25,  # 25-49
        'LOW': 0,  # 0-24
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
        score = 0
        now = timezone.now()
        days_remaining = (valid_to - now).days
        
        # PRIMARY FACTOR: Expiry (most important)
        if days_remaining <= 0:
            score = 100  # Expired
        elif days_remaining < 7:
            score = 90   # < 7 days: CRITICAL
        elif days_remaining < 30:
            score = 75   # < 30 days: HIGH
        elif days_remaining < 90:
            score = 50   # < 90 days: MEDIUM
        else:
            score = 0    # >= 90 days: LOW baseline
        
        # SECONDARY FACTORS: Penalties to add on top
        
        # Key strength penalty
        if key_length < 2048:
            score += 40  # Weak key
        # 2048-3071: no penalty (standard)
        # 3072+: no penalty (strong)
        
        # Self-signing penalty
        if is_self_signed:
            score += 25
        
        # Algorithm penalty
        if algorithm:
            weak_algorithms = ['md5WithRSAEncryption', 'sha1WithRSAEncryption']
            if any(weak in algorithm.lower() for weak in weak_algorithms):
                score += 20
        
        # Cap at 100
        return min(score, 100)
    
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
        
        reasoning = {
            'expiry_days': days_remaining,
            'expiry_penalty': 0,
            'expiry_factor': 'Unknown',
            'key_length': key_length,
            'key_penalty': 0,
            'key_factor': 'Unknown',
            'self_signed': is_self_signed,
            'self_signed_penalty': 0,
            'algorithm': algorithm or 'Unknown',
            'algorithm_penalty': 0,
            'algorithm_factor': 'Unknown',
            'risk_reasons': [],
        }
        
        # Expiry factor
        if days_remaining <= 0:
            reasoning['expiry_penalty'] = 100
            reasoning['expiry_factor'] = 'Expired'
            reasoning['risk_reasons'].append(f'Certificate already expired {abs(days_remaining)} days ago')
        elif days_remaining < cls.THRESHOLDS['critical_expiry']:
            reasoning['expiry_penalty'] = 90
            reasoning['expiry_factor'] = 'Critical (< 7 days)'
            reasoning['risk_reasons'].append(f'Expires in {days_remaining} days (critical)')
        elif days_remaining < cls.THRESHOLDS['high_expiry']:
            reasoning['expiry_penalty'] = 75
            reasoning['expiry_factor'] = 'High (< 30 days)'
            reasoning['risk_reasons'].append(f'Expires in {days_remaining} days (high priority)')
        elif days_remaining < cls.THRESHOLDS['medium_expiry']:
            reasoning['expiry_penalty'] = 50
            reasoning['expiry_factor'] = 'Medium (< 90 days)'
            reasoning['risk_reasons'].append(f'Expires in {days_remaining} days (medium priority)')
        else:
            reasoning['expiry_penalty'] = 0
            reasoning['expiry_factor'] = 'Low (> 90 days)'
            reasoning['risk_reasons'].append(f'Expires in {days_remaining} days (acceptable)')
        
        # Key strength factor
        if key_length < cls.THRESHOLDS['weak_key']:
            reasoning['key_penalty'] = 40
            reasoning['key_factor'] = f'Weak ({key_length} bits)'
            reasoning['risk_reasons'].append(f'Weak key length: {key_length} bits (recommended >= 2048)')
        elif key_length < cls.THRESHOLDS['medium_key']:
            reasoning['key_penalty'] = 15
            reasoning['key_factor'] = f'Moderate ({key_length} bits)'
            reasoning['risk_reasons'].append(f'Moderate key length: {key_length} bits')
        else:
            reasoning['key_penalty'] = 0
            reasoning['key_factor'] = f'Strong ({key_length} bits)'
            reasoning['risk_reasons'].append(f'Strong key length: {key_length} bits')
        
        # Self-signed factor
        if is_self_signed:
            reasoning['self_signed_penalty'] = cls.THRESHOLDS['self_signed_penalty']
            reasoning['risk_reasons'].append('Self-signed certificate (not from trusted CA)')
        
        # Algorithm factor
        if algorithm:
            weak_algorithms = ['md5WithRSAEncryption', 'sha1WithRSAEncryption']
            if any(weak in algorithm.lower() for weak in weak_algorithms):
                reasoning['algorithm_penalty'] = 20
                reasoning['algorithm_factor'] = f'Weak ({algorithm})'
                reasoning['risk_reasons'].append(f'Weak algorithm: {algorithm}')
            else:
                reasoning['algorithm_penalty'] = 0
                reasoning['algorithm_factor'] = f'Strong ({algorithm})'
        
        # Calculate total and risk level
        total = cls.calculate_risk_score(valid_to, key_length, is_self_signed, algorithm)
        reasoning['total_score'] = total
        reasoning['risk_level'] = cls.determine_risk_level(total)
        
        return reasoning
    
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
