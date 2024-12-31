from apscheduler.schedulers.background import BackgroundScheduler
from tracking import check_prices
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler()
    
    # 添加定时任务，每小时检查一次价格
    scheduler.add_job(
        check_prices,
        'interval',
        hours=1,
        next_run_time=datetime.now(),  # 立即开始第一次运行
        id='check_prices',
        replace_existing=True
    )
    
    # 启动调度器
    try:
        scheduler.start()
        logger.info("价格检查调度器已启动")
    except Exception as e:
        logger.error(f"启动调度器失败: {str(e)}")

if __name__ == "__main__":
    start_scheduler()
