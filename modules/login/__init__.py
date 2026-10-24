"""Login protocol module.

Call LoginClient.login, or login_from_env to read the project-root .env.
The client does not mint cs_stable_gate.
"""

from .client import (
    GATE_COOKIE,
    LOGIN_URL,
    ORIGIN,
    SESSION_COOKIE,
    USER_STATS_URL,
    LoginClient,
    LoginError,
    build_login_request,
    login_from_env,
    session_cookie_set,
)
from .env import PASSWORD_KEY, USERNAME_KEY, credentials, env_path, load_dotenv, project_root

__all__ = [
    "GATE_COOKIE",
    "LOGIN_URL",
    "ORIGIN",
    "PASSWORD_KEY",
    "SESSION_COOKIE",
    "USER_STATS_URL",
    "USERNAME_KEY",
    "LoginClient",
    "LoginError",
    "build_login_request",
    "credentials",
    "env_path",
    "load_dotenv",
    "login_from_env",
    "project_root",
    "session_cookie_set",
]
