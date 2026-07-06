# Guide: Multi-Threaded CPU Profiling with Samply & Firefox Profiler

## Overview
`samply` is a state-of-the-art CPU sampling profiler for macOS and Linux. It records application execution and automatically streams the telemetry into the world-class **Firefox Profiler** web application (`profiler.firefox.com`). It is especially renowned for its unmatched visualization of multi-threaded Rust work pools (like Tokio or Rayon) and seamless Apple Silicon (macOS) support.

---

## 1. How to Download & Install (`download`)

`samply` is a standalone command-line tool installed via Cargo:

```bash
cargo install samply
```

* **macOS Note:** No system kernel modifications or root privileges are required on macOS!
* **Linux Note:** Ensure `kernel.perf_event_paranoid` is set to `-1` or `1` (see Linux perf setup in `flamegraph.profile.md`).

---

## 2. How to Configure for Debugging (`debug`)

Just like all sampling profilers, `samply` requires debug symbols to map memory addresses to Rust function names and filenames.

Add this to your project's `Cargo.toml`:

```toml
[profile.release]
debug = true        # Retain DWARF debug symbols
strip = false       # Do not strip binary symbols
```

### Optional: Enabling Frame Pointers (For Extra Call Stack Accuracy)
On some x86_64 architectures, enabling frame pointers ensures 100% perfect stack unwinding without reliance on DWARF tables:

```bash
# Set in your terminal environment before building:
export RUSTFLAGS="-C force-frame-pointers=yes"
```

---

## 3. How to Run & Profile (`profile`)

### Profiling a Cargo Project Directly
You can prefix any `cargo run` command with `samply record`:

```bash
samply record cargo run --release --bin my_app -- --arg1 --arg2
```

### Profiling a Pre-compiled Binary
If you have already built your release binary:

```bash
samply record ./target/release/my_app
```

### What Happens When Execution Ends?
1. `samply` compresses the recorded stack samples into a local profile file.
2. It spins up a temporary local web server (e.g., on `http://127.0.0.1:3000`).
3. It **automatically opens your default web browser** to `https://profiler.firefox.com` and loads the profile directly from your local machine!
   * *Privacy Note:* All data is processed 100% locally inside your browser; no profiling data is ever uploaded to Mozilla or external servers!

---

## 4. Interpreting Results & Best Practices

The Firefox Profiler UI is arguably the most powerful open-source visualization suite in systems programming.

### Key Features to Explore:
1. **Thread Timeline (Top Panel):** Shows every OS thread spawned by your Rust app (e.g., `tokio-runtime-worker-0`, `rayon-core-1`). You can see exactly when threads are executing CPU work, sleeping, or blocked on locks!
2. **Call Tree (Bottom Left):** A hierarchical breakdown of total execution time per function, sorted by **Self Time** (time spent directly in the function) versus **Total Time** (time spent in the function and its children).
3. **Flame Graph Tab:** An interactive FlameGraph similar to `cargo-flamegraph`, but with instant search, filtering by thread, and time-slice selection.
4. **Stack Chart / Timeline Zoom:** Highlight any time range in the top timeline (e.g., during a latency spike or initialization drop) to filter the Call Tree and Flame Graph exclusively to that exact millisecond window!

### Best Practices:
* Use `samply` when debugging async Tokio deadlocks or Rayon thread-pool starvation.
* Look for gaps in worker thread timelines—if 7 out of 8 threads are idle while 1 thread is at 100% CPU, your workload is poorly parallelized or suffering from lock contention!
