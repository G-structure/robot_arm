"""SDR streaming and control logic."""

import time
import json
import threading
import numpy as np
import SoapySDR
from scipy import signal as sp_signal

from . import device as sdr_device
from . import signal as sdr_signal

class SDRStreamer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SDRStreamer, cls).__new__(cls)
        return cls._instance

    def __init__(self, app_logger=None):
        # Ensure __init__ is called only once
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.logger = app_logger
        self.sdr = None
        self.rx_stream = None
        self.is_streaming = False
        self.clients = set()
        self.streaming_thread = None
        self.lock = threading.Lock()

        # Default SDR parameters
        self.params = {
            "device_args": "driver=hackrf",
            "sample_rate": 10e6,
            "center_freq": 100e6,
            "rx_gain": 20,
            "fft_size": 1024,
            "window": "hann"
        }
        self._initialized = True

    def add_client(self, client):
        with self.lock:
            self.clients.add(client)
        if not self.is_streaming:
            self.start()

    def remove_client(self, client):
        with self.lock:
            self.clients.remove(client)
        if not self.clients:
            self.stop()

    def start(self):
        if self.is_streaming:
            return True
        
        self.logger.info("Starting SDR stream...")
        try:
            with self.lock:
                self.sdr = sdr_device.setup_sdr_device(
                    device_args=self.params["device_args"],
                    sample_rate=self.params["sample_rate"],
                    center_freq=self.params["center_freq"],
                    rx_gain=self.params["rx_gain"]
                )
                self.rx_stream = self.sdr.setupStream(SoapySDR.SOAPY_SDR_RX, SoapySDR.SOAPY_SDR_CF32)
                self.sdr.activateStream(self.rx_stream)
            
            self.is_streaming = True
            self.streaming_thread = threading.Thread(target=self._streaming_loop)
            self.streaming_thread.daemon = True
            self.streaming_thread.start()
            self.logger.info("SDR stream started.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start SDR stream: {e}")
            self.cleanup()
            return False

    def stop(self):
        if not self.is_streaming:
            return
        
        self.logger.info("Stopping SDR stream...")
        self.is_streaming = False
        if self.streaming_thread:
            self.streaming_thread.join()
        self.cleanup()
        self.logger.info("SDR stream stopped.")
        
    def cleanup(self):
        with self.lock:
            if self.sdr and self.rx_stream:
                try:
                    self.sdr.deactivateStream(self.rx_stream)
                    self.sdr.closeStream(self.rx_stream)
                except Exception as e:
                    self.logger.error(f"Error during stream deactivation: {e}")
            self.sdr = None
            self.rx_stream = None

    def _streaming_loop(self):
        buffer = np.empty(self.params["fft_size"], dtype=np.complex64)
        window = sp_signal.get_window(self.params["window"], self.params["fft_size"])
        
        while self.is_streaming:
            with self.lock:
                if not self.sdr:
                    break
                sr = self.sdr.readStream(self.rx_stream, [buffer], len(buffer), timeoutUs=int(1e6))
            
            if sr.ret > 0:
                psd_db = sdr_signal.compute_psd_db(buffer, fft_size=self.params["fft_size"], window=window)
                self.broadcast(json.dumps(psd_db.tolist()))
            elif sr.ret != SoapySDR.SOAPY_SDR_TIMEOUT:
                self.logger.warning(f"SDR stream read error: {SoapySDR.SoapySDR_errToStr(sr.ret)}")
                time.sleep(0.01)

    def broadcast(self, message):
        disconnected_clients = set()
        with self.lock:
            clients_to_broadcast = list(self.clients)

        for client in clients_to_broadcast:
            try:
                client.send(message)
            except Exception as e:
                self.logger.warning(f"WebSocket send error: {e}. Client will be removed.")
                disconnected_clients.add(client)
        
        if disconnected_clients:
            with self.lock:
                self.clients.difference_update(disconnected_clients)

    def update_settings(self, new_settings):
        was_streaming = self.is_streaming
        if was_streaming:
            self.stop()

        with self.lock:
            for key, value in new_settings.items():
                if key in self.params:
                    # Coerce to correct type
                    param_type = type(self.params[key])
                    try:
                        self.params[key] = param_type(value)
                    except ValueError:
                         self.logger.warning(f"Could not convert {value} to type {param_type} for setting {key}")
        
        if was_streaming:
            self.start()
            
    def get_status(self):
        with self.lock:
            status = self.params.copy()
            status['is_streaming'] = self.is_streaming
            status['clients'] = len(self.clients)
            if self.sdr:
                try:
                    status['sdr_info'] = sdr_device.get_device_info(self.sdr)
                except Exception as e:
                    status['sdr_info'] = f"Error getting info: {e}"
            else:
                status['sdr_info'] = "SDR not initialized"
        return status 