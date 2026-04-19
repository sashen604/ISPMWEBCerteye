"""
Django management command for scanning SSL/TLS certificates.

Usage:
    # Scan single domain
    python manage.py scan_certificates google.com
    
    # Scan multiple domains
    python manage.py scan_certificates google.com github.com amazon.com
    
    # Scan with custom timeout (in seconds)
    python manage.py scan_certificates google.com --timeout 15
    
    # Don't update existing certificates
    python manage.py scan_certificates google.com --no-update
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from apps.certificates.services import CertificateFetchService


class Command(BaseCommand):
    help = 'Scan domains for SSL/TLS certificates and store in database'
    
    def add_arguments(self, parser):
        """Define command-line arguments."""
        parser.add_argument(
            'domains',
            nargs='+',
            type=str,
            help='Domain(s) to scan (e.g., google.com github.com)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=10,
            help='Connection timeout in seconds (default: 10)'
        )
        parser.add_argument(
            '--no-update',
            action='store_true',
            help='Do not update existing certificates'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output with detailed certificate information'
        )
    
    def handle(self, *args, **options):
        """Execute the management command."""
        domains = options['domains']
        timeout = options['timeout']
        update_if_exists = not options['no_update']
        verbose = options['verbose']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📡 Starting certificate scan at {now().isoformat()}\n'
            )
        )
        
        # Initialize service
        service = CertificateFetchService(timeout=timeout)
        
        # Handle single vs multiple domains
        if len(domains) == 1:
            result = service.scan_and_store(domains[0], update_if_exists=update_if_exists)
            self._output_single_result(result, verbose)
        else:
            results = service.scan_multiple(domains, update_if_exists=update_if_exists)
            self._output_multiple_results(results, verbose)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Scan completed at {now().isoformat()}\n')
        )
    
    def _output_single_result(self, result: dict, verbose: bool):
        """Output result for single domain scan."""
        if result['success']:
            cert = result['certificate']
            status_icon = '✨' if result['status'] == 'created' else '🔄'
            status_text = 'Created' if result['status'] == 'created' else 'Updated'
            
            self.stdout.write(
                self.style.SUCCESS(f'{status_icon} {status_text}: {cert.domain}')
            )
            
            if verbose:
                self._output_certificate_details(cert)
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {result["message"]}')
            )
            self.stdout.write(
                self.style.ERROR(f'   Error: {result["error"]}')
            )
    
    def _output_multiple_results(self, aggregated: dict, verbose: bool):
        """Output aggregated results for multiple domain scan."""
        self.stdout.write(
            self.style.WARNING(
                f'\n📊 Scan Results (Timeout: 10s):\n'
                f'   Total:   {aggregated["total"]}\n'
                f'   Success: {aggregated["succeeded"]}\n'
                f'   Failed:  {aggregated["failed"]}\n'
                f'   Created: {aggregated["created"]}\n'
                f'   Updated: {aggregated["updated"]}\n'
            )
        )
        
        self.stdout.write(self.style.WARNING('\n📋 Detailed Results:\n'))
        
        for result in aggregated['results']:
            if result['success']:
                cert = result['certificate']
                status_icon = '✨' if result['status'] == 'created' else '🔄'
                status_text = 'Created' if result['status'] == 'created' else 'Updated'
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{status_icon} {status_text}: {cert.domain} '
                        f'[Expires: {cert.days_remaining} days]'
                    )
                )
                
                if verbose:
                    self._output_certificate_details(cert)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ {result["message"]}: {result["error"]}'
                    )
                )
    
    def _output_certificate_details(self, cert):
        """Output detailed certificate information."""
        self.stdout.write(
            f'   ├─ Subject:     {cert.subject}\n'
            f'   ├─ Issuer:      {cert.issuer}\n'
            f'   ├─ Serial:      {cert.serial_number}\n'
            f'   ├─ Key Length:  {cert.key_length} bits\n'
            f'   ├─ Algorithm:   {cert.signature_algorithm}\n'
            f'   ├─ Valid From:  {cert.valid_from.isoformat()}\n'
            f'   ├─ Valid To:    {cert.valid_to.isoformat()}\n'
            f'   ├─ Days Left:   {cert.days_remaining}\n'
            f'   ├─ Risk Level:  {cert.risk_level} ({cert.risk_score}/100)\n'
            f'   └─ Type:        {cert.certificate_type}\n'
        )
