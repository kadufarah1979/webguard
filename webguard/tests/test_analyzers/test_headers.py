"""Testes do analisador de cabeçalhos de segurança."""

from __future__ import annotations

import pytest

from webguard.analyzers.passive.headers import analyze_headers
from webguard.core.models import Severity


@pytest.mark.asyncio
async def test_csp_missing(make_scan_record):
    """CSP ausente deve emitir finding Medium."""
    record = make_scan_record(headers={})
    findings = await analyze_headers(record)

    csp_findings = [f for f in findings if f.id == "HDR-CSP-MISSING"]
    assert len(csp_findings) == 1
    assert csp_findings[0].severity == Severity.MEDIUM


@pytest.mark.asyncio
async def test_csp_unsafe_inline(make_scan_record):
    """CSP com unsafe-inline deve emitir finding."""
    record = make_scan_record(headers={
        "content-security-policy": "default-src 'self'; script-src 'self' 'unsafe-inline'"
    })
    findings = await analyze_headers(record)

    unsafe = [f for f in findings if f.id == "HDR-CSP-UNSAFE-INLINE"]
    assert len(unsafe) == 1
    assert "'unsafe-inline'" in unsafe[0].evidence


@pytest.mark.asyncio
async def test_csp_unsafe_eval(make_scan_record):
    """CSP com unsafe-eval deve emitir finding."""
    record = make_scan_record(headers={
        "content-security-policy": "script-src 'self' 'unsafe-eval'"
    })
    findings = await analyze_headers(record)

    unsafe = [f for f in findings if f.id == "HDR-CSP-UNSAFE-EVAL"]
    assert len(unsafe) == 1


@pytest.mark.asyncio
async def test_csp_wildcard(make_scan_record):
    """CSP com wildcard em script-src deve emitir High."""
    record = make_scan_record(headers={
        "content-security-policy": "script-src *"
    })
    findings = await analyze_headers(record)

    wildcard = [f for f in findings if f.id == "HDR-CSP-WILDCARD"]
    assert len(wildcard) == 1
    assert wildcard[0].severity == Severity.HIGH


@pytest.mark.asyncio
async def test_csp_good(make_scan_record):
    """CSP completa e segura não deve emitir warnings de CSP."""
    record = make_scan_record(headers={
        "content-security-policy": (
            "default-src 'self'; script-src 'self'; "
            "object-src 'none'; base-uri 'self'"
        ),
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=(), microphone=()",
        "cross-origin-opener-policy": "same-origin",
        "cross-origin-embedder-policy": "require-corp",
        "cross-origin-resource-policy": "same-origin",
        "cache-control": "no-store",
    })
    findings = await analyze_headers(record)

    # Deve ter apenas informativos
    non_info = [f for f in findings if f.severity not in (Severity.INFO, Severity.LOW)]
    # base-uri está presente, object-src 'none' presente
    assert len(non_info) == 0, f"Unexpected findings: {[f.id for f in non_info]}"


@pytest.mark.asyncio
async def test_hsts_missing(make_scan_record):
    """HSTS ausente deve emitir Medium."""
    record = make_scan_record(headers={})
    findings = await analyze_headers(record)

    hsts = [f for f in findings if f.id == "HDR-HSTS-MISSING"]
    assert len(hsts) == 1
    assert hsts[0].severity == Severity.MEDIUM


@pytest.mark.asyncio
async def test_hsts_short_max_age(make_scan_record):
    """HSTS com max-age curto deve emitir Low."""
    record = make_scan_record(headers={
        "strict-transport-security": "max-age=86400"
    })
    findings = await analyze_headers(record)

    short = [f for f in findings if f.id == "HDR-HSTS-SHORT"]
    assert len(short) == 1
    assert short[0].severity == Severity.LOW


@pytest.mark.asyncio
async def test_x_frame_options_missing(make_scan_record):
    """X-Frame-Options ausente deve emitir Medium."""
    record = make_scan_record(headers={})
    findings = await analyze_headers(record)

    xfo = [f for f in findings if f.id == "HDR-XFO-MISSING"]
    assert len(xfo) == 1


@pytest.mark.asyncio
async def test_xcto_nosniff_correct(make_scan_record):
    """X-Content-Type-Options: nosniff não deve emitir warning."""
    record = make_scan_record(headers={"x-content-type-options": "nosniff"})
    findings = await analyze_headers(record)

    xcto = [f for f in findings if "XCTO" in f.id]
    assert len(xcto) == 0


@pytest.mark.asyncio
async def test_referrer_policy_unsafe_url(make_scan_record):
    """Referrer-Policy: unsafe-url deve emitir Medium."""
    record = make_scan_record(headers={"referrer-policy": "unsafe-url"})
    findings = await analyze_headers(record)

    rp = [f for f in findings if f.id == "HDR-RP-UNSAFE"]
    assert len(rp) == 1
    assert rp[0].severity == Severity.MEDIUM
