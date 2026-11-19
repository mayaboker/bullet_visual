import json
from types import SimpleNamespace

import pytest

from bullet_visual.publisher import BboxPublisher


def test_publisher_builds_current_packet_without_network():
    sent = []
    publisher = BboxPublisher.__new__(BboxPublisher)
    publisher.socket = SimpleNamespace(send_multipart=lambda parts, flags: sent.append(parts))

    metadata = {'version': 3, 'session': 'a' * 32, 'sequence': 1,
                'capture_ns': 123, 'host_capture_ns': 456, 'width': 640, 'height': 480,
                'drone_id': 'drone_1', 'header': {'fid': 77}}
    assert publisher.publish(metadata, (1, 2, 3, 4), 'camera/front/image')
    assert sent[0][0] == b'tracking/front/bbox'
    packet = json.loads(sent[0][1])
    assert packet['schema_version'] == 3
    assert packet['capture_ns'] == 456
    assert packet['fid'] == 77
    assert packet['bbox'] == {'x': 1, 'y': 2, 'width': 3, 'height': 4}


def test_no_target_packet_keeps_fid():
    sent = []
    publisher = BboxPublisher.__new__(BboxPublisher)
    publisher.socket = SimpleNamespace(send_multipart=lambda parts, flags: sent.append(parts))
    metadata = {'session': 'a' * 32, 'sequence': 5, 'host_capture_ns': 10,
                'width': 640, 'height': 480, 'header': {'fid': 80}}
    assert publisher.publish(metadata, None, 'camera/front/image')
    assert json.loads(sent[0][1])['bbox'] is None
    assert json.loads(sent[0][1])['fid'] == 80
