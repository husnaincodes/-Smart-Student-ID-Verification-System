from django.test import TestCase
from io import BytesIO
from datetime import date, timedelta
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.urls import reverse
from PIL import Image

from .admin import StudentAdmin
from .admin import StudentAdminForm
from .models import Student


def image_upload(name='student.png', image_format='PNG'):
	image = Image.new('RGB', (40, 25), color='navy')
	content = BytesIO()
	image.save(content, format=image_format)
	return SimpleUploadedFile(name, content.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=TemporaryDirectory().name)
class StudentVerificationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.student = Student.objects.create(
			student_name='Active Student',
			roll_number='CS-001',
			batch_year=2025,
			department='Computer Science',
			student_card=image_upload(),
			status='Active',
		)
		cls.inactive_student = Student.objects.create(
			student_name='Inactive Student',
			roll_number='CS-002',
			batch_year=2025,
			department='Computer Science',
			student_card=image_upload('inactive.png'),
			status='Inactive',
		)
		cls.future_student = Student.objects.create(
			student_name='Future Card Student', roll_number='CS-003', batch_year=2025,
			department='Computer Science', student_card=image_upload('future.png'),
			status='Inactive', card_expiry_date=date.today() + timedelta(days=30),
		)
		cls.today_student = Student.objects.create(
			student_name='Today Card Student', roll_number='CS-004', batch_year=2025,
			department='Computer Science', student_card=image_upload('today.png'),
			status='Inactive', card_expiry_date=date.today(),
		)
		cls.expired_student = Student.objects.create(
			student_name='Expired Card Student', roll_number='CS-005', batch_year=2025,
			department='Computer Science', student_card=image_upload('expired.png'),
			status='Active', card_expiry_date=date.today() - timedelta(days=1),
		)
		cls.user_model = get_user_model()
		cls.guard = cls.user_model.objects.create_user(username='guard', password='guard-pass')
		cls.admin = cls.user_model.objects.create_superuser(
			username='admin', password='admin-pass', email='admin@example.com'
		)

	def setUp(self):
		self.client.login(username='guard', password='guard-pass')

	def search_url(self, **overrides):
		values = {
			'year': '2025',
			'department': 'Computer Science',
			'roll_number': 'CS-001',
		}
		values.update(overrides)
		return f"{reverse('student_search')}?" + '&'.join(
			f'{key}={value.replace(" ", "+")}' for key, value in values.items()
		)

	def test_valid_active_student_shows_original_card(self):
		response = self.client.get(self.search_url())

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Student found')
		self.assertContains(response, 'Active')
		self.assertContains(response, self.student.student_card.url)

	def test_wrong_roll_number_batch_or_department_shows_not_found(self):
		for overrides in (
			{'roll_number': 'CS-999'},
			{'year': '2024'},
			{'department': 'Physics'},
		):
			with self.subTest(overrides=overrides):
				response = self.client.get(self.search_url(**overrides))
				self.assertContains(response, 'Student Record Not Found')

	def test_inactive_student_is_returned_with_its_card(self):
		response = self.client.get(self.search_url(roll_number='CS-002'))

		self.assertContains(response, 'Inactive')
		self.assertContains(response, 'Not Valid for Entry')
		self.assertContains(response, self.inactive_student.student_card.url)

	def test_future_and_today_expiry_are_valid_for_entry(self):
		for roll_number in ('CS-003', 'CS-004'):
			with self.subTest(roll_number=roll_number):
				response = self.client.get(self.search_url(roll_number=roll_number))
				self.assertContains(response, 'Active - Valid for Entry')
				self.assertContains(response, 'Card expiry date')

	def test_expired_card_is_not_valid_for_entry(self):
		response = self.client.get(self.search_url(roll_number='CS-005'))

		self.assertContains(response, 'Inactive - Not Valid for Entry')
		self.assertContains(response, 'Expired Card Student')

	def test_legacy_record_without_expiry_keeps_existing_status(self):
		self.assertIsNone(self.student.card_expiry_date)
		self.assertEqual(self.student.effective_status(), 'Active')

	def test_new_admin_student_requires_expiry_date(self):
		form = StudentAdminForm()

		self.assertTrue(form.fields['card_expiry_date'].required)

	def test_status_sync_command_updates_expired_cards_and_skips_legacy_rows(self):
		call_command('sync_student_status')

		self.expired_student.refresh_from_db()
		self.student.refresh_from_db()
		self.assertEqual(self.expired_student.status, 'Inactive')
		self.assertEqual(self.student.status, 'Active')

	def test_reset_returns_empty_dashboard(self):
		response = self.client.get(reverse('student_search'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Ready to verify')
		self.assertNotContains(response, 'Student found')

	def test_incomplete_search_is_rejected(self):
		response = self.client.get(reverse('student_search'), {'year': '2025'})

		self.assertContains(response, 'This field is required.')
		self.assertNotContains(response, 'Student found')

	def test_dashboard_requires_login(self):
		self.client.logout()

		response = self.client.get(reverse('student_search'))

		self.assertRedirects(response, '/login/?next=/')

	def test_guard_cannot_manage_students_in_admin(self):
		model_admin = StudentAdmin(Student, AdminSite())
		request = SimpleNamespace(user=self.guard)

		self.assertFalse(model_admin.has_add_permission(request))
		self.assertFalse(model_admin.has_change_permission(request))
		self.assertFalse(model_admin.has_delete_permission(request))
		self.assertFalse(model_admin.has_view_permission(request))

	def test_admin_can_manage_students(self):
		model_admin = StudentAdmin(Student, AdminSite())
		request = SimpleNamespace(user=self.admin)

		self.assertTrue(model_admin.has_add_permission(request))
		self.assertTrue(model_admin.has_change_permission(request))
		self.assertTrue(model_admin.has_delete_permission(request))

	def test_invalid_extension_and_oversized_image_are_rejected(self):
		invalid = Student(
			student_name='Invalid', roll_number='BAD', batch_year=2025,
			department='Computer Science', student_card=SimpleUploadedFile(
				'card.gif', b'not-an-image', content_type='image/gif'
			)
		)
		with self.assertRaises(ValidationError):
			invalid.full_clean()

		invalid_content = Student(
			student_name='Corrupt', roll_number='CORRUPT', batch_year=2025,
			department='Computer Science', student_card=SimpleUploadedFile(
				'card.png', b'not-an-image', content_type='image/png'
			)
		)
		with self.assertRaises(ValidationError):
			invalid_content.full_clean()

		oversized = Student(
			student_name='Large', roll_number='BIG', batch_year=2025,
			department='Computer Science', student_card=SimpleUploadedFile(
				'card.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png'
			)
		)
		with self.assertRaises(ValidationError):
			oversized.full_clean()

# Create your tests here.
