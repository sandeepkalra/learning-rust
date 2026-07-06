# Guide: CPU Profiling with cargo-flamegraph & perf

## Overview
`cargo-flamegraph` is a Rust-native wrapper around Linux's `perf` subsystem (and DTrace on macOS). It collects high-frequency CPU stack trace samples and generates interactive SVG FlameGraphs to visualize hot code paths and execution bottlenecks.

---

## 1. How to Download & Install (`download`)

### Prerequisites (Linux)
You must install the Linux kernel performance counters tool (`perf`):
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y linux-tools-common linux-tools-generic linux-tools-$(uname -r)

# Fedora / RHEL
sudo dnf install -y perf

# Arch Linux
sudo pacman -S perf
```

### Allow Non-Root Profiling (Linux)
By default, Linux restricts `perf` to root users. To allow non-root users to record CPU events:
```bash
# Temporary (until reboot):
sudo sysctl -w kernel.perf_event_paranoid=-1

# Permanent:
echo "kernel.perf_event_paranoid = -1" | sudo tee -a /etc/sysctl.conf
```

### Install `cargo-flamegraph`
Install the Rust CLI wrapper directly via Cargo:
```bash
cargo install cargo-flamegraph
```

---

## 2. How to Configure for Debugging (`debug`)

To generate readable FlameGraphs, the profiler **must** have access to debug symbols (function names and line numbers). If you compile in standard `--release` mode without symbols, your FlameGraph will just show `[unknown]` or hex memory addresses!

Add the following configuration to your project's `Cargo.toml`:

```toml
[profile.release]
debug = true        # Keep debug symbols in release builds (essential!)
strip = false       # Do not strip symbols
lto = "thin"        # Optional: Link-time optimization for realistic performance
```

---

## 3. How to Run & Profile (`profile`)

### Profiling a Binary Application
To compile your app in release mode and immediately generate a FlameGraph:
```bash
cargo flamegraph --bin my_app -- --my-arg-1 --my-arg-2
```
* Note: Everything after `--` is passed directly as arguments to your application.

### Profiling Unit Tests or Integration Tests
You can also profile specific test cases to find bottlenecks in algorithms:
```bash
cargo flamegraph --unit-test --test test_name -- --nocapture
```

### Profiling a Running Process (PID)
If your Rust server or daemon is already running in the background:
```bash
sudo flamegraph --pid <PID> --output server-flamegraph.svg
```

---

## 4. Interpreting Results & Best Practices

When execution finishes, `cargo-flamegraph` creates an interactive SVG file named `flamegraph.svg` in your current directory. Open it in any web browser (Chrome, Firefox, Safari):

```bash
xdg-open flamegraph.svg # Linux
open flamegraph.svg     # macOS
```

### How to Read the FlameGraph:
1. **Y-Axis (Stack Depth):** Represents the call stack hierarchy. The bottom box is `main()`, and boxes stacked on top are the functions called by their parents.
2. **X-Axis (Population / CPU Samples):** **This is NOT time!** The width of a box represents the **total percentage of CPU samples** that the function occupied during the entire run.
3. **Plateaus (Wide Horizontal Boxes):** A wide box at the very top of a stack represents a **CPU Hotspot**—a function actively consuming massive amounts of processor time!
4. **Interactive Zoom:** Click on any box in the browser to zoom in on that specific call tree. Click "Reset Zoom" in the top left to zoom out.

### Optimization Workflow:
* Identify the widest top-level boxes.
* Check if time is spent in memory allocation (`malloc` / `free`), hashing (`SipHash` vs `FxHash` / `AHash`), or cloning (`<T as Clone>::clone`).
* Optimize the hot algorithm, re-run `cargo flamegraph`, and verify that the plateau shrinks!
