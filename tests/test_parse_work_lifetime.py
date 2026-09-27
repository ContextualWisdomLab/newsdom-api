"""Actual ASGI cancellation must retain capacity until synchronous work ends."""
import asyncio
import threading
from io import BytesIO

import httpx
import pytest
from fastapi import Request
from pypdf import PdfWriter
from test_parse_admission import _production_settings
from test_parse_endpoint import _ReadTrackingUpload

from newsdom_api.errors import MineruIncompleteOutputError
from newsdom_api.main import create_app, parse
from newsdom_api.schemas import ParseResponse


@pytest.mark.asyncio
@pytest.mark.parametrize('worker_fails', [False, True])
async def test_outer_asgi_cancellation_keeps_worker_capacity(monkeypatch, worker_fails):
    application = create_app(_production_settings(capacity=1),
                             runtime_readiness_probe=lambda: True)
    writer = PdfWriter()
    writer.add_blank_page(width=620, height=810)
    stream = BytesIO()
    writer.write(stream)
    payload = stream.getvalue()
    loop = asyncio.get_running_loop()
    started = loop.create_future()
    release = threading.Event()
    finished = threading.Event()
    calls = []

    def worker(path, **kwargs):
        calls.append(path)
        if len(calls) == 1:
            loop.call_soon_threadsafe(started.set_result, None)
            try:
                assert release.wait(5)
                assert path.exists()
                if worker_fails:
                    raise MineruIncompleteOutputError('Controlled synthetic failure')
            finally:
                finished.set()
        return ParseResponse(document_id='synthetic', pages=[])

    monkeypatch.setattr('newsdom_api.main.parse_pdf', worker)
    headers = {'Authorization': 'Bearer admission-test-token'}
    files = {'file': ('fixture.pdf', payload, 'application/pdf')}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=application),
                                base_url='http://testserver', headers=headers) as client:
        first = asyncio.create_task(client.post('/parse', files=files))
        try:
            await asyncio.wait_for(started, 5)
            first.cancel()
            for _ in range(4):
                await asyncio.sleep(0)
            second = await client.post('/parse', files=files)
            assert second.status_code == 429
            assert second.headers['Retry-After'] == '1'
            assert 'no-store' in second.headers['Cache-Control']
            assert len(calls) == 1
            assert not finished.is_set()
        finally:
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await first
            await asyncio.to_thread(finished.wait, 5)
        recovered = await client.post('/parse', files=files)
        assert recovered.status_code == 200
        assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize('worker_fails', [False, True])
@pytest.mark.parametrize('scope_cancel', [False, True])
async def test_cancelled_request_keeps_upload_until_worker_finishes(monkeypatch, worker_fails, scope_cancel):
    import asyncio
    import threading
    from io import BytesIO

    from anyio import CancelScope
    from pypdf import PdfWriter

    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=620, height=810)
    writer.write(stream)
    upload = _ReadTrackingUpload(stream.getvalue())
    loop = asyncio.get_running_loop()
    started = loop.create_future()
    release = threading.Event()
    finished = threading.Event()
    paths = []

    def worker(path, **kwargs):
        paths.append(path)
        loop.call_soon_threadsafe(started.set_result, None)
        try:
            assert release.wait(5), 'Test worker was not released'
            assert path.exists(), 'Upload removed while worker was still running'
            if worker_fails:
                raise RuntimeError('Controlled worker failure after cancellation')
        finally:
            finished.set()

    monkeypatch.setattr('newsdom_api.main.parse_pdf', worker)
    scopes = []

    async def scoped_request():
        with CancelScope() as scope:
            scopes.append(scope)
            await parse(upload, language='korean', mode='ocr', request=Request({'type': 'http'}))

    request = asyncio.create_task(scoped_request() if scope_cancel else
                                  parse(upload, language='korean', mode='ocr', request=Request({'type': 'http'})))
    try:
        await asyncio.wait_for(started, 5)
        for _ in range(2):
            if scope_cancel:
                scopes[0].cancel()
            else:
                request.cancel()
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            assert not request.done(), 'Request released before worker terminated'
            assert paths[0].exists()
    finally:
        release.set()
        if scope_cancel:
            await request
        else:
            with pytest.raises(asyncio.CancelledError):
                await request
        await asyncio.to_thread(finished.wait, 5)
    assert finished.is_set()
    assert not paths[0].exists()


def test_event_loop_shutdown_waits_for_actual_parse_thread(monkeypatch):
    import asyncio
    import threading
    from io import BytesIO

    from pypdf import PdfWriter

    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=620, height=810)
    writer.write(stream)
    upload = _ReadTrackingUpload(stream.getvalue())
    release = threading.Event()
    finished = threading.Event()
    cleanup_states = []
    from pathlib import Path

    unlink = Path.unlink

    def spy_unlink(path, *args, **kwargs):
        cleanup_states.append(finished.is_set())
        return unlink(path, *args, **kwargs)

    async def scenario():
        loop = asyncio.get_running_loop()
        started = loop.create_future()

        def worker(path, **kwargs):
            loop.call_soon_threadsafe(started.set_result, None)
            try:
                assert release.wait(5)
                assert path.exists()
            finally:
                finished.set()

        async def observe_shutdown():
            try:
                await asyncio.Future()
            finally:
                # Leave the thread live while asyncio cancels all remaining tasks.
                loop.call_later(0.02, release.set)

        monkeypatch.setattr('newsdom_api.main.parse_pdf', worker)
        asyncio.create_task(observe_shutdown())
        asyncio.create_task(parse(upload, language='korean', mode='ocr', request=Request({'type': 'http'})))
        await started

    monkeypatch.setattr(Path, 'unlink', spy_unlink)
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(scenario())
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_default_executor())
    finally:
        release.set()
        loop.close()
    assert finished.is_set()
    assert cleanup_states == [True]
