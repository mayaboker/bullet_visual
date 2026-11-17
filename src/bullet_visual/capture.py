"""Capture adapters normalized to BGR frames and bbox packet metadata."""
from dataclasses import dataclass
import time
from uuid import uuid4

import cv2
import numpy as np
import zmq
from bullet_image_transport.shm import FrameReader, MAX_MESSAGE_BYTES, topic_prefix

from .config import SourceConfig


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    metadata: dict


class ZmqShmSource:
    def __init__(self, config: SourceConfig):
        self.reader = FrameReader(config.topic)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.CONFLATE, 1)
        self.socket.setsockopt(zmq.MAXMSGSIZE, MAX_MESSAGE_BYTES)
        self.socket.setsockopt(zmq.SUBSCRIBE, topic_prefix(config.topic))
        self.socket.connect(config.endpoint)
        self.topic = config.topic

    def poll(self):
        try:
            message = self.socket.recv(zmq.NOBLOCK)
        except zmq.Again:
            return None
        result = self.reader.read(message)
        if result is None:
            return None
        metadata, pixels = result
        if metadata.get('version') == 3 and 'host_capture_ns' not in metadata:
            raise RuntimeError(
                'Renderer image is missing host_capture_ns. Rebuild the packaged renderer '
                'and restart the simulation launcher so Godot loads the new binary.')
        if metadata.get('version') in (1, 2):
            metadata['host_capture_ns'] = metadata['capture_ns']
        rows = np.frombuffer(pixels, dtype=np.uint8).reshape(metadata['height'], metadata['step'])
        image = rows[:, :metadata['width'] * 3].reshape(metadata['height'], metadata['width'], 3)
        if metadata['encoding'] == 'rgb8':
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            image = image.copy()
        return Frame(image, metadata)

    def close(self):
        self.reader.close()
        self.socket.close(linger=0)
        self.context.term()


class OpenCvSource:
    def __init__(self, config: SourceConfig):
        backend = cv2.CAP_GSTREAMER if config.type == 'mipi' else cv2.CAP_ANY
        device = config.pipeline if config.type == 'mipi' else config.device
        self.capture = cv2.VideoCapture(device, backend)
        if not self.capture.isOpened():
            self.capture.release()
            raise OSError(f'could not open {config.type} camera source')
        self.session = uuid4().hex
        self.sequence = 0

    def poll(self):
        ok, image = self.capture.read()
        if not ok or image is None:
            raise OSError('camera source stopped returning frames')
        self.sequence += 1
        return Frame(image, {
            'version': 1,
            'session': self.session,
            'sequence': self.sequence,
            'capture_ns': time.monotonic_ns(),
            'host_capture_ns': time.monotonic_ns(),
            'width': image.shape[1],
            'height': image.shape[0],
        })

    def close(self):
        self.capture.release()


def open_source(config: SourceConfig):
    return ZmqShmSource(config) if config.type == 'zmq_shm' else OpenCvSource(config)
