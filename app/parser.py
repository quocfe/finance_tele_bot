import re
import logging

logger = logging.getLogger(__name__)

# Regex: "Tên món <số tiền>" — số tiền có thể chứa dấu chấm/phẩy và hậu tố k/K/d/đ
_EXPENSE_RE = re.compile(
    r"^(?P<item>.+?)\s+(?P<raw_amount>[\d.,]+)\s*(?P<suffix>[kKdđ]?)$"
)


def parse_expense(text: str) -> dict | None:
    """
    Parse một chuỗi chi tiêu dạng tự do thành dict {"item": str, "amount": int}.

    Hỗ trợ:
      - "Cafe 30k"          -> {"item": "Cafe",       "amount": 30000}
      - "Ăn sáng 50000"     -> {"item": "Ăn sáng",    "amount": 50000}
      - "Lương 10.000.000"  -> {"item": "Lương",       "amount": 10000000}
      - "Trà đá 15,000"     -> {"item": "Trà đá",     "amount": 15000}

    Trả về None nếu chuỗi không khớp hoặc số tiền <= 0.
    """
    if not text or not text.strip():
        return None

    text = text.strip()
    match = _EXPENSE_RE.match(text)
    if not match:
        logger.debug("Không khớp regex: %s", text)
        return None

    item = match.group("item").strip()
    raw_amount = match.group("raw_amount")
    suffix = match.group("suffix").lower()

    # Loại bỏ dấu chấm và dấu phẩy (dùng làm phân cách hàng nghìn)
    cleaned = raw_amount.replace(".", "").replace(",", "")

    try:
        amount = int(cleaned)
    except ValueError:
        logger.warning("Không thể chuyển '%s' thành số", raw_amount)
        return None

    # Hậu tố 'k' -> nhân 1000
    if suffix in ("k",):
        amount *= 1000

    if amount <= 0:
        logger.debug("Số tiền <= 0: %s", amount)
        return None

    return {"item": item, "amount": amount}

