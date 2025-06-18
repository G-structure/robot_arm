# WASM Waterfall Analysis & Integration Plan

## Executive Summary

This document analyzes the maia-wasm waterfall implementation and evaluates the requirements for integrating it into the existing robot arm web UI to replace the current JavaScript-based spectrum visualizer.

## Current Web UI Architecture

### Data Flow
1. **Backend (Python)**: 
   - `web_ui/sdr/stream.py` - Uses SoapySDR to interface with HackRF SDR
   - Reads IQ samples, computes FFT, converts to dB
   - Broadcasts spectrum data via WebSocket as JSON arrays
   - Rate-limited to 1-30 FPS

2. **Frontend (JavaScript)**:
   - `web_ui/static/spectrum.js` - Canvas 2D-based waterfall & spectrum
   - Real-time data visualization with configurable colormaps
   - Features: pause, colormap switching, max hold, averaging
   - Uses `turbo`, `fosphor`, `viridis`, and other colormaps

### Current Limitations
- Canvas 2D rendering (not GPU-accelerated)
- Limited to ~30 FPS update rates
- JSON data transmission overhead
- Simple FFT processing without advanced windowing
- No zoom/pan functionality

## Maia-WASM Waterfall Architecture

### Core Components

#### 1. **WebGL2 Rendering Engine** (`render/engine.rs`)
- High-performance GPU-accelerated rendering
- Texture-based waterfall storage (4096×512 texture)
- Shader-based colormap application
- Multiple render objects: waterfall, spectrum, frequency labels

#### 2. **Waterfall Core** (`waterfall.rs`)
- 4096-point spectrum resolution 
- 512-line waterfall buffer
- Hardware-accelerated zoom/pan
- Real-time frequency axis labeling
- Multiple display modes (waterfall, spectrum, both)

#### 3. **Data Reception** (`websocket.rs`)
- Binary ArrayBuffer data transmission (not JSON)
- Automatic reconnection on connection loss
- Direct Float32Array processing

#### 4. **User Interaction** (`waterfall_interaction.rs`)
- Mouse/touch gesture support (drag, pinch-to-zoom)
- Frequency tuning via UI interaction
- Real-time pan/zoom with hardware acceleration

### Key Advantages
- **Performance**: 60+ FPS rendering via WebGL2
- **Efficiency**: Binary data transmission vs JSON
- **Features**: Hardware zoom/pan, frequency interaction
- **Quality**: Advanced windowing, better spectrum processing
- **Professional**: Frequency axis, multiple colormaps, channel markers

## Maia-WASM Data Interface (Detailed)

### WebSocket Protocol

**Endpoint**: `ws://hostname:port/waterfall`

**Connection**: 
- Auto-connects based on current page URL (`window.location`)
- Handles HTTP/HTTPS protocol detection (ws/wss)
- Automatic reconnection on connection loss

### Data Format Requirements

#### 1. **Transport Format**
- **Protocol**: Binary WebSocket (NOT text/JSON)
- **Binary Type**: `ArrayBuffer` (set via `ws.set_binary_type(web_sys::BinaryType::Arraybuffer)`)
- **JavaScript Reception**: Converted to `js_sys::Float32Array`

#### 2. **Data Content**
```rust
// From websocket.rs onmessage handler:
let data = event.data().dyn_into::<js_sys::ArrayBuffer>()?;
waterfall.put_waterfall_spectrum(&js_sys::Float32Array::new(&data));
```

#### 3. **Expected Data Format**
- **Type**: `Float32Array` (32-bit IEEE 754 floating point)
- **Byte Order**: Native endian
- **Length**: Exactly **4096 elements** (16,384 bytes total)
- **Units**: **Linear power** (NOT dB!)

#### 4. **Data Processing in WASM**
```rust
// From waterfall.rs put_waterfall_spectrum():
pub fn put_waterfall_spectrum(&mut self, spectrum_linear: &js_sys::Float32Array) {
    // Copy linear power data to texture buffer
    spectrum_linear.copy_to(spectrum_texture);
    
    // Convert to "dB" for shader processing
    for x in spectrum_texture.iter_mut() {
        if *x != 0.0 {
            *x = x.log10();  // Convert to log scale (without 10x factor)
        }
    }
}
```

### Maia-SDR Backend Data Generation

The maia-httpd backend generates data as follows:

```rust
// From spectrometer.rs
fn buffer_u64fp_to_f32(buffer: &[u64], scale: f32) -> Bytes {
    buffer.iter()
        .flat_map(|&x| {
            let exponent = (x >> 56) as u8;
            let value = x & ((1u64 << 56) - 1);
            let y = value << (2 * exponent);
            let z = y as f32 * scale;  // Convert to linear power
            z.to_ne_bytes().into_iter()  // Serialize as Float32 bytes
        })
        .collect()
}
```

### Key Differences from Current Robot Arm Implementation

