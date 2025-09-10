from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from config import Config
from db import engine
from sqlmodel import Session, select

from models import Player
from models.model_helpers import TGFPInfo, get_tgfp_info

config = Config.get_config()


class EmailSchema(BaseModel):
    email: List[EmailStr]
    first_name: str


template_folder: Path = Path(__file__).parent.parent / "templates"
conf = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=config.MAIL_PASSWORD,
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    TEMPLATE_FOLDER=template_folder,
)

router = APIRouter(prefix="/mail", tags=["mail"])

templates = Jinja2Templates(directory=str(template_folder))


def _get_session():
    with Session(engine) as session:
        yield session


async def _get_latest_info():
    """Returns the current TGFPInfo object"""
    return get_tgfp_info()


async def _verify_player(request: Request) -> int:
    """Make sure we have a player session, otherwise, get one"""
    cookie = request.cookies.get("tgfp-discord-id")
    if cookie:
        player_discord_id: Optional[int] = int(cookie)
        return player_discord_id

    raise HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/login"},
    )


@router.get("/send_welcome")
async def send_welcome(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    info: TGFPInfo = Depends(_get_latest_info),
):
    player: Player = Player.by_discord_id(session, discord_id)
    context = {"player": player, "info": info}
    return templates.TemplateResponse(
        request=request, name="send_welcome.j2", context=context
    )


@router.post("/welcome_email")
async def welcome_email(
    request: Request,
    email_model: EmailSchema | None = None,
    first_name: str | None = Form(default=None),
    email: EmailStr | None = Form(default=None),
) -> JSONResponse:
    print(request.url)

    # Support both JSON body (email_model) and HTML form posts
    if email_model is not None:
        recipients: List[EmailStr] = email_model.email
        first = email_model.first_name
    elif email is not None and first_name is not None:
        recipients = [email]
        first = first_name
    else:
        return JSONResponse(
            status_code=422, content={"message": "first_name and email are required"}
        )

    body = {
        "first_name": first,
        "discord_img_url": str(
            request.url_for("static", path="images/discord_login.png")
        ),
        "homepage_url": str(request.url_for("home")),
        "rules_url": str(request.url_for("rules")),
        "admin_email": config.MAIL_FROM,
        "discord_invite_link": "https://discord.gg/f25zmnF",
    }
    # noinspection PyTypeChecker
    message = MessageSchema(
        subject="Welcome to the Great Football Pool!",
        recipients=recipients,
        template_body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="email_welcome.j2")
    return JSONResponse(status_code=200, content={"message": "email has been sent"})


@router.get("/send_standings")
async def send_standings(
    request: Request,
    discord_id: int = Depends(_verify_player),
    session: Session = Depends(_get_session),
    info: TGFPInfo = Depends(_get_latest_info),
):
    """Serve a minimal standalone page with a single text field for standings commentary.

    Note: The `send_standings.j2` template will be a minimal template (not extending `base.j2`).
    This route only renders the form page; the POST handler will be added in a later step.
    """
    session.info["TGFPInfo"] = info
    player: Player = Player.by_discord_id(session, discord_id)
    players: List[Player] = Player.active_players(session)
    players.sort(key=lambda x: x.total_points, reverse=True)
    context = {"player": player, "info": info, "active_players": players}
    return templates.TemplateResponse(
        request=request,
        name="send_standings.j2",
        context=context,
    )


@router.post("/standings_email")
async def standings_email(
    request: Request,
    email_model: EmailSchema | None = None,
    first_name: str | None = Form(default=None),
    email: EmailStr | None = Form(default=None),
) -> JSONResponse:
    pass
