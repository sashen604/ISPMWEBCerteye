"""
Testing script for Internal Certificate Collection API

This module provides utilities for testing the internal certificate collection endpoint
with various scenarios: valid payloads, duplicates, malformed data, missing fields,
and unauthorized requests.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple


class InternalCertificateAPITester:
    """Test client for internal certificate collection endpoint."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/certificates/collect_internal/"
        self.agent_token = None
        self.results = []
    
    def set_agent_token(self, token: str):
        """Set the agent token for requests."""
        self.agent_token = token
    
    def _make_request(
        self,
        payload: Dict[str, Any],
        token: str = None
    ) -> Tuple[int, Dict]:
        """
        Make request to the API endpoint.
        
        Returns: (status_code, response_json)
        """
        headers = {'Content-Type': 'application/json'}
        
        if token:
            payload['agent_token'] = token
        elif self.agent_token:
            payload['agent_token'] = self.agent_token
        
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=10)
            return response.status_code, response.json()
        except Exception as e:
            return 500, {'error': str(e)}
    
    def test_missing_token(self) -> bool:
        """Test: Missing agent token."""
        print("\n[Test 1] Missing agent token")
        payload = {
            'hostname': 'SERVER01',
            'subject': '*.example.com',
            'issuer': 'Internal CA',
            'thumbprint': 'ABCD1234567890',
            'valid_to': datetime.now(timezone.utc).isoformat(),
        }
        
        status, response = requests.post(
            self.endpoint,
            json=payload,
            timeout=10
        ).status_code, requests.post(
            self.endpoint,
            json=payload,
            timeout=10
        ).json()
        
        expected = 401
        passed = status == expected
        print(f"  Status: {status} (expected {expected}) {'✓' if passed else '✗'}")
        print(f"  Message: {response.get('message', 'N/A')}")
        return passed
    
    def test_valid_single_certificate(self, token: str) -> bool:
        """Test: Valid single certificate ingestion."""
        print("\n[Test 2] Valid single certificate")
        
        payload = {
            'agent_token': token,
            'hostname': 'SERVER01',
            'subject': 'server01.example.com',
            'issuer': 'Example Internal CA',
            'thumbprint': 'ABC123DEF456GHI789JKL012',
            'valid_from': (datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
            'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            'certificate_template': 'WebServer',
            'signature_algorithm': 'sha256WithRSAEncryption',
            'key_length': 2048,
        }
        
        status, response = self._make_request(payload, token)
        
        passed = status in (200, 201) and response.get('success')
        print(f"  Status: {status} {'✓' if passed else '✗'}")
        print(f"  Message: {response.get('message', 'N/A')}")
        if response.get('certificate'):
            print(f"  Certificate ID: {response['certificate'].get('id', 'N/A')}")
        
        return passed
    
    def test_duplicate_thumbprint(self, token: str, thumbprint: str) -> bool:
        """Test: Duplicate thumbprint (should update)."""
        print("\n[Test 3] Duplicate thumbprint (upsert)")
        
        payload = {
            'agent_token': token,
            'hostname': 'SERVER02',
            'subject': 'server02.example.com',
            'issuer': 'Example Internal CA',
            'thumbprint': thumbprint,  # Same thumbprint as before
            'valid_from': (datetime.now(timezone.utc) - timedelta(days=365)).isoformat(),
            'valid_to': (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),  # Different date
            'certificate_template': 'WebServer',
        }
        
        status, response = self._make_request(payload, token)
        
        passed = status in (200, 201) and response.get('success')
        expected_status = 'updated'
        status_matched = response.get('status') == expected_status
        
        print(f"  HTTP Status: {status} {'✓' if passed else '✗'}")
        print(f"  Status: {response.get('status')} (expected '{expected_status}') {'✓' if status_matched else '✗'}")
        print(f"  Message: {response.get('message', 'N/A')}")
        
        return passed and status_matched
    
    def test_malformed_json(self, token: str) -> bool:
        """Test: Malformed JSON payload."""
        print("\n[Test 4] Malformed JSON")
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(
                self.endpoint,
                data='{invalid json}',
                headers=headers,
                timeout=10
            )
            status = response.status_code
            passed = status in (400, 422)
            print(f"  Status: {status} (expected 400 or 422) {'✓' if passed else '✗'}")
            return passed
        except Exception as e:
            print(f"  Error: {str(e)}")
            return False
    
    def test_missing_required_field(self, token: str) -> bool:
        """Test: Missing required field."""
        print("\n[Test 5] Missing required field (thumbprint)")
        
        payload = {
            'agent_token': token,
            'hostname': 'SERVER03',
            'subject': 'server03.example.com',
            'issuer': 'Example Internal CA',
            # Missing: thumbprint
            'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        }
        
        status, response = self._make_request(payload, token)
        
        passed = status == 400 and not response.get('success')
        print(f"  Status: {status} (expected 400) {'✓' if passed else '✗'}")
        print(f"  Message: {response.get('message', 'N/A')}")
        
        return passed
    
    def test_invalid_token(self) -> bool:
        """Test: Invalid agent token."""
        print("\n[Test 6] Invalid agent token")
        
        payload = {
            'agent_token': 'invalid_token_12345',
            'hostname': 'SERVER04',
            'subject': 'server04.example.com',
            'issuer': 'Example Internal CA',
            'thumbprint': 'INVALID123456789',
            'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        }
        
        # Make request without passing token parameter to prevent override by self.agent_token
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=10)
            status = response.status_code
            response_json = response.json()
        except Exception as e:
            status = 500
            response_json = {'error': str(e)}
        
        passed = status == 401 and not response_json.get('success')
        print(f"  Status: {status} (expected 401) {'✓' if passed else '✗'}")
        print(f"  Message: {response_json.get('message', 'N/A')}")
        
        return passed
    
    def test_batch_ingestion(self, token: str) -> bool:
        """Test: Batch certificate ingestion."""
        print("\n[Test 7] Batch certificate ingestion")
        
        payload = {
            'agent_token': token,
            'certificates': [
                {
                    'hostname': 'BATCH-SERVER-01',
                    'subject': 'batch01.example.com',
                    'issuer': 'Example Internal CA',
                    'thumbprint': 'BATCH001CERT001THUMBPRINT',
                    'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
                    'certificate_template': 'WebServer',
                },
                {
                    'hostname': 'BATCH-SERVER-02',
                    'subject': 'batch02.example.com',
                    'issuer': 'Example Internal CA',
                    'thumbprint': 'BATCH002CERT002THUMBPRINT',
                    'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
                    'certificate_template': 'IIS',
                },
                {
                    'hostname': 'BATCH-SERVER-03',
                    'subject': 'batch03.example.com',
                    'issuer': 'Example Internal CA',
                    'thumbprint': 'BATCH003CERT003THUMBPRINT',
                    'valid_to': (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
                    'certificate_template': 'WebServer',
                },
            ],
            'update_if_exists': True,
        }
        
        status, response = self._make_request(payload, token)
        
        passed = status in (200, 201) and response.get('success')
        print(f"  HTTP Status: {status} {'✓' if passed else '✗'}")
        print(f"  Total: {response.get('total')} | Created: {response.get('created')} | Updated: {response.get('updated')} | Failed: {response.get('failed')}")
        
        return passed
    
    def test_expired_certificate(self, token: str) -> bool:
        """Test: Expired certificate handling."""
        print("\n[Test 8] Expired certificate (should mark as CRITICAL)")
        
        payload = {
            'agent_token': token,
            'hostname': 'EXPIRED-SERVER',
            'subject': 'expired.example.com',
            'issuer': 'Example Internal CA',
            'thumbprint': 'EXPIRED123456789THUMBPRINT',
            'valid_from': (datetime.now(timezone.utc) - timedelta(days=730)).isoformat(),
            'valid_to': (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),  # Expired yesterday
            'certificate_template': 'WebServer',
        }
        
        status, response = self._make_request(payload, token)
        
        passed = status in (200, 201) and response.get('success')
        if response.get('certificate'):
            cert = response['certificate']
            risk_is_critical = cert.get('risk_level') == 'CRITICAL'
            print(f"  Risk Level: {cert.get('risk_level')} (expected CRITICAL) {'✓' if risk_is_critical else '✗'}")
            print(f"  Risk Score: {cert.get('risk_score')} (expected 100) {'✓' if cert.get('risk_score') == 100 else '✗'}")
            passed = passed and risk_is_critical
        
        return passed


def run_all_tests(agent_token: str, base_url: str = "http://localhost:8000"):
    """Run all tests."""
    print("=" * 60)
    print("Internal Certificate Collection API - Test Suite")
    print("=" * 60)
    
    tester = InternalCertificateAPITester(base_url)
    tester.set_agent_token(agent_token)
    
    results = {
        'Test 1: Missing token': tester.test_missing_token(),
        'Test 2: Valid single certificate': tester.test_valid_single_certificate(agent_token),
        'Test 3: Duplicate thumbprint': tester.test_duplicate_thumbprint(agent_token, 'ABC123DEF456GHI789JKL012'),
        'Test 4: Malformed JSON': tester.test_malformed_json(agent_token),
        'Test 5: Missing required field': tester.test_missing_required_field(agent_token),
        'Test 6: Invalid token': tester.test_invalid_token(),
        'Test 7: Batch ingestion': tester.test_batch_ingestion(agent_token),
        'Test 8: Expired certificate': tester.test_expired_certificate(agent_token),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = '✓ PASS' if result else '✗ FAIL'
        print(f"{test_name:45} {status}")
    
    print(f"\n{'Total':45} {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return results


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_internal_certs.py <agent_token> [base_url]")
        print("Example: python test_internal_certs.py abc123def456 http://localhost:8000")
        sys.exit(1)
    
    agent_token = sys.argv[1]
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    run_all_tests(agent_token, base_url)
