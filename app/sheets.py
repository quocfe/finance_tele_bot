import os
import asyncio
import logging
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption

logger = logging.getLogger(__name__)

# ---- Config ------------------------------------------------------------------
SERVICE_ACCOUNT_FILE = "service_account.json"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "your-spreadsheet-id")
SHEET_NAME = "bot-chitieu"

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_PATH = os.path.join(base_path, SERVICE_ACCOUNT_FILE)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---- Google Sheets client ----------------------------------------------------
_creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=SCOPES)
_client = gspread.authorize(_creds)


def _get_worksheet() -> gspread.Worksheet:
    """Mở worksheet theo tên trong spreadsheet được cấu hình."""
    spreadsheet = _client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)


async def save_to_sheet(data: dict, user_id: int) -> None:
    """
    Append một dòng chi tiêu vào Google Sheet.

    Các cột: Thời gian | User ID | Nội dung | Số tiền

    Dùng gspread (sync I/O) nhưng chạy trong thread-pool để không block event-loop.
    """

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, _append_row, data, user_id)
        logger.info(
            "Appended to sheet — user=%s item='%s' amount=%s",
            user_id,
            data["item"],
            data["amount"],
        )
    except Exception:
        logger.exception(
            "Lỗi khi ghi Google Sheet — user_id=%s data=%s", user_id, data
        )
        raise


def _append_row(data: dict, user_id: int) -> None:
    """Hàm sync — chạy trong executor."""
    worksheet = _get_worksheet()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    row = [now_str, user_id, data["item"], data["amount"]]
    worksheet.append_row(row, value_input_option=ValueInputOption.user_entered)

