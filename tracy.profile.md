# Guide: Real-Time Frame & Execution Timeline Profiling with Tracy

## Overview
**Tracy Profiler** is a real-time, nanosecond-resolution frame and execution timeline profiler. Widely used in systems programming, game engines (such as Bevy), robotics, and real-time audio/video processing, Tracy streams live performance telemetry from your running Rust application directly to the graphical Tracy desktop client, visualizing thread contention, lock delays, frame rate spikes, and memory allocations over time.

---

## 1. How to Download & Install (`download`)

Tracy consists of two parts: the **Desktop Client GUI** (the viewer) and the **Rust Library Crates** (the instrumentation).

### Step 1: Download the Tracy Desktop Client GUI
Download the pre-compiled Tracy Profiler graphical client for your OS (Windows, macOS, or Linux) from the official GitHub releases:
* **[https://github.com/wolfpld/tracy/releases](https://github.com/wolfpld/tracy/releases)**

### Step 2: Add Rust Dependencies
Hook Tracy directly into Rust's standard `tracing` ecosystem by adding `tracing` and `tracing-tracy` to your `Cargo.toml`:

```toml
[dependencies]
tracing = "0.1"
tracing-subscriber = "0.3"
tracing-tracy = "0.11"
```

---

## 2. How to Configure for Debugging (`debug`)

In your application's entry point (`src/main.rs`), initialize the `tracing-subscriber` with the `TracyLayer`. Then, annotate any function or async task you want to track on the timeline with `#[tracing::instrument]`.

### Runnable Instrumentation Template (`src/main.rs`):

```rust
use std::time::Duration;
use tracing::{info, instrument};
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;

// 1. Annotate functions to automatically emit begin/end timeline spans!
#[instrument]
fn perform_heavy_database_query(query_id: u32) {
    info!("Executing query {}", query_id);
    std::thread::sleep(Duration::from_millis(15)); // Simulate CPU/IO work
}

#[instrument]
fn render_game_frame(frame_num: u64) {
    perform_heavy_database_query(1);
    perform_heavy_database_query(2);
    std::thread::sleep(Duration::from_millis(5));
}

fn main() {
    // 2. Initialize the Tracy layer to stream telemetry on port 8042
    tracing_subscriber::registry()
        .with(tracing_tracy::TracyLayer::default())
        .init();

    println!("Connecting to Tracy Profiler... (Open Tracy GUI now!)");

    // 3. Main application loop (simulating 60 FPS frame updates)
    for frame in 1..=500 {
        render_game_frame(frame);
        
        // Mark the end of a graphical or logical frame in Tracy:
        tracing_tracy::client::frame_mark();
    }
}
```

---

## 3. How to Run & Profile (`profile`)

### Step 1: Launch the Tracy Desktop GUI
Open the downloaded `Tracy` application on your desktop. You will see a button labeled **"Connect (localhost)"**.

### Step 2: Run Your Rust Application
Launch your application in release mode:

```bash
cargo run --release
```

### Step 3: Connect Live in the GUI
As soon as your Rust app starts, click **"Connect"** in the Tracy GUI! You will see live, real-time telemetry streaming across your screen at 60+ FPS!

---

## 4. Interpreting Results & Best Practices

The Tracy GUI provides deep insight into real-time system behavior:

### Key Features in the Tracy GUI:
1. **Frame Time Graph (Top Bar):** Shows a bar chart of every frame's duration in milliseconds. Spikes above `16.6 ms` indicate dropped frames (falling below 60 FPS)! Click on any spike to inspect that exact frame!
2. **Timeline Tracks (Center):** Displays horizontal tracks for every OS thread and async worker. You will see nested colored boxes representing your `#[instrument]` function spans (`render_game_frame` -> `perform_heavy_database_query`).
3. **Lock Contention Tracking:** Tracy automatically highlights Mutex/RwLock waiting times in red, showing you exactly which thread was holding the lock and causing another thread to stall!
4. **Memory Profiling Tab:** If configured with Tracy's global allocator wrapper, this tab displays live graphs of heap memory fragmentation and total allocated blocks over time.

### Best Practices:
* **Feature Gating in Production:** Keep Tracy instrumentation zero-cost in production by wrapping the subscriber initialization behind a Cargo feature flag:
  ```toml
  [features]
  profiling = ["tracing-tracy"]
  ```
  Run with `cargo run --release --features profiling` only when live profiling is needed!
* **Async Tokio Tracking:** Tracy works seamlessly with async/await! When using Tokio, `#[tracing::instrument]` correctly tracks async futures across worker thread migrations!
