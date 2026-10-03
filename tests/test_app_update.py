import hashlib
import threading

import pytest

from superyt import app_update


def publication(version='v99.0.0'):
    prefix = f'https://github.com/{app_update.REPO}/releases/download/{version}/'
    return {'tag_name': version, 'body': 'Cambios', 'assets': [
        {'name': name, 'browser_download_url': prefix + name}
        for name in (app_update.INSTALLER, 'SHA256SUMS.txt')
    ]}


def test_stable_versions_compare_numerically():
    assert app_update.version_tuple('v1.10.0') > app_update.version_tuple('1.9.9')
    with pytest.raises(ValueError):
        app_update.version_tuple('v2.0.0-beta')


def test_new_release_requires_installer_checksum(monkeypatch):
    monkeypatch.setattr(app_update, 'release', lambda *_: publication())
    monkeypatch.setattr(app_update, 'read_text', lambda *_: 'invalid')
    with pytest.raises(ValueError, match='SHA256'):
        app_update.check_release(threading.Event())
    monkeypatch.setattr(app_update, 'read_text',
                        lambda *_: 'a' * 64 + '  ' + app_update.INSTALLER)
    result = app_update.check_release(threading.Event())
    assert result.version == 'v99.0.0'
    assert result.sha256 == 'a' * 64


def test_current_version_does_not_download(monkeypatch):
    monkeypatch.setattr(app_update, 'release', lambda *_: publication('v' + app_update.__version__))
    assert app_update.check_release(threading.Event()) is None


def test_rejects_external_installer(monkeypatch):
    info = publication()
    info['assets'][0]['browser_download_url'] = 'https://example.org/setup.exe'
    monkeypatch.setattr(app_update, 'release', lambda *_: info)
    with pytest.raises(ValueError, match='inesperada'):
        app_update.check_release(threading.Event())


def test_download_verifies_before_activating(tmp_path, monkeypatch):
    import io

    from superyt import releases

    monkeypatch.setattr(app_update, 'data_dir', lambda: tmp_path)
    monkeypatch.setattr(releases, 'request', lambda *_: io.BytesIO(b'installer'))
    info = app_update.AppRelease('v2.0.0', '', 'https://example.org', '0' * 64)
    with pytest.raises(RuntimeError, match='verificación'):
        app_update.fetch_installer(info, threading.Event(), lambda _: None)
    assert not list(tmp_path.rglob('*.exe'))
    assert not list(tmp_path.rglob('*.partial'))
    info = app_update.AppRelease('v2.0.0', '', 'https://example.org',
                                hashlib.sha256(b'installer').hexdigest())
    assert app_update.fetch_installer(info, threading.Event(), lambda _: None).read_bytes() == b'installer'


def test_development_build_cannot_install():
    assert not app_update.can_install()
    with pytest.raises(RuntimeError, match='Windows'):
        app_update.launch_installer(None)
