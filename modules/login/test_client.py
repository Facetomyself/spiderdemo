import json
import unittest
from http.cookiejar import CookieJar

from modules.login.client import (
    LOGIN_URL,
    LoginClient,
    _gate_cookie,
    build_login_request,
    session_cookie_set,
)


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> bool:
        return False


class _Opener:
    def __init__(self, body: dict) -> None:
        self.body = body
        self.requests = []
        self.jar = CookieJar()

    def open(self, request, timeout=None):
        self.requests.append((request, timeout))
        if self.body.get("success") is True:
            cookie = _gate_cookie("not-used")
            cookie.name = "sessionid"
            cookie.value = "session-placeholder"
            self.jar.set_cookie(cookie)
        return _Response(json.dumps(self.body).encode("utf-8"))


class LoginRequestTest(unittest.TestCase):
    def test_body_is_only_username_and_password(self) -> None:
        request = build_login_request("name", "secret")
        self.assertEqual(LOGIN_URL, request.full_url)
        self.assertEqual("POST", request.get_method())
        self.assertEqual("application/json", request.get_header("Content-type"))
        self.assertEqual("https://www.spiderdemo.cn", request.get_header("Origin"))
        self.assertEqual({"username": "name", "password": "secret"}, json.loads(request.data.decode("utf-8")))

    def test_rejected_login_has_no_session_cookie(self) -> None:
        opener = _Opener({"success": False, "message": "用户名或密码错误"})
        client = LoginClient(opener=opener)
        client.jar = opener.jar
        result = client.login("name", "secret")
        self.assertFalse(result["success"])
        self.assertFalse(result["session_cookie_set"])
        self.assertFalse(session_cookie_set(opener.jar))

    def test_accepted_login_marks_session_cookie(self) -> None:
        opener = _Opener({"success": True, "message": "登录成功", "user": {"username": "name"}})
        client = LoginClient(opener=opener)
        client.jar = opener.jar
        result = client.login("name", "secret")
        self.assertTrue(result["success"])
        self.assertTrue(result["session_cookie_set"])


if __name__ == "__main__":
    unittest.main()
