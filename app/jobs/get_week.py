import logging

from models.model_helpers import get_tgfp_info, TGFPInfo


def get_week():
    info: TGFPInfo = get_tgfp_info()
    logging.info(f"Current week {info.current_week}")


if __name__ == "__main__":
    get_week()
