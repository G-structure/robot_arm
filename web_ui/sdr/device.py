"""Device management utilities for SoapySDR."""

import SoapySDR
from typing import Optional, Dict, Any


def setup_sdr_device(
    device_args: str,
    sample_rate: float,
    center_freq: Optional[float] = None,
    rx_gain: Optional[float] = None,
    tx_gain: Optional[float] = None,
    rx_antenna: Optional[str] = None,
    tx_antenna: Optional[str] = None,
    clock_rate: Optional[float] = None
) -> SoapySDR.Device:
    """
    Setup and configure an SDR device with common parameters.
    
    Args:
        device_args: SoapySDR device arguments string
        sample_rate: Sample rate in Hz
        center_freq: Center frequency in Hz
        rx_gain: RX gain in dB
        tx_gain: TX gain in dB  
        rx_antenna: RX antenna selection
        tx_antenna: TX antenna selection
        clock_rate: Master clock rate in Hz
        
    Returns:
        Configured SoapySDR device
    """
    sdr = SoapySDR.Device(device_args)
    
    # Set clock rate first if specified
    if clock_rate is not None:
        sdr.setMasterClockRate(clock_rate)
    
    # Configure sample rates
    sdr.setSampleRate(SoapySDR.SOAPY_SDR_RX, 0, sample_rate)
    if sdr.getNumChannels(SoapySDR.SOAPY_SDR_TX) > 0:
        sdr.setSampleRate(SoapySDR.SOAPY_SDR_TX, 0, sample_rate)
    
    # Configure frequencies
    if center_freq is not None:
        sdr.setFrequency(SoapySDR.SOAPY_SDR_RX, 0, center_freq)
        if sdr.getNumChannels(SoapySDR.SOAPY_SDR_TX) > 0:
            sdr.setFrequency(SoapySDR.SOAPY_SDR_TX, 0, center_freq)
    
    # Configure gains
    if rx_gain is not None:
        sdr.setGain(SoapySDR.SOAPY_SDR_RX, 0, rx_gain)
    if tx_gain is not None and sdr.getNumChannels(SoapySDR.SOAPY_SDR_TX) > 0:
        sdr.setGain(SoapySDR.SOAPY_SDR_TX, 0, tx_gain)
    
    # Configure antennas
    if rx_antenna is not None:
        sdr.setAntenna(SoapySDR.SOAPY_SDR_RX, 0, rx_antenna)
    if tx_antenna is not None and sdr.getNumChannels(SoapySDR.SOAPY_SDR_TX) > 0:
        sdr.setAntenna(SoapySDR.SOAPY_SDR_TX, 0, tx_antenna)
    
    return sdr


def configure_stream(
    sdr: SoapySDR.Device,
    direction: int,
    format_type: str = SoapySDR.SOAPY_SDR_CF32,
    channels: list = None
):
    """
    Configure and setup a stream for the SDR device.
    
    Args:
        sdr: SoapySDR device
        direction: Stream direction (SOAPY_SDR_RX or SOAPY_SDR_TX)
        format_type: Sample format 
        channels: List of channel indices
        
    Returns:
        Configured stream object (opaque SoapySDR stream handle)
    """
    if channels is None:
        channels = [0]
    
    stream = sdr.setupStream(direction, format_type, channels)
    return stream


def get_device_info(sdr: SoapySDR.Device) -> Dict[str, Any]:
    """
    Get comprehensive device information.
    
    Args:
        sdr: SoapySDR device
        
    Returns:
        Dictionary containing device information
    """
    info = {}
    
    # Basic device info
    info['driver'] = sdr.getDriverKey()
    info['hardware'] = sdr.getHardwareKey()
    
    # Channel counts
    info['rx_channels'] = sdr.getNumChannels(SoapySDR.SOAPY_SDR_RX)
    info['tx_channels'] = sdr.getNumChannels(SoapySDR.SOAPY_SDR_TX)
    
    # Sample rate ranges
    if info['rx_channels'] > 0:
        info['rx_sample_rate_range'] = sdr.getSampleRateRange(SoapySDR.SOAPY_SDR_RX, 0)
        info['rx_frequency_range'] = sdr.getFrequencyRange(SoapySDR.SOAPY_SDR_RX, 0)
        info['rx_gain_range'] = sdr.getGainRange(SoapySDR.SOAPY_SDR_RX, 0)
    
    if info['tx_channels'] > 0:
        info['tx_sample_rate_range'] = sdr.getSampleRateRange(SoapySDR.SOAPY_SDR_TX, 0)
        info['tx_frequency_range'] = sdr.getFrequencyRange(SoapySDR.SOAPY_SDR_TX, 0)
        info['tx_gain_range'] = sdr.getGainRange(SoapySDR.SOAPY_SDR_TX, 0)
    
    # Timing capabilities
    info['has_hardware_time'] = sdr.hasHardwareTime()
    
    return info 