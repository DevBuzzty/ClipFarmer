import threading
import uuid

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_id, status="starting", progress=0):
        self.tasks[task_id] = {
            "status": status,
            "progress": progress,
            "result": None,
            "error": None
        }

    def update_task(self, task_id, status=None, progress=None, result=None, error=None):
        if task_id in self.tasks:
            if status: self.tasks[task_id]["status"] = status
            if progress is not None: self.tasks[task_id]["progress"] = progress
            if result is not None: self.tasks[task_id]["result"] = result
            if error: self.tasks[task_id]["error"] = error

    def get_task(self, task_id):
        return self.tasks.get(task_id)
