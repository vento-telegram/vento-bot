from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.cronjobs.daily_topup import run_daily_topup


async def init_jobs_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(run_daily_topup, CronTrigger(hour=21, minute=0))  # UTC
    scheduler.start()
