import asyncio
import logging
import signal
import sys

try:
    from worker.app.config import worker_settings
except ModuleNotFoundError:
    from app.config import worker_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, worker_settings.WORKER_LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(worker_settings.WORKER_NAME)


class RepoMindWorker:
    """Background worker responsible for asynchronous repository tasks."""

    def __init__(self) -> None:
        self.is_running: bool = False
        self._shutdown_event: asyncio.Event = asyncio.Event()

    async def start(self) -> None:
        """Start worker polling loop."""
        self.is_running = True
        logger.info(
            "Worker started. Listening for tasks (Poll interval: %ds)...",
            worker_settings.WORKER_POLL_INTERVAL,
        )

        try:
            while not self._shutdown_event.is_set():
                await self.process_next_batch()
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=worker_settings.WORKER_POLL_INTERVAL,
                    )
                except TimeoutError:
                    pass
        finally:
            self.is_running = False
            logger.info("Worker stopped gracefully.")

    async def process_next_batch(self) -> None:
        """Process any pending background tasks."""
        logger.debug("Checking for pending repository indexing tasks...")
        # Stub for future background tasks (git clone, AST parse, indexing)

    def stop(self) -> None:
        """Signal worker to stop processing."""
        logger.info("Shutdown signal received. Stopping worker...")
        self._shutdown_event.set()


async def main() -> None:
    worker = RepoMindWorker()

    loop = asyncio.get_running_loop()

    # Register signal handlers where supported
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            # Signal handlers not implemented on Windows event loop for non-main thread
            pass

    await worker.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker terminated by user.")
