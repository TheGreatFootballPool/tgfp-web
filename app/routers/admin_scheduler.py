# routers/admin_scheduler.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from bots.scheduler import scheduler

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/admin/scheduler", tags=["Scheduler"])


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request):
    jobs = scheduler.get_jobs()
    return templates.TemplateResponse(
        "scheduler_jobs.j2", {"request": request, "jobs": jobs}
    )
