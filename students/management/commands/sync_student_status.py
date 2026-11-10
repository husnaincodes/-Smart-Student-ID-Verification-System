from django.core.management.base import BaseCommand

from students.models import Student


class Command(BaseCommand):
    help = 'Synchronize stored student status from card expiry dates.'

    def handle(self, *args, **options):
        updated = 0
        skipped = 0
        for student in Student.objects.all().iterator():
            if student.card_expiry_date is None:
                skipped += 1
                continue
            if student.sync_status():
                student.save(update_fields=['status'])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Synchronized {updated} student status(es); skipped {skipped} record(s) without expiry dates.'
            )
        )