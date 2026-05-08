import json
import queue
import threading
import traceback
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.task import Task
from app.utils.time import utc_now

TaskHandler = Callable[[Task, Session], dict]


class TaskQueue:
    def __init__(self) -> None:
        self._queue: queue.Queue[int] = queue.Queue()
        self._handlers: dict[str, TaskHandler] = {}
        self._worker: threading.Thread | None = None
        self._lock = threading.Lock()
        self._started = False

    def register(self, task_type: str, handler: TaskHandler) -> None:
        self._handlers[task_type] = handler

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()
            self._started = True

    def enqueue(self, task_id: int) -> None:
        self.start()
        self._queue.put(task_id)

    def _run(self) -> None:
        while True:
            task_id = self._queue.get()
            try:
                self._execute(task_id)
            finally:
                self._queue.task_done()

    def _execute(self, task_id: int) -> None:
        db = SessionLocal()
        try:
            task = db.get(Task, task_id)
            if task is None:
                return
            handler = self._handlers.get(task.type)
            if handler is None:
                task.status = "failed"
                task.error_message = f"No handler registered for task type: {task.type}"
                task.finished_at = utc_now()
                db.commit()
                return
            if task.status == "cancelled":
                task.finished_at = utc_now()
                db.commit()
                return
            task.status = "running"
            task.started_at = utc_now()
            task.error_message = ""
            db.commit()
            try:
                result = handler(task, db)
                task = db.get(Task, task_id)
                if task is None:
                    return
                if task.status == "cancelled":
                    task.progress = min(task.progress, 100.0)
                    task.result_json = json.dumps(result, ensure_ascii=False)
                    task.finished_at = utc_now()
                    db.commit()
                    return
                task.status = "done"
                task.progress = 100.0
                task.result_json = json.dumps(result, ensure_ascii=False)
                task.finished_at = utc_now()
                db.commit()
            except Exception as exc:
                db.rollback()
                task = db.get(Task, task_id)
                if task is None:
                    return
                task.retry_count += 1
                task.error_message = f"{exc}\n{traceback.format_exc(limit=5)}"
                if task.retry_count <= task.max_retries:
                    task.status = "pending"
                    db.commit()
                    self.enqueue(task.id)
                else:
                    task.status = "failed"
                    task.finished_at = utc_now()
                    db.commit()
        finally:
            db.close()


task_queue = TaskQueue()
