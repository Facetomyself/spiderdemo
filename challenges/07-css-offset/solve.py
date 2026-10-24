"""CSS1_challenge: restore digit order from local CSS offsets and submit the sum."""

from __future__ import annotations

import asyncio
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from modules.runtime import SpiderSession, collect_pages, public_result

CHALLENGE = "CSS1_challenge"
ORIGIN_PAGE = "/css_anti/CSS1_challenge?challenge_type=CSS1_challenge"
INIT_URL = "/css_anti/api/challenge/init/?challenge_type=" + CHALLENGE
SUBMIT_URL = "/css_anti/api/challenge/submit/"
PAGE_URL = "/css_anti/api/" + CHALLENGE + "/page/{page}/?challenge_type=" + CHALLENGE
UNIT_PX = 15
HERE = Path(__file__).resolve().parent
HEADERS = {"Referer": "https://www.spiderdemo.cn" + ORIGIN_PAGE}


class CssError(ValueError):
    """The offset stylesheet could not be reduced to one integer."""


class _UnknownVar(CssError):
    pass


def _add(left, right):
    if left[1] != right[1] and left[1] is not None and right[1] is not None:
        raise CssError("unit mismatch")
    return (left[0] + right[0], left[1] or right[1])


def _mul(left, right):
    if left[1] and right[1]:
        raise CssError("length times length")
    return (left[0] * right[0], left[1] or right[1])


def _div(left, right):
    if right[1]:
        raise CssError("divide by length")
    if right[0] == 0:
        raise CssError("divide by zero")
    return (left[0] / right[0], left[1])


class _Expr:
    def __init__(self, text: str, env: dict[str, tuple[float, str | None]]) -> None:
        self.text = text
        self.n = len(text)
        self.i = 0
        self.env = env

    def parse(self) -> tuple[float, str | None]:
        value = self._expr()
        self._skip()
        if self.i != self.n:
            raise CssError("trailing css")
        return value

    def _skip(self) -> None:
        while self.i < self.n and self.text[self.i].isspace():
            self.i += 1

    def _eat(self, token: str) -> bool:
        self._skip()
        if self.text.startswith(token, self.i):
            self.i += len(token)
            return True
        return False

    def _peek(self) -> str:
        self._skip()
        if self.i >= self.n:
            return ""
        return self.text[self.i]

    def _expr(self) -> tuple[float, str | None]:
        value = self._term()
        while True:
            if self._eat("+"):
                value = _add(value, self._term())
            elif self._eat("-"):
                other = self._term()
                value = _add(value, (-other[0], other[1]))
            else:
                break
        return value

    def _term(self) -> tuple[float, str | None]:
        value = self._factor()
        while True:
            if self._eat("*"):
                value = _mul(value, self._factor())
            elif self._eat("/"):
                value = _div(value, self._factor())
            else:
                break
        return value

    def _factor(self) -> tuple[float, str | None]:
        if self._eat("-"):
            value = self._factor()
            return (-value[0], value[1])
        if self._eat("+"):
            return self._factor()
        if self._eat("("):
            value = self._expr()
            if not self._eat(")"):
                raise CssError("unclosed paren")
            return value
        if self._peek().isalpha():
            return self._call()
        return self._number()

    def _call(self) -> tuple[float, str | None]:
        start = self.i
        while self.i < self.n and self.text[self.i].isalpha():
            self.i += 1
        name = self.text[start:self.i]
        if not self._eat("("):
            raise CssError("expected call")
        if name == "var":
            self._skip()
            end = self.i
            while end < self.n and self.text[end] not in ",)":
                end += 1
            key = self.text[self.i:end].strip()
            self.i = end
            if not self._eat(")"):
                raise CssError("unclosed var")
            if key not in self.env:
                raise _UnknownVar(key)
            return self.env[key]
        if name == "calc":
            value = self._expr()
            if not self._eat(")"):
                raise CssError("unclosed calc")
            return value
        if name in ("min", "max"):
            args = [self._expr()]
            while self._eat(","):
                args.append(self._expr())
            if not self._eat(")"):
                raise CssError("unclosed " + name)
            pick = min if name == "min" else max
            return pick(args, key=lambda item: item[0])
        raise CssError("unknown func")

    def _number(self) -> tuple[float, str | None]:
        self._skip()
        start = self.i
        while self.i < self.n and (self.text[self.i].isdigit() or self.text[self.i] == "."):
            self.i += 1
        if start == self.i:
            raise CssError("expected number")
        number = float(self.text[start:self.i])
        if self.text.startswith("px", self.i):
            self.i += 2
            return (number, "px")
        return (number, None)


def _px(value: tuple[float, str | None]) -> float:
    if value[1] not in (None, "px"):
        raise CssError("unexpected unit")
    if value[1] is None and value[0] != 0:
        raise CssError("bare number")
    return value[0]


def _declarations(style_text: str) -> list[tuple[str, str]]:
    match = re.search(r"\{(.*)\}", style_text, re.S)
    body = match.group(1) if match else style_text
    found: list[tuple[str, str]] = []
    cursor = 0
    while True:
        name_match = re.search(r"(--[A-Za-z0-9_-]+)\s*:", body[cursor:])
        if not name_match:
            break
        start = cursor + name_match.end()
        depth = 0
        end = start
        while end < len(body):
            char = body[end]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == ";" and depth == 0:
                break
            end += 1
        found.append((name_match.group(1), body[start:end].strip()))
        cursor = end + 1
    return found


