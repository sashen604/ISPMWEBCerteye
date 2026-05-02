from django.test import TestCase, override_settings

from apps.certificates.adcs_crypto import ADCSCredentialEncryption


@override_settings(ADCS_ENCRYPTION_KEY="unit-test-adcs-encryption-key-1234567890")
class ADCSCredentialEncryptionTests(TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "SuperSecretPassword!"
        encrypted = ADCSCredentialEncryption.encrypt(plaintext)
        self.assertNotEqual(encrypted, plaintext)
        decrypted = ADCSCredentialEncryption.decrypt(encrypted)
        self.assertEqual(decrypted, plaintext)


@override_settings(ADCS_PLAINTEXT_PASSWORDS_DEV=True)
class ADCSCredentialPlaintextDevTests(TestCase):
    def test_plaintext_roundtrip(self):
        plaintext = "PlainDevPassword#1"
        blob = ADCSCredentialEncryption.encrypt(plaintext)
        self.assertTrue(blob.startswith("ADCSPT1:"))
        self.assertEqual(ADCSCredentialEncryption.decrypt(blob), plaintext)