| Aspect | Current Robot Arm | Maia-WASM Required |
|--------|-------------------|-------------------|
| **Transport** | Text WebSocket | Binary WebSocket |
| **Format** | JSON array | Float32Array bytes |
| **Data Type** | String/Number | Binary Float32 |
| **Data Unit** | dB values | Linear power values |
| **Array Size** | Variable (decimated) | Fixed 4096 elements |
| **Byte Count** | ~2KB JSON text | 16,384 bytes binary |

## Integration Requirements

### 1. **WASM Module Compilation**
```bash
# In maia-wasm directory
wasm-pack build --target web --out-dir pkg
```

### 2. **Backend Data Format Changes**
Current: JSON array of dB values
```python
decimated_psd = psd_db[::2]  # Take every other point
self.broadcast(json.dumps(decimated_psd.tolist()))
```

Required: Binary Float32Array of linear power values
```python
# Convert to linear power (not dB)
linear_power = 10**(psd_db / 10.0)
# Send as binary ArrayBuffer
self.broadcast_binary(linear_power.astype(np.float32).tobytes())
```

### 3. **Frontend HTML Changes**
Current waterfall canvas:
```html
<canvas id="waterfall"></canvas>
```

Required structure (from maia-wasm example):
```html
<canvas id="canvas"></canvas>
<form class="ui">
  <fieldset class="waterfall_levels">
    <input type="number" id="waterfall_min" value="35">
    <input type="number" id="waterfall_max" value="85">
  </fieldset>
  <select id="colormap_select">
    <option>Turbo</option>
    <option>Viridis</option>
    <option>Inferno</option>
  </select>
  <input type="checkbox" id="waterfall_show_waterfall" checked>
  <input type="checkbox" id="waterfall_show_spectrum">
</form>
```

### 4. **JavaScript Integration**
Replace current spectrum.js initialization:
```javascript
// Current
spectrum = new Spectrum('waterfall', {spectrumPercent: 50});

// New WASM approach
import init, { make_waterfall_with_ui } from './maia-wasm/pkg/maia_wasm.js';
await init();
make_waterfall_with_ui('canvas');
```

### 5. **CSS Styling Integration**
Maia-wasm expects specific CSS classes and styling. Current robot arm theme would need:
- `.ui` form styling
- `.waterfall_levels` input styling  
- Dark theme color variables
- Canvas sizing and positioning

## Implementation Strategy

### Key Insight: No WASM Modifications Required

**The maia-wasm code does NOT need to be modified at all.** It's designed as a reusable library with configurable entry points:

1. **WebSocket Endpoint is Auto-Configured**: WASM automatically constructs WebSocket URL based on current page location
2. **Canvas ID is Configurable**: Can be called with any canvas ID via `make_waterfall_with_ui(canvas_id)`
3. **HTML Element IDs Are Standard**: Uses predictable IDs like `waterfall_min`, `waterfall_max`, `colormap_select`

### Simple Integration Approach

#### 1. Backend Integration (Flask/Python)
Add new binary WebSocket endpoint:
```python
# In server.py - add new endpoint
@sock.route('/waterfall')  
def waterfall_binary_socket(ws):
    """Binary waterfall data for WASM."""
    logger.info("WASM Waterfall WebSocket client connected.")
    sdr_streamer.add_binary_client(ws)
    try:
        while True:
            message = ws.receive()
            # Handle control messages if needed
    except Exception as e:
        logger.info(f"WASM Waterfall client disconnected: {e}")
    finally:
        sdr_streamer.remove_binary_client(ws)
```

Extend SDR streamer for binary data:
```python
# In sdr/stream.py - add methods
def add_binary_client(self, client):
    with self.lock:
        if not hasattr(self, 'binary_clients'):
            self.binary_clients = set()
        self.binary_clients.add(client)

def broadcast_binary(self, linear_power_data):
    """Send binary Float32Array data to WASM clients"""
    if not hasattr(self, 'binary_clients'):
        return
    binary_data = linear_power_data.astype(np.float32).tobytes()
    disconnected = set()
    for client in self.binary_clients:
        try:
            client.send(binary_data, mode='binary')
        except Exception as e:
            disconnected.add(client)
    self.binary_clients.difference_update(disconnected)

# Modify _streaming_loop to also send binary data
def _streaming_loop(self):
    # ... existing code ...
    if sr.ret > 0:
        # ... existing JSON broadcast ...
        
        # Add binary broadcast for WASM
        if hasattr(self, 'binary_clients') and self.binary_clients:
            # Convert dB to linear power for WASM
            linear_power = 10**(psd_db / 10.0)
            self.broadcast_binary(linear_power)
```

#### 2. Frontend Integration (HTML/JS)
Add WASM waterfall alongside existing one:
```html
<!-- Existing waterfall (can keep during transition) -->
<canvas id="waterfall"></canvas>

<!-- New WASM waterfall -->
<canvas id="wasm-waterfall"></canvas>
<div class="wasm-waterfall-controls">
    <input type="number" id="waterfall_min" value="35">
    <input type="number" id="waterfall_max" value="85">
    <select id="colormap_select">
        <option>Turbo</option>
        <option>Viridis</option>
        <option>Inferno</option>
    </select>
    <input type="checkbox" id="waterfall_show_waterfall" checked>
    <input type="checkbox" id="waterfall_show_spectrum">
</div>
```

