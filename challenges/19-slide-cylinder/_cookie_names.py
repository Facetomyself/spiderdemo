"""Print Set-Cookie names from the captcha endpoints. No values."""

from modules.runtime import SpiderSession


def names(response) -> list[str]:
    raw = response.headers.get_list("set-cookie")
    found = []
    for item in raw:
        found.append(item.split("=", 1)[0])
    return found


def main() -> None:
    session = SpiderSession()
    with session.client(
        headers={
            "Referer": "https://www.spiderdemo.cn/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge"
        }
    ) as client:
        page = client.get("/captcha/slide_cylinder_challenge?challenge_type=slide_cylinder_challenge")
        init = client.get(
            "/captcha/api/slide_cylinder_challenge/init/",
            params={"challenge_type": "slide_cylinder_challenge"},
        )
        image = client.get("/captcha/api/slide_cylinder_challenge/captcha_image/")
        print("page", page.status_code, names(page))
        print("init", init.status_code, names(init))
        print("image", image.status_code, names(image))
        jar = sorted({cookie.name for cookie in client.cookies.jar})
        print("jar", ",".join(jar))


if __name__ == "__main__":
    main()
