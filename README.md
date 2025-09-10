# Ethernet TCP Verification for AXI4-Stream Image Processing IP

## 1) Overview
This repository provides a **verification environment that integrates AXI4-Stream–based image processing IP with Ethernet TCP on FPGA**, and a **Python pixel-wise validation pipeline**.  
The primary goal is to **send frames from a PC to the FPGA over TCP, run them through AXI DMA ↔ AXI4-Stream IP, bring results back over TCP, and verify outputs at the pixel level in Python**.

**Status by version**
- **V1 – Header → DDR → TCP (2-frame test): _Completed_**  
  *For V1 verification, we also exercised a teammate’s **Bicubic image IP** to sanity-check AXI4-Stream formatting and end-to-end flow.* See: **[Bicubic IP (GitHub)][bicubic_ip]**.
- **V2 – TCP RX → DDR → TCP TX (loopback): _In progress_**
- **V3 – TCP RX → DDR → (optional DMA→AXIS IP→DDR) → TCP TX (7,220 frames): _In progress_**

### Minimal dataflow
```
PC ──TCP──> PS(DDR) ──MM2S DMA──> AXI4-Stream IP ──S2MM DMA──> PS(DDR) ──TCP──> PC
^ ^
|---------------------- DDR Buffers ---------------------|
```

## 2) Repository Structure
```
Ethernet_TCP_Verification/
│── v1_Header_Test_workspace /
│ ├── src  # for vitis application project
│ └── scripts  # python scripts for RAW API
```

---

## 3) System Architecture
- **PC (Client)**: Sends raw frames (`.bin/.raw`) via TCP and receives processed frames; runs **pixel-wise validators**.  
- **FPGA – PS (MPSoC/Zynq)**: lwIP RAW TCP server for RX/TX; manages **DDR buffers** and **AXI DMA**.  
- **FPGA – PL**: **AXI4-Stream image IP** (e.g., FSRCNN layer, color converter, *Bicubic*).  
- **Dataflow**: `PC → TCP → PS(DDR) → DMA(MM2S) → AXIS IP → DMA(S2MM) → PS(DDR) → TCP → PC`

---

## 4) Versions

### V1 — Header-Based Transmission (2 frames) — ✅ Completed
- **Flow**: `.h` (pre-loaded) → DDR → TCP → PC  
- **Goal**: Verify **TX path**, DDR→TCP send pipeline, and cache/flush discipline.  
- **Note**: To sanity-check AXI4-Stream formatting in the full loop, we additionally exercised a teammate’s **Bicubic IP** in a controlled path. See **[Bicubic IP (GitHub)][[bicubic_ip](https://github.com/youngyang00/axi4s-bicubic-upscaler)]**.

### V2 — Ethernet Loopback via DDR — 🚧 In Progress
- **Flow**: TCP RX → DDR → TCP TX → PC  
- **Goal**: Validate **both RX/TX paths** with DDR buffering.

### V3 — Long Video Streaming (7,220 frames) — 🚧 In Progress
- **Flow**: TCP RX → DDR → (optional DMA→AXIS IP→DDR) → TCP TX → PC  
- **Goal**: Stress-test **continuous high-frame-count streaming** and run **pixel-wise** checks with the IP in the loop.

---

## 5) Data Format
- **Input**: BGR24 (`W×H×3`)  
- **Output**: ABGR32 (`W×H×4`)  
- **Chunk size**: 1460 bytes (MTU-friendly)  
- **HEX dump baseline**: `AABBGGRR` per pixel  
- **Buffers**: 64-byte aligned with explicit flush/invalidate around DMA ops

---

## 6) Build & Run

### Hardware (Vivado)
- Block Design: PS (DDR) ↔ **AXI DMA (MM2S/S2MM)** ↔ **AXI4-Stream IP**  
- AXI4-Stream interconnect clock example: **300 MHz**  
- Export **XSA** → Vitis

### Software (Vitis)
- BSP: **Standalone + lwIP RAW + AXI DMA driver**  
- Import `src/` (and `include/` if present), build **Release**, program board (bit + ELF)

### Python Client
```
# V1: 2-frame header test
python scripts/ethernet.py

# V2: Loopback test
python scripts/

# V3: Long video streaming
python scripts/
# Defaults: IP=192.168.1.20, port=6001, chunk=1460, fps=60
