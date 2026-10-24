"""Probe init and one signed page. Prints only status fields, not page numbers."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlencode

from modules.runtime import SpiderSession

from solve import CHALLENGE, page_tokens


async def main() -> None:
    session = SpiderSession()
    async with session.async_client() as client:
        init = await client.get(
            f"/authentication/api/symmetry_challenge/init/?challenge_type={CHALLENGE}"
        )
        body = init.json()
        data = body.get("page_data")
        print(
            "init",
            init.status_code,
            "success",
            body.get("success"),
            "page_data_len",
            len(data) if isinstance(data, list) else None,
            "error",
            body.get("error"),
            "message",
            body.get("message"),
        )
        stamp = int(time.time() * 1000)
        signed = page_tokens(2, stamp)
        query = urlencode(
            {
                "challenge_type": CHALLENGE,
                "aes_sign": signed["aes_sign"],
                "des_sign": signed["des_sign"],
                "t": signed["t"],
            }
        )
        response = await client.get(
            f"/authentication/api/symmetry_challenge/page/2/?{query}",
            headers={
                "X-Aes-Token": signed["aes_token"],
                "X-Des-Token": signed["des_token"],
            },
        )
        page = response.json()
        numbers = page.get("page_data")
        print(
            "page2",
            response.status_code,
            "success",
            page.get("success"),
            "page_data_len",
            len(numbers) if isinstance(numbers, list) else None,
            "error",
            page.get("error"),
            "message",
            page.get("message"),
        )


if __name__ == "__main__":
    asyncio.run(main())
