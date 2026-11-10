
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image, UnidentifiedImageError
from datetime import date


MAX_STUDENT_CARD_SIZE = 5 * 1024 * 1024


def validate_student_card_size(upload):
    if upload.size > MAX_STUDENT_CARD_SIZE:
        from django.core.exceptions import ValidationError

        raise ValidationError('Student ID card images must be 5 MB or smaller.')


def validate_student_card_image(upload):
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        from django.core.exceptions import ValidationError

        raise ValidationError('Upload a valid JPG or PNG image.')
    finally:
        upload.seek(0)


class Student(models.Model):

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    student_name = models.CharField(max_length=100)

    roll_number = models.CharField(max_length=20)

    batch_year = models.PositiveIntegerField()

    department = models.CharField(max_length=50)

    student_card = models.ImageField(
        upload_to='student_cards/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
            validate_student_card_size,
            validate_student_card_image,
        ],
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Active'
    )

    card_expiry_date = models.DateField(null=True, blank=True)

    def effective_status(self, on_date=None):
        check_date = on_date or date.today()
        if self.card_expiry_date is None:
            return self.status
        return 'Active' if check_date <= self.card_expiry_date else 'Inactive'

    def sync_status(self, on_date=None):
        effective_status = self.effective_status(on_date)
        if self.card_expiry_date is not None and self.status != effective_status:
            self.status = effective_status
            return True
        return False

    def __str__(self):
        return f"{self.student_name} - {self.roll_number}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['batch_year', 'department', 'roll_number'],
                name='unique_student_identity'
            )
        ]

