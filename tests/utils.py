from typing import Any
from django import http as dj_http


def expected_x_but_got_y(expected: Any, actual: Any) -> str:
    return f"Expected {expected}, got {actual}s"


def serialize_response(response: "dj_http.HttpResponse") -> str:
    headers = "\r\n".join(
        f"{header}: {value}" for header, value in response.headers.items()
    )
    return (
        f"HTTP/1.1 {response.status_code} {response.reason_phrase}\r\n"
        f"{headers}\r\n\r\n{response.content}"
    )
