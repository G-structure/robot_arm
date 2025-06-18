"""Signal processing utilities for SDR experiments."""

import numpy as np
from typing import Optional


def generate_cf32_pulse(num_samps: int, width: float = 5, scale_factor: float = 0.3) -> np.ndarray:
    """
    Create a sinc pulse for SDR transmission.
    
    Args:
        num_samps: Number of samples in the pulse
        width: Width parameter for the sinc function
        scale_factor: Scaling factor for the pulse amplitude
        
    Returns:
        Complex64 numpy array containing the pulse
    """
    rel_time = np.linspace(-width, width, num_samps)
    pulse = np.sinc(rel_time).astype(np.complex64)
    return pulse * scale_factor


def normalize_samples(samps: np.ndarray) -> np.ndarray:
    """
    Normalize samples by removing DC, taking magnitude, and normalizing to peak.
    
    Args:
        samps: Input samples (complex or real)
        
    Returns:
        Normalized magnitude samples
    """
    samps = samps - np.mean(samps)  # Remove DC
    samps = np.absolute(samps)  # Magnitude
    max_val = np.max(samps)
    if max_val > 0:
        samps = samps / max_val  # Normalize amplitude to peak
    return samps


def compute_psd_db(samples: np.ndarray, fft_size: Optional[int] = None, min_val_db: float = -100) -> np.ndarray:
    """
    Compute power spectral density in dB.
    
    Args:
        samples: Input samples
        fft_size: FFT size (defaults to length of samples)
        min_val_db: Minimum value in dB for clipping
        
    Returns:
        PSD in dB, fftshifted
    """
    if fft_size is None:
        fft_size = len(samples)
    
    if len(samples) >= fft_size:
        samples_for_fft = samples[:fft_size]
    else:
        samples_for_fft = np.pad(samples, (0, fft_size - len(samples)), 'constant', constant_values=(0,))
    
    spectrum = np.fft.fft(samples_for_fft, n=fft_size)
    psd_line = np.abs(spectrum)**2
    psd_line_shifted = np.fft.fftshift(psd_line)
    psd_line_db = 10 * np.log10(psd_line_shifted + 1e-12)
    psd_line_db = np.clip(psd_line_db, min_val_db, None)
    
    return psd_line_db


def cross_correlate_peak(signal1: np.ndarray, signal2: np.ndarray) -> tuple[int, float]:
    """
    Find the peak correlation between two signals.
    
    Args:
        signal1: First signal
        signal2: Second signal (template)
        
    Returns:
        Tuple of (peak_index, correlation_value)
    """
    correlation = np.correlate(signal1, signal2, mode='full')
    peak_index = np.argmax(np.abs(correlation))
    correlation_value = correlation[peak_index]
    
    # Adjust index to be relative to signal1
    adjusted_index = peak_index - len(signal2) + 1
    
    return adjusted_index, correlation_value 