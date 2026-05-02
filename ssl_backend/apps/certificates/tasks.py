from celery import shared_task
from django.utils import timezone

from apps.certificates.models import Domain
from apps.certificates.services import CertificateFetchService


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def scan_domain_task(self, domain_id: int, timeout: int = 10, update_if_exists: bool = True):
    domain = Domain.objects.get(id=domain_id)
    service = CertificateFetchService(timeout=timeout)
    result = service.scan_and_store(
        domain=domain.name,
        update_if_exists=update_if_exists,
        domain_obj=domain,
    )
    if not result.get("success"):
        error_type = result.get("error_type")
        if error_type in {"invalid_domain", "parse_error"}:
            return {
                "domain": domain.name,
                "status": "failed",
                "error_type": error_type,
                "error": result.get("error"),
                "scanned_at": timezone.now().isoformat(),
            }
        # Trigger retry for transient failures.
        raise RuntimeError(result.get("error") or "Domain scan failed")
    return {
        "domain": domain.name,
        "status": result.get("status"),
        "scanned_at": timezone.now().isoformat(),
    }


@shared_task
def scan_all_enabled_domains_task():
    domain_ids = list(Domain.objects.filter(is_enabled=True).values_list("id", flat=True))
    for domain_id in domain_ids:
        scan_domain_task.delay(domain_id)
    return {"scheduled_count": len(domain_ids), "scanned_at": timezone.now().isoformat()}
