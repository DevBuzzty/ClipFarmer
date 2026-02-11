import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_id, status, progress=0):
        self.tasks[task_id] = {
            "status": status,
            "progress": progress,
            "result": None,
            "error": None,
            "updated_at": time.time()
        }
        logger.info(f"Task {task_id} created: {status}")

    def update_task(self, task_id, status=None, progress=None, result=None, error=None):
        if task_id in self.tasks:
            if status: self.tasks[task_id]["status"] = status
            if progress is not None: self.tasks[task_id]["progress"] = progress
            if result is not None: self.tasks[task_id]["result"] = result
            if error is not None: self.tasks[task_id]["error"] = error
            self.tasks[task_id]["updated_at"] = time.time()
            if error:
                logger.error(f"Task {task_id} failed: {error}")
            else:
                logger.info(f"Task {task_id} updated: {status} ({progress}%)")

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def cleanup_old_tasks(self, max_age_seconds=3600):
        now = time.time()
        to_delete = [tid for tid, t in self.tasks.items() if now - t["updated_at"] > max_age_seconds]
        for tid in to_delete:
            del self.tasks[tid]
            logger.info(f"Task {tid} cleaned up")
