"""
Agent Authentication and Authorization

Manages PowerShell agent tokens, authentication, logging, and rate limiting.
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Tuple

from django.db import models
from django.utils import timezone
from django.core.cache import cache


class CertificateAgent(models.Model):
    """
    Represents a PowerShell certificate collection agent.
    
    Tracks agent identity, authentication token, and submission statistics.
    """
    
    AGENT_TYPES = [
        ('powershell', 'PowerShell Script'),
        ('manual', 'Manual Upload'),
        ('api', 'Direct API'),
    ]
    
    agent_id = models.CharField(max_length=255, unique=True, db_index=True)
    agent_name = models.CharField(max_length=255, help_text="Human-readable agent name")
    agent_type = models.CharField(
        max_length=50,
        choices=AGENT_TYPES,
        default='powershell'
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    token_created_at = models.DateTimeField(default=timezone.now)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    hostname = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True, db_index=True)
    last_submission_at = models.DateTimeField(null=True, blank=True)
    submission_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent_id', 'is_active']),
            models.Index(fields=['token', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.agent_name} ({self.agent_id})"
    
    def save(self, *args, **kwargs):
        """Generate token if not already set."""
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())
        
        if not self.token:
            # Generate a 40-character hex token
            self.token = hashlib.sha1(
                f"{self.agent_id}{uuid.uuid4()}{timezone.now().isoformat()}".encode()
            ).hexdigest()[:40]
        
        super().save(*args, **kwargs)
    
    def is_token_valid(self) -> bool:
        """Check if agent token is still valid."""
        if not self.is_active:
            return False
        
        if self.token_expires_at and self.token_expires_at < timezone.now():
            return False
        
        return True
    
    def record_submission(self, count: int = 1):
        """Record certificate submission from agent."""
        self.submission_count += count
        self.last_submission_at = timezone.now()
        self.save(update_fields=['submission_count', 'last_submission_at'])


class AgentAuditLog(models.Model):
    """
    Audit log for all agent submissions.
    
    Tracks every certificate submission, success/failure, and details.
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
        ('unauthorized', 'Unauthorized'),
        ('malformed', 'Malformed Payload'),
    ]
    
    agent = models.ForeignKey(
        CertificateAgent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    certificates_submitted = models.PositiveIntegerField(default=0)
    certificates_created = models.PositiveIntegerField(default=0)
    certificates_updated = models.PositiveIntegerField(default=0)
    certificates_failed = models.PositiveIntegerField(default=0)
    
    error_message = models.TextField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.agent.agent_name if self.agent else 'Unknown'} - {self.status} ({self.timestamp})"


class AgentRateLimiter:
    """
    Rate limiting for certificate collection agents.
    
    Prevents abuse by limiting submissions per agent and globally.
    """
    
    # Rate limits
    SUBMISSIONS_PER_MINUTE = 60  # Max submissions per minute per agent
    CERTIFICATES_PER_HOUR = 10000  # Max certificates per hour per agent
    GLOBAL_CERTIFICATES_PER_MINUTE = 50000  # Global max per minute
    
    @staticmethod
    def check_rate_limit(agent_id: str, certificate_count: int = 1) -> Tuple[bool, str]:
        """
        Check if agent is within rate limits.
        
        Args:
            agent_id (str): Agent identifier
            certificate_count (int): Number of certificates being submitted
            
        Returns:
            Tuple[bool, str]: (is_allowed, message)
        """
        # Per-agent rate limits
        agent_key = f"agent_submissions_{agent_id}"
        agent_hour_key = f"agent_certs_hour_{agent_id}"
        
        agent_submissions = cache.get(agent_key, 0)
        agent_certs_hour = cache.get(agent_hour_key, 0)
        
        if agent_submissions >= AgentRateLimiter.SUBMISSIONS_PER_MINUTE:
            return False, "Agent submission rate limit exceeded (60 per minute)"
        
        if agent_certs_hour + certificate_count > AgentRateLimiter.CERTIFICATES_PER_HOUR:
            return False, f"Agent certificate limit exceeded (10000 per hour)"
        
        # Global rate limits
        global_key = "global_certs_minute"
        global_certs = cache.get(global_key, 0)
        
        if global_certs + certificate_count > AgentRateLimiter.GLOBAL_CERTIFICATES_PER_MINUTE:
            return False, "Global certificate rate limit exceeded (50000 per minute)"
        
        return True, "OK"
    
    @staticmethod
    def record_submission(agent_id: str, certificate_count: int = 1):
        """Record submission for rate limiting."""
        agent_key = f"agent_submissions_{agent_id}"
        agent_hour_key = f"agent_certs_hour_{agent_id}"
        global_key = "global_certs_minute"
        
        # Increment per-agent submission count
        current = cache.get(agent_key, 0)
        cache.set(agent_key, current + 1, 60)
        
        # Increment per-agent hourly certificate count
        current = cache.get(agent_hour_key, 0)
        cache.set(agent_hour_key, current + certificate_count, 3600)
        
        # Increment global certificate count
        current = cache.get(global_key, 0)
        cache.set(global_key, current + certificate_count, 60)


def generate_agent_token() -> str:
    """Generate a secure random agent token."""
    return hashlib.sha256(
        (str(uuid.uuid4()) + str(timezone.now())).encode()
    ).hexdigest()


def create_agent(
    agent_name: str,
    hostname: str = None,
    ip_address: str = None,
    agent_type: str = 'powershell'
) -> CertificateAgent:
    """
    Create a new certificate collection agent.
    
    Args:
        agent_name (str): Human-readable agent name
        hostname (str): Optional hostname of agent machine
        ip_address (str): Optional IP address of agent
        agent_type (str): Type of agent (powershell, manual, api)
        
    Returns:
        CertificateAgent: Created agent with token
    """
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    token = generate_agent_token()
    
    agent = CertificateAgent.objects.create(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_type=agent_type,
        token=token,
        token_expires_at=timezone.now() + timedelta(days=365),
        hostname=hostname,
        ip_address=ip_address,
    )
    
    return agent
