"""Collector — coleta HTTP e monta ScanRecord (ADE-5, L-5)."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from webguard.core.guard import RequestGuard
from webguard.core.models import (
    CollectError,
    CookieInfo,
    Mode,
    ScanContext,
    ScanRecord,
)

MAX_REDIRECTS = 10
MAX_BODY_SIZE = 2 * 1024 * 1024  # 2MB
DEFAULT_TIMEOUT = 15.0
USER_AGENT = "WebGuard/1.0 (Passive & Active Security Scanner; +https://github.com/webguard)"


class Collector:
    """Coleta a resposta HTTP e monta o ScanRecord."""

    async def collect(
        self,
        url: str,
        guard: RequestGuard,
        ctx: ScanContext,
    ) -> ScanRecord | CollectError:
        """Busca a URL, segue redirects, coleta metadados."""
        # Normalizar URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        redirect_chain: list[str] = []
        current_url = url
        final_response: httpx.Response | None = None

        try:
            # Seguir redirects manualmente para registrar a cadeia
            for _ in range(MAX_REDIRECTS):
                if ctx.is_cancelled():
                    return CollectError(
                        reason="cancelled",
                        detail="Scan cancelado pelo usuário.",
                        url=current_url,
                    )

                response = await guard.request(
                    "GET",
                    current_url,
                    headers={"User-Agent": USER_AGENT, "Origin": "https://evil.example"},
                    timeout=DEFAULT_TIMEOUT,
                    follow_redirects=False,
                )

                if response.is_redirect:
                    redirect_chain.append(current_url)
                    location = response.headers.get("location", "")
                    if not location:
                        break
                    # Resolver URL relativa
                    if location.startswith("/"):
                        parsed = urlparse(current_url)
                        location = f"{parsed.scheme}://{parsed.netloc}{location}"
                    current_url = location
                else:
                    final_response = response
                    break
            else:
                return CollectError(
                    reason="too_many_redirects",
                    detail=f"Mais de {MAX_REDIRECTS} redirecionamentos.",
                    url=url,
                )

            if final_response is None:
                final_response = response  # type: ignore[possibly-undefined]

        except httpx.TimeoutException:
            return CollectError(
                reason="timeout",
                detail=f"Timeout de {DEFAULT_TIMEOUT}s excedido.",
                url=current_url,
            )
        except httpx.ConnectError as e:
            return CollectError(
                reason="connection_refused",
                detail=str(e),
                url=current_url,
            )
        except httpx.ConnectTimeout:
            return CollectError(
                reason="timeout",
                detail="Timeout ao conectar.",
                url=current_url,
            )
        except Exception as e:
            return CollectError(
                reason="unexpected_error",
                detail=str(e),
                url=current_url,
            )

        # Extrair cookies
        cookies = self._extract_cookies(final_response)

        # Truncar body
        body = final_response.text[:MAX_BODY_SIZE] if final_response.text else ""

        return ScanRecord(
            target_url=url,
            final_url=current_url,
            redirect_chain=redirect_chain,
            response_status=final_response.status_code,
            response_headers=dict(final_response.headers),
            response_body=body,
            cookies=cookies,
            tls=None,  # Preenchido pela sub-02
            timestamp=datetime.now(timezone.utc),
            mode=guard.mode,
            request_log=list(ctx.request_log),
        )

    def _extract_cookies(self, response: httpx.Response) -> list[CookieInfo]:
        """Extrai CookieInfo dos headers Set-Cookie."""
        cookies: list[CookieInfo] = []

        for header_value in response.headers.get_list("set-cookie"):
            cookie = self._parse_set_cookie(header_value)
            if cookie:
                cookies.append(cookie)

        return cookies

    def _parse_set_cookie(self, header: str) -> CookieInfo | None:
        """Parse simplificado de Set-Cookie."""
        parts = header.split(";")
        if not parts:
            return None

        # Primeiro campo: name=value
        name_value = parts[0].strip()
        if "=" not in name_value:
            return None

        name, value = name_value.split("=", 1)
        name = name.strip()
        value = value.strip()

        # Atributos
        secure = False
        httponly = False
        samesite: str | None = None
        domain = ""
        path = "/"
        expires: datetime | None = None

        for part in parts[1:]:
            part = part.strip().lower()
            if part == "secure":
                secure = True
            elif part == "httponly":
                httponly = True
            elif part.startswith("samesite="):
                samesite = part.split("=", 1)[1].strip()
            elif part.startswith("domain="):
                domain = part.split("=", 1)[1].strip()
            elif part.startswith("path="):
                path = part.split("=", 1)[1].strip()

        return CookieInfo(
            name=name,
            value_snippet=value[:20],
            domain=domain,
            path=path,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
            expires=expires,
        )
