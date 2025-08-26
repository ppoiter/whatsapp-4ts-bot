from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import timedelta, datetime
from config.settings import GAMEWEEK_SCHEDULE
from utils.date_utils import get_uk_timezone

class SchedulerService:
    def __init__(self, message_service):
        self.message_service = message_service
    
    def schedule_deadline_summaries(self):
        """Schedule summary messages for all gameweek deadlines"""
        scheduler = BackgroundScheduler(timezone=get_uk_timezone())
        
        for gw_num, start_date, deadline in GAMEWEEK_SCHEDULE:
            # Schedule summary 1 minute after deadline
            summary_time = deadline + timedelta(minutes=1)
            
            # Only schedule if time is in the future
            uk_tz = get_uk_timezone()
            now = datetime.now(uk_tz).replace(tzinfo=None)
            uk_summary = uk_tz.localize(summary_time).replace(tzinfo=None)
            
            if uk_summary > now:
                trigger = DateTrigger(run_date=summary_time, timezone=uk_tz)
                scheduler.add_job(
                    lambda gw=gw_num: self.message_service.send_deadline_summary(gw),
                    trigger=trigger,
                    id=f'gw_{gw_num}_summary',
                    name=f'Gameweek {gw_num} Summary'
                )
                print(f"Scheduled summary for GW{gw_num} at {summary_time}")
        
        return scheduler