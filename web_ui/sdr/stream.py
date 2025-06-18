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
            "window": "hann",
            "baseband_filter_bw": 0  # 0 = auto, or specify bandwidth in Hz
        }
        # Rate limiting for UI responsiveness
        self.update_rate = 10     # Updates per second
        self.last_update_time = 0
        self.frame_counter = 0
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
                    rx_gain=self.params["rx_gain"],
                    baseband_filter_bw=self.params["baseband_filter_bw"]
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
                current_time = time.time()
                self.frame_counter += 1
                
                # Rate limit: only send data at specified update rate
                if current_time - self.last_update_time >= (1.0 / self.update_rate):
                    psd_db = sdr_signal.compute_psd_db(buffer, fft_size=self.params["fft_size"], window=window)
                    # Reduce data size by decimating the spectrum
                    decimated_psd = psd_db[::2]  # Take every other point
                    self.broadcast(json.dumps(decimated_psd.tolist()))
                    self.last_update_time = current_time
                # Continue reading to prevent buffer overflow, but don't broadcast every frame
                    
            elif sr.ret != SoapySDR.SOAPY_SDR_TIMEOUT:
                self.logger.warning(f"SDR stream read error: {sr.ret}")
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
                    if key == "sample_rate":
                        # HackRF practical limits over USB 2.0
                        max_sample_rate = 15e6  # 15 MSPS is more reliable than 20 MSPS
                        min_sample_rate = 1e6   # 1 MSPS minimum
                        value = max(min_sample_rate, min(max_sample_rate, float(value)))
                        self.logger.info(f"Sample rate clamped to {value/1e6:.1f} MSPS (USB 2.0 limit)")
                    
                    elif key == "baseband_filter_bw":
                        # HackRF baseband filter limits (per MAX2837 chip)
                        if value > 0:  # 0 = auto mode
                            min_filter_bw = 1.75e6   # 1.75 MHz minimum per HackRF docs
                            max_filter_bw = 28e6     # 28 MHz maximum
                            value = max(min_filter_bw, min(max_filter_bw, float(value)))
                            self.logger.info(f"Baseband filter BW set to {value/1e6:.2f} MHz")
                        else:
                            self.logger.info("Baseband filter set to AUTO mode")
                    
                    # Coerce to correct type
                    param_type = type(self.params[key])
                    try:
                        self.params[key] = param_type(value)
                    except ValueError:
                         self.logger.warning(f"Could not convert {value} to type {param_type} for setting {key}")
                elif key == "update_rate":
                    # Special handling for update rate
                    try:
                        self.update_rate = max(1, min(30, int(value)))  # Limit between 1-30 FPS
                    except ValueError:
                        self.logger.warning(f"Invalid update rate: {value}")
        
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