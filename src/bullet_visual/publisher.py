"""Publish bounded red-target detections with camera capture identity."""
import json

import zmq
from bullet_simulation_protocol import validate_endpoint

BBOX_TOPIC = b'tracking/front/bbox'


class BboxPublisher:
    def __init__(self, endpoint):
        validate_endpoint(endpoint)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDHWM, 64)
        self.socket.bind(endpoint)

    def publish(self, metadata, bbox, image_topic):
        width, height = metadata['width'], metadata['height']
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise ValueError('invalid image dimensions')
        if bbox is not None:
            x, y, w, h = bbox
            if any(type(v) is not int for v in bbox) or min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
                raise ValueError('bbox outside image')
        capture_ns = metadata.get('host_capture_ns')
        if type(capture_ns) is not int or capture_ns <= 0:
            raise ValueError('host camera timestamp required')
        packet = dict(schema_version=3, image_topic=image_topic, session=metadata['session'],
                      sequence=metadata['sequence'], capture_ns=capture_ns,
                      width=width, height=height, drone_id=metadata.get('drone_id'),
                      bbox=None if bbox is None else dict(zip(('x', 'y', 'width', 'height'), bbox, strict=True)))
        try:
            self.socket.send_multipart([BBOX_TOPIC, json.dumps(packet, allow_nan=False, separators=(',', ':')).encode()],
                                       flags=zmq.NOBLOCK)
        except zmq.Again:
            return False
        return True

    def close(self):
        self.socket.close(linger=0)
        self.context.term()