JavaScript integration:
```javascript
// Add to script.js
import init, { make_waterfall_with_ui } from './static/maia-wasm/maia_wasm.js';

async function initWasmWaterfall() {
    try {
        await init();
        make_waterfall_with_ui('wasm-waterfall');
        console.log('WASM waterfall initialized');
    } catch (error) {
        console.error('Failed to initialize WASM waterfall:', error);
    }
}

// Initialize when SDR section is ready
document.addEventListener('DOMContentLoaded', () => {
    // ... existing initialization ...
    initWasmWaterfall();
});
```

#### 3. CSS Theme Integration
Override WASM styles to match robot arm theme:
```css
/* WASM Waterfall Styling */
#wasm-waterfall {
    background: #000;
    border: 1px solid #00ff00;
    width: 100%;
    height: 400px;
}

.wasm-waterfall-controls {
    background: #1a1a1a;
    padding: 10px;
    border: 1px solid #333;
}

.wasm-waterfall-controls input,
.wasm-waterfall-controls select {
    background: #1a1a1a;
    color: #00ff00;
    border: 1px solid #333;
    font-family: 'Share Tech Mono', monospace;
}

.wasm-waterfall-controls input:focus,
.wasm-waterfall-controls select:focus {
    border-color: #00ff00;
    outline: none;
}
```

### Deployment Steps

1. **Compile WASM module**:
   ```bash
   cd robot_arm/maia-sdr-main/maia-wasm
   wasm-pack build --target web --out-dir ../../web_ui/static/maia-wasm
   ```

2. **Add binary WebSocket endpoint** to Flask app

3. **Extend SDR streamer** for binary data transmission

4. **Update HTML template** with WASM elements and required IDs

5. **Add JavaScript ES6 import** and initialization

6. **Style integration** with CSS overrides

## Technical Challenges

### 1. **Data Format Conversion**
- Current: dB values in JSON → Required: Linear power in binary
- Backend requires significant rework of `_streaming_loop()`
- Must maintain backward compatibility during transition

### 2. **WebSocket Binary Support**
- Current Flask-Sock may need configuration for binary data
- Need to handle both JSON (controls) and binary (waterfall) on same connection
- Or implement separate WebSocket endpoints

### 3. **UI Theme Integration**  
- Maia-wasm has its own UI paradigm
- Robot arm UI uses dark theme with specific color scheme
- Need custom CSS integration without breaking existing layout

### 4. **Bundle Size**
- WASM module adds ~500KB-1MB to page load
- Consider lazy loading for SDR functionality
- May impact initial page load time

### 5. **Browser Compatibility**
- Requires WebGL2 support (modern browsers only)
- May need graceful fallback to current Canvas 2D implementation
- Mobile device performance considerations

## Benefits of This Approach

### Zero WASM Code Changes
- **Reusable Library**: maia-wasm is designed as a library, not a monolithic app
- **Standard APIs**: Uses WebSocket and Canvas APIs that work with any server
- **Configurable Entry Points**: `make_waterfall_with_ui()` is designed for integration
- **Future Updates**: Easy to update to newer WASM versions without code changes

### Gradual Migration Path
- **Side-by-Side**: Can run both waterfalls simultaneously during testing
- **Low Risk**: Easy to revert if issues arise
- **Incremental**: Can test performance before fully switching over
- **Backward Compatibility**: Existing JSON endpoint remains functional

### Technical Advantages
- **Performance**: 60+ FPS WebGL2 rendering vs 30 FPS Canvas 2D
- **Efficiency**: Binary data transmission reduces bandwidth
- **Features**: Hardware-accelerated zoom/pan, frequency interaction
- **Professional**: Real frequency axis, multiple colormaps, better UX

## Implementation Summary

The maia-wasm waterfall can be integrated **without modifying any WASM code**. The integration is straightforward and low-risk:

### Required Changes
1. **Backend**: Add `/waterfall` WebSocket endpoint for binary data
2. **SDR Streamer**: Extend to broadcast binary Float32Array data
3. **Frontend**: Add WASM canvas and required HTML elements with correct IDs
4. **JavaScript**: Import and initialize WASM module
5. **CSS**: Style overrides to match robot arm theme

### Key Success Factors
1. **Binary Data Pipeline**: HackRF → SoapySDR → WebSocket (binary) → WASM
2. **Element ID Matching**: Use standard IDs expected by WASM (`waterfall_min`, `colormap_select`, etc.)
3. **Theme Integration**: CSS overrides to maintain robot arm aesthetic
4. **Gradual Migration**: Run both waterfalls side-by-side initially

### Data Format Conversion
- **Current**: JSON array of dB values `[psd_db[0], psd_db[1], ...]`
- **WASM**: Binary Float32Array of linear power values `10**(psd_db/10.0)`

This approach provides significant performance improvements (60+ FPS WebGL2 vs 30 FPS Canvas 2D) with minimal development risk and no WASM modifications required. 