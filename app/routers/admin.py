# routers/admin_scheduler.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette import status
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlmodel import Session

from db import engine
from jobs.create_picks import create_the_picks
from jobs.update_all_scores import update_all_scores
from jobs.sync_team_records import sync_the_team_records
from jobs.scheduler import job_scheduler, schedule_jobs
from models.model_helpers import current_week_info

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


@router.get("/job_update_all_scores")
def job_update_all_scores(request: Request):
    with Session(engine) as session:
        update_all_scores(session)
    redirect_url = request.url_for("home")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@router.get("/job_sync_team_records")
def job_sync_team_records(request: Request):
    sync_the_team_records()
    redirect_url = request.url_for("home")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response


@router.get("/job_schedule_jobs")
def job_schedule_jobs(request: Request):
    schedule_jobs(week_info=current_week_info())
    redirect_url = request.url_for("job_schedule")
    response = RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)
    return response
