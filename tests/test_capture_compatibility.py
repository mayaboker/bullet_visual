from types import SimpleNamespace

import pytest

from bullet_visual.capture import ZmqShmSource


def test_old_renderer_descriptor_reports_required_restart():
    source = ZmqShmSource.__new__(ZmqShmSource)
    source.socket = SimpleNamespace(recv=lambda flags: b'descriptor')
    source.reader = SimpleNamespace(read=lambda message: (
        {'version': 3, 'session': 'a' * 32, 'width': 640, 'height': 480}, b''))
    with pytest.raises(RuntimeError, match='restart the simulation launcher'):
        source.poll()
