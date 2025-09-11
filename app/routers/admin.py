# routers/admin_scheduler.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from jobs.create_picks import create_the_picks
from jobs.scheduler import job_scheduler, schedule_jobs

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/admin", tags=["Scheduler"])


@router.get("/job_schedule", response_class=HTMLResponse)
def job_schedule(request: Request):
    jobs = job_scheduler.get_jobs()
    return templates.TemplateResponse(
        "admin_job_schedule.j2", {"request": request, "jobs": jobs}
    )


@router.get("/job_create_picks")
def job_create_picks(request: Request):
    create_the_picks()
    redirect_url = request.url_for("picks")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@router.get("/job_schedule_jobs")
async def job_schedule_jobs(request: Request):
    await schedule_jobs()
    redirect_url = request.url_for("job_schedule")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response
