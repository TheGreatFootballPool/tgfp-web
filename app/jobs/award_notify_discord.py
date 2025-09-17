import datetime

from discord_webhook import DiscordWebhook, DiscordEmbed
from sqlmodel import Session

from db import engine
from models import PlayerAward
from config import Config

config = Config.get_config()


def get_award_embed(award: PlayerAward) -> DiscordEmbed:
    embed = DiscordEmbed(
        title="New Award Announcement",
        description=f"🎉 Congratulations to <@{award.player.discord_id}> 🎉",
        colour=0xAD4500,
    )

    embed.set_author(
        name="TGFP Award Bot",
        url="https://tgfp.us",
        icon_url="https://tgfp.us/static/images/tgfp_logo_background.png",
    )

    embed.add_embed_field(
        name="⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯",
        value=f"**Award:**: 🥇{award.award.name} 🥇\n**Season**: {award.season}\n**Week**: {award.week_no}",
        inline=False,
    )

    embed.set_image(url=f"https://tgfp.us/static/images/{award.award.icon}-med.png")
    return embed


def send_award_notification(session: Session):
    for player_award in PlayerAward.awards_needing_notification(session):
        player_award.notified_at = datetime.datetime.now(datetime.UTC)
        session.add(player_award)
        award_embed = get_award_embed(player_award)
        webhook = DiscordWebhook(url=config.DISCORD_AWARD_BOT_WEBHOOK_URL)
        webhook.add_embed(award_embed)
        webhook.execute()
    session.commit()


if __name__ == "__main__":
    send_award_notification()
