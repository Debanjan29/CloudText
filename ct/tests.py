from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.timezone import now
from datetime import timedelta
from ct.models import Store
from ct.views import cleanup_expired_files

# === 2026 update! ===
class CloudTextTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_text_upload_and_retrieval(self):
        response = self.client.post('/', {'content': 'console.log("Hello 2026");'})
        self.assertEqual(response.status_code, 200)
        item = Store.objects.filter(is_file=False).first()
        self.assertIsNotNone(item)
        self.assertIn('console.log', item.msg)

        # Retrieve text
        get_res = self.client.post('/get/', {'query': item.id})
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'console.log')

    def test_file_upload_and_download(self):
        file_data = SimpleUploadedFile("test_doc.txt", b"CloudText binary content", content_type="text/plain")
        response = self.client.post('/save/', {'file_upload': file_data})
        self.assertEqual(response.status_code, 200)

        item = Store.objects.filter(is_file=True).first()
        self.assertIsNotNone(item)
        self.assertTrue(item.file_name.endswith('.zip'))

        # Test download endpoint
        dl_res = self.client.get(f'/download/{item.id}/')
        self.assertEqual(dl_res.status_code, 200)
        self.assertEqual(dl_res['Content-Disposition'], f'attachment; filename="{item.file_name}"')

    def test_image_quality_preservation(self):
        raw_png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        img_file = SimpleUploadedFile("photo.png", raw_png_bytes, content_type="image/png")
        self.client.post('/save/', {'file_upload': img_file})

        item = Store.objects.filter(is_file=True, file_type='image/png').first()
        self.assertIsNotNone(item)
        self.assertEqual(bytes(item.file_data), raw_png_bytes)

    def test_30_day_cleanup_conditional_rules(self):
        # Create an old text record (40 days old)
        old_text = Store.objects.create(id='txt1', msg='Permanent Text', is_file=False, date=now() - timedelta(days=40))
        # Create an old file record (40 days old, 10MB)
        old_file = Store.objects.create(id='file1', msg='Old File', is_file=True, file_data=b'data', file_size=10*1024*1024, date=now() - timedelta(days=40))

        # Case 1: DB storage < 400MB and incoming file < 200MB -> NO CLEANUP
        cleanup_expired_files(incoming_file_size=50*1024*1024)
        self.assertTrue(Store.objects.filter(id='txt1').exists())
        self.assertTrue(Store.objects.filter(id='file1').exists())

        # Case 2: Incoming file size >= 200MB -> CLEANUP TRIGGERS
        cleanup_expired_files(incoming_file_size=205*1024*1024)
        # Text record MUST remain
        self.assertTrue(Store.objects.filter(id='txt1').exists())
        # File record MUST be cleaned up
        self.assertFalse(Store.objects.filter(id='file1').exists())

    # === SECURITY MEASURES 2026: Security Tests ===
    def test_ip_rate_limiting_max_7_per_minute(self):
        client = Client(REMOTE_ADDR='192.168.1.100')
        # First 7 requests should pass
        for i in range(7):
            res = client.post('/', {'content': f'Test paste {i}'})
            self.assertEqual(res.status_code, 200)
            self.assertNotIn('Rate limit exceeded', res.content.decode('utf-8'))

        # 8th request from same IP within 1 minute MUST be rate limited
        limited_res = client.post('/', {'content': 'Spam paste 8'})
        self.assertContains(limited_res, 'Rate limit exceeded')

    def test_path_traversal_filename_sanitization(self):
        client = Client(REMOTE_ADDR='192.168.1.101')
        dangerous_file = SimpleUploadedFile("../../etc/passwd", b"malicious data", content_type="text/plain")
        client.post('/save/', {'file_upload': dangerous_file})

        item = Store.objects.filter(is_file=True).first()
        self.assertIsNotNone(item)
        self.assertNotIn('../', item.file_name)
        self.assertNotIn('..\\', item.file_name)
    def test_simultaneous_text_and_file_upload(self):
        client = Client(REMOTE_ADDR='192.168.1.102')
        img_file = SimpleUploadedFile("diagram.png", b"png_data", content_type="image/png")
        res = client.post('/save/', {'content': 'Here is the diagram description', 'file_upload': img_file})
        self.assertEqual(res.status_code, 200)

        item = Store.objects.filter(is_file=True, file_name='diagram.png').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.msg, 'Here is the diagram description')

        # Retrieve and verify both image and text are rendered
        get_res = client.post('/get/', {'query': item.id})
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'diagram.png')
        self.assertContains(get_res, 'Here is the diagram description')
    # === SECURITY MEASURES 2026 ===
# === 2026 update! ===
