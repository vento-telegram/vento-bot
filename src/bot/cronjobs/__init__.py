from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def init_jobs_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.start()
