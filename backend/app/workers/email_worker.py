"""Background worker for application email notifications."""

from __future__ import annotations

import argparse
import logging
import time

from app.database.connection import SessionLocal
from app.services.email_delivery_service import deliver_pending_notifications


logger = logging.getLogger(__name__)


DEFAULT_BATCH_SIZE = 10
DEFAULT_POLL_INTERVAL = 30


def run_once(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> int:
    """Process one batch of pending email notifications.

    Returns the number of notifications processed.
    """

    db = SessionLocal()

    try:
        notifications = deliver_pending_notifications(
            db,
            limit=batch_size,
        )

        if notifications:
            logger.info(
                "Processed %d email notification(s).",
                len(notifications),
            )
        else:
            logger.debug("No pending email notifications found.")

        return len(notifications)

    except Exception:
        logger.exception("Email worker batch failed.")
        return 0

    finally:
        db.close()


def run_forever(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> None:
    """Continuously process pending email notifications."""


    logger.info(
        "Email worker started. Batch size=%d, poll interval=%ds.",
        batch_size,
        poll_interval,
    )

    try:
        while True:
            run_once(batch_size=batch_size)
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Email worker stopped gracefully.")

def main() -> None:
    """CLI entry point for the email worker."""

    parser = argparse.ArgumentParser(
        description="Application email notification worker.",
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one batch and exit.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Maximum notifications per batch (default: {DEFAULT_BATCH_SIZE}).",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL}).",
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")

    if args.interval < 1:
        parser.error("--interval must be at least 1 second")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if args.once:
        run_once(batch_size=args.batch_size)
        return

    run_forever(
        batch_size=args.batch_size,
        poll_interval=args.interval,
    )


if __name__ == "__main__":
    main()