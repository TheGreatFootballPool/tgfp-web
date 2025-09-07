from fastapi import APIRouter
from config import Config
from sqlmodel import Session, select

from db import engine
from models import Team, Game
from models.model_helpers import TGFPInfo, get_tgfp_info
from tgfp_nfl import TgfpNfl, TgfpNflGame

config = Config.get_config()

router = APIRouter(prefix="/api", tags=["api"])
