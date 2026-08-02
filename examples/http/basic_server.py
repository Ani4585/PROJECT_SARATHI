"""Run a minimal PROJECT SARATHI ASGI HTTP application."""

from __future__ import annotations

from src.http import HttpApplication, Request, TextResponse, UvicornServerAdapter


async def homepage(request: Request) -> TextResponse:
    """Return a small response while demonstrating request access."""

    return TextResponse(f"PROJECT SARATHI is ready: {request.method} {request.path}")


application = HttpApplication(homepage)


if __name__ == "__main__":
    UvicornServerAdapter().run(application)
