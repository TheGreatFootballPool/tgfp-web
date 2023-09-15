""" FastAPI Web Server for The Great Football Pool """

from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="8b5a86ed-2c1a-4290-b0d6-f02e274017a5")


@app.get("/")
async def index(request: Request):
    """ Home page route """
    return templates.TemplateResponse("index.j2",  {
        "request": request,
        "week_no": 2,
        "page_title": "Home Page"
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8822)