def css_variables(style_text: str) -> dict[str, float]:
    pending = _declarations(style_text)
    env: dict[str, tuple[float, str | None]] = {}
    for _ in range(len(pending) + 1):
        later: list[tuple[str, str]] = []
        for name, expr in pending:
            try:
                env[name] = _Expr(expr, env).parse()
            except _UnknownVar:
                later.append((name, expr))
        if not later:
            pending = []
            break
        if len(later) == len(pending):
            break
        pending = later
    if pending:
        raise CssError("unresolved css variable")
    return {name: _px(value) for name, value in env.items()}


def _shift(style: str, env: dict[str, float]) -> float:
    if not style:
        return 0.0
    match = re.search(r"(?:^|;)\s*(left|right)\s*:\s*([^;]+)", style, re.I)
    if not match:
        return 0.0
    side, raw = match.group(1).lower(), match.group(2).strip()
    value = _px(_Expr(raw, {key: (px, "px") for key, px in env.items()}).parse())
    return -value if side == "right" else value


class _Digits(HTMLParser):
    def __init__(self, env: dict[str, float]) -> None:
        super().__init__(convert_charrefs=True)
        self.env = env
        self.chars: list[tuple[str, float]] = []
        self.stack: list[float] = []
        self.style_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "style":
            self.style_depth += 1
            return
        if tag == "span":
            style = ""
            for key, value in attrs:
                if key == "style" and value:
                    style = value
            self.stack.append(_shift(style, self.env))

    def handle_endtag(self, tag: str) -> None:
        if tag == "style" and self.style_depth:
            self.style_depth -= 1
        elif tag == "span" and self.stack:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if self.style_depth:
            return
        shift = self.stack[-1] if self.stack else 0.0
        for char in data:
            if char.isdigit():
                self.chars.append((char, shift))


def decode_html(html: str) -> int:
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.I | re.S))
    env = css_variables(style) if style else {}
    parser = _Digits(env)
    parser.feed(html)
    parser.close()
    if not parser.chars:
        raise CssError("no digits")
    placed: list[tuple[int, int, str]] = []
    for index, (char, shift) in enumerate(parser.chars):
        slot = index + shift / UNIT_PX
        nearest = round(slot)
        if abs(slot - nearest) > 1e-6:
            raise CssError("offset is not a whole digit")
        placed.append((nearest, index, char))
    placed.sort()
    slots = [item[0] for item in placed]
    if len(slots) != len(set(slots)):
        raise CssError("digit slots overlap")
    return int("".join(item[2] for item in placed))


def decode_item(item: object) -> int:
    if isinstance(item, bool):
        raise CssError("bad page item")
    if isinstance(item, int):
        return item
    if isinstance(item, str):
        return decode_html(item) if "<" in item else int(item)
    if isinstance(item, dict):
        html = item.get("display_html")
        if isinstance(html, str):
            return decode_html(html)
    raise CssError("bad page item")


def _self_check() -> None:
    plain = decode_html("6444")
    swapped = decode_html(
        "<style>:root { --offset-0-3505: calc(((3 * 3 * 5px) + 1px - 1px));"
        " --offset-1-5749: calc(min((3 * 3 * 5px), (3 * 3 * 5px)));"
        " --neg-2-2306: calc(-1 * var(--offset-1-5749)); }</style>"
        '<span style="position:relative;left:var(--offset-0-3505)">5</span>02'
        '<span style="position:relative;left:var(--neg-2-2306)">9</span>'
    )
    if (plain, swapped) != (6444, 9025):
        raise CssError("decoder self-check failed")


async def _fetch_numbers(client, page: int) -> list[int]:
    delay = 0.5
    for _ in range(8):
        response = await client.get(PAGE_URL.format(page=page))
        if response.status_code == 429:
            await asyncio.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        response.raise_for_status()
        payload = response.json()
        if payload.get("success") is not True:
            message = str(payload.get("error") or payload.get("message") or "page failed")
            raise CssError(message)
        data = payload.get("page_data")
        if not isinstance(data, list) or len(data) != 10:
            raise CssError("unexpected page size")
        return [decode_item(item) for item in data]
    raise CssError("rate limited")


def _accepted(payload: dict) -> bool:
    if payload.get("is_correct") is True or payload.get("correct") is True:
        return True
    message = str(payload.get("message") or payload.get("msg") or "")
    return "正确" in message and "不正确" not in message and "错误" not in message


async def _collect(session: SpiderSession, total: int) -> dict[int, list[int]]:
    async with session.async_client(HEADERS) as client:

        async def fetch_page(page: int) -> list[int]:
            return await _fetch_numbers(client, page)

        return await collect_pages(fetch_page, range(1, total + 1), concurrency=4)


def main() -> None:
    _self_check()
    session = SpiderSession()
    with session.client(HEADERS) as client:
        init = client.get(INIT_URL)
        init.raise_for_status()
        init_payload = init.json()
    if init_payload.get("success") is not True:
        raise CssError("init failed")
    total = int(init_payload["total_pages"])
    init_page = [decode_item(item) for item in init_payload["page_data"]]
    pages = asyncio.run(_collect(session, total))
    if sorted(pages) != list(range(1, total + 1)):
        raise CssError("missing pages")
    if pages[1] != init_page:
        raise CssError("page 1 does not match init")
    answer = sum(number for page in pages.values() for number in page)
    with session.client(HEADERS) as client:
        submitted = client.post(
            SUBMIT_URL,
            json={"challenge_type": CHALLENGE, "answer": answer},
        )
        submitted.raise_for_status()
        body = submitted.json()
    public = public_result(body)
    (HERE / "result.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not _accepted(body):
        raise CssError("submit was not accepted")
    print("pages", total, "numbers", total * 10, "accepted", True)


if __name__ == "__main__":
    main()
