from django.core.management.base import BaseCommand
from file_sharing.tasks import cleanup_expired_files, cleanup_old_inactive_files

class Command(BaseCommand):
    help = 'Clean up expired and old files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clean up both expired and old files',
        )
        parser.add_argument(
            '--old-only',
            action='store_true',
            help='Clean up only old inactive files',
        )
    
    def handle(self, *args, **options):
        if options['old_only']:
            result = cleanup_old_inactive_files()
            self.stdout.write(self.style.SUCCESS(result))
        elif options['all']:
            result1 = cleanup_expired_files()
            result2 = cleanup_old_inactive_files()
            self.stdout.write(self.style.SUCCESS(result1))
            self.stdout.write(self.style.SUCCESS(result2))
        else:
            result = cleanup_expired_files()
            self.stdout.write(self.style.SUCCESS(result))