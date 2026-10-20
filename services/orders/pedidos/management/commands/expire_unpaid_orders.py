import time

from django.core.management.base import BaseCommand, CommandError

from pedidos.views import _expire_due_unpaid_orders


class Command(BaseCommand):
    help = "Reject unpaid orders after their five-minute payment window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Keep checking for expired orders until the process is stopped.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=10,
            help="Seconds between checks when --loop is used (default: 10).",
        )

    def handle(self, *args, **options):
        interval = options["interval"]
        if interval < 1:
            raise CommandError("--interval must be at least one second.")

        while True:
            expired_count = _expire_due_unpaid_orders()
            if expired_count:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Rejected {expired_count} expired unpaid order(s)."
                    )
                )
            if not options["loop"]:
                return
            time.sleep(interval)
