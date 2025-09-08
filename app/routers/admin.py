# routers/admin_scheduler.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from jobs.scheduler import job_scheduler

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/admin", tags=["Scheduler"])


@router.get("/job_schedule", response_class=HTMLResponse)
def job_schedule(request: Request):
    jobs = job_scheduler.get_jobs()
    return templates.TemplateResponse(
        "admin_job_schedule.j2", {"request": request, "jobs": jobs}
    )
