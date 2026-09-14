from dataclasses import dataclass
from pathlib import Path
import re

from dotenv import dotenv_values


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"

TOKEN_PATTERN = re.compile(r"^\d+:[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: frozenset[int]


def _parse_admin_ids(raw_value: str) -> frozenset[int]:
    raw_value = raw_value.strip()

    if not raw_value:
        return frozenset()

    admin_ids: set[int] = set()

    for item in raw_value.split(","):
        item = item.strip()

        if not item or not item.isdigit():
            raise RuntimeError(
                "ADMIN_IDS is invalid. Use numeric Telegram user IDs separated by commas."
            )

        admin_ids.add(int(item))

    return frozenset(admin_ids)


def load_settings() -> Settings:
    if not ENV_FILE.exists():
        raise RuntimeError(
            ".env was not found. Run setup.bat first."
        )

    values = dotenv_values(ENV_FILE)

    bot_token = (values.get("BOT_TOKEN") or "").strip()
    admin_ids_raw = (values.get("ADMIN_IDS") or "").strip()

    if (
        not bot_token
        or bot_token == "PASTE_YOUR_BOT_TOKEN_HERE"
        or not TOKEN_PATTERN.fullmatch(bot_token)
    ):
        raise RuntimeError(
            "BOT_TOKEN is missing or invalid. Run setup.bat again."
        )

    return Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(admin_ids_raw),
    )


settings = load_settings()
