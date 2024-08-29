# library
from io import BytesIO

import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from tgfp_nfl import TgfpNflGame
from urllib.request import urlopen


def get_image(url) -> Image:
    """ Returns an image from the url """
    response = urlopen(url)
    img_data = BytesIO(response.read())
    return Image.open(img_data)


def get_matchup_chart(espn_game: TgfpNflGame) -> str:
    """
    Get a chart for a matchup of espn and tgfp games
    @param espn_game:
    @return: filename for the chart
    """
    tie_pct: float = 100.0 - (
        espn_game.home_team_predicted_win_pct +
        espn_game.away_team_predicted_win_pct
    )
    team_labels = (
        f"{espn_game.home_team_predicted_win_pct}%",
        f"{espn_game.away_team_predicted_win_pct}%"
    )
    size_of_groups = [
        espn_game.home_team_predicted_win_pct,
        espn_game.away_team_predicted_win_pct
    ]
    image_urls = [
        espn_game.home_team.logo_url,
        espn_game.away_team.logo_url
    ]
    colors = (
        f"#{espn_game.home_team.color}",
        f"#{espn_game.away_team.color}"
    )
    # Create a donut
    _, _, auto_texts = plt.pie(
        size_of_groups,
        labels=team_labels,
        autopct='%1.1f',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 20, 'fontweight': 'bold'},
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
    )
    title = plt.title("TGFP Match Predictor")
    title.set_fontsize(20)
    plt.tight_layout()

    for _, (auto_label, url) in enumerate(zip(auto_texts, image_urls)):
        img = get_image(url)
        imagebox = OffsetImage(img, zoom=0.14)
        auto_label.set_visible(False)
        x, y = auto_label.get_position()
        x = x*.7
        y = y*.7
        auto_label.set_position((x, y))
        box = AnnotationBbox(
            imagebox,
            auto_label.get_position(),
            frameon=False,
            xycoords='data',
            boxcoords="data",
            pad=0.1
        )
        plot_ctx = plt.gcf()
        plot_ctx.gca().add_artist(box)

    # add a circle at the center to transform it in a donut chart
    my_circle = plt.Circle((0, 0), 0.80, color='white')
    plt.figtext(
        0.04,
        0.02,
        f'* {tie_pct:.2f}% chance of a tie -- **Powered by ESPN Analytics',
        fontsize=13,
        fontstyle='italic'
    )
    p = plt.gcf()
    p.gca().add_artist(my_circle)
    filename = f"{espn_game.event_id}-pct-win.png"
    plt.savefig(filename, dpi=300)
    plt.close()
    return filename
