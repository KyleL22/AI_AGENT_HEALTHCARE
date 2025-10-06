from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
from .config import TIMEZONE, REPORT_HOUR, REPORT_MINUTE
import logging
logger = logging.getLogger(__name__)

def start_scheduler(job_fn):
    sched = BackgroundScheduler(timezone=timezone(TIMEZONE))
    sched.add_job(job_fn, 'cron', hour=REPORT_HOUR, minute=REPORT_MINUTE, id='daily_report')
    sched.start()
    logger.info(f"Scheduler started for {REPORT_HOUR:02d}:{REPORT_MINUTE:02d} {TIMEZONE}")
    return sched
