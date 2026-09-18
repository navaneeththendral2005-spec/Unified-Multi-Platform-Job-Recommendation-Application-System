"""Background worker for application email notifications.

The worker is responsible for continuously invoking the email delivery
engine. Retry scheduling, stale-delivery recovery, and SMTP delivery remain
inside the delivery service.
"""

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
    """Process one batch of eligible email notifications.

    The delivery service determines which notifications are currently
    eligible, including newly pending notifications and scheduled retries.

    Returns the number of notifications processed.
    """

    db = SessionLocal()

    try:
        notifications = deliver_pending_notifications(
            db,
            limit=batch_size,
        )

        processed_count = len(notifications)

        if processed_count:
            logger.info(
                "Processed %d email notification(s).",
                processed_count,
            )
        else:
            logger.debug(
                "No eligible email notifications found."
            )

        return processed_count

    except Exception:
        logger.exception(
            "Email worker batch failed."
        )
        return 0

    finally:
        db.close()


def run_forever(
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> None:
    """Continuously process eligible email notifications."""

    logger.info(
        "Email worker started | batch_size=%d | poll_interval=%ds",
        batch_size,
        poll_interval,
    )

    try:
        while True:
            run_once(
                batch_size=batch_size,
            )

            time.sleep(
                poll_interval,
            )

    except KeyboardInterrupt:
        logger.info(
            "Email worker stopped gracefully."
        )


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
        help=(
            "Maximum notifications processed per batch "
            f"(default: {DEFAULT_BATCH_SIZE})."
        ),
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=(
            "Polling interval in seconds "
            f"(default: {DEFAULT_POLL_INTERVAL})."
        ),
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error(
            "--batch-size must be at least 1"
        )

    if args.interval < 1:
        parser.error(
            "--interval must be at least 1 second"
        )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    if args.once:
        run_once(
            batch_size=args.batch_size,
        )
        return

    run_forever(
        batch_size=args.batch_size,
        poll_interval=args.interval,
    )


if __name__ == "__main__":
    main()