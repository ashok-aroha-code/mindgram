import time
import datetime

class ScraperTimer:
    """Utility to track and format scraper execution time."""
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()
        return self

    def stop(self):
        self.end_time = time.time()
        return self

    @property
    def elapsed_seconds(self):
        if not self.start_time:
            return 0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def format_elapsed(self):
        seconds = self.elapsed_seconds
        return str(datetime.timedelta(seconds=round(seconds)))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
