# Guide: Heap Memory Profiling & Leak Detection with DHAT

## Overview
**DHAT** (Dynamic Heap Analysis Tool) is an industry-standard heap profiler for Rust. Built as a native Rust implementation of Valgrind's DHAT algorithm, it intercepts every heap allocation (`Box`, `Vec`, `String`, `HashMap`, etc.) to track allocation counts, peak memory consumption, short-lived heap churn, and memory leaks at program termination.

---

## 1. How to Download & Install (`download`)

Unlike external command-line tools, `dhat` is integrated directly into your Rust application as a library crate and custom global allocator.

Add `dhat` to your project's `Cargo.toml`:

```toml
[dependencies]
dhat = "0.3"
```

---

## 2. How to Configure for Debugging (`debug`)

To allow DHAT to record exact file names and line numbers for every allocation and memory leak, ensure debug symbols are enabled in `Cargo.toml`:

```toml
[profile.release]
debug = true        # Required for line-by-line allocation stack traces!
strip = false
```

### Setting up the Global Allocator in Code
In your `src/main.rs` (or test harness), register DHAT as the program's global allocator and initialize the profiler:

```rust
use dhat::{Dhat, Profiler};

// 1. Register DHAT as the global heap allocator
#[global_allocator]
static ALLOC: Dhat = Dhat;

fn main() {
    // 2. Start the heap profiler as the very first line in main()
    let _profiler = Profiler::new_heap();

    println!("Starting application execution...");
    
    // Simulate some heap work and an intentional memory leak!
    let mut numbers = Vec::with_capacity(10_000);
    numbers.extend(0..10_000);
    
    // Leaking memory intentionally to demonstrate leak detection:
    let _leaked_box = Box::leak(Box::new(vec!["leak", "memory", "forever"]));

    println!("Application finishing...");
    // 3. When `_profiler` is dropped at the end of main(), DHAT outputs
    //    its summary to stderr and writes `dhat-heap.json` to disk!
}
```

---

## 3. How to Run & Profile (`profile`)

Compile and run your application in release mode:

```bash
cargo run --release
```

### Terminal Output Summary
When execution finishes, DHAT prints a high-level summary to `stderr`:

```text
dhat: Total:     80,072 bytes in 2 blocks
dhat: At t-gmax: 80,000 bytes in 1 blocks
dhat: At t-end:  72 bytes in 1 blocks (LEAKED!)
dhat: The data has been saved to dhat-heap.json, and is viewable with dhat/dh-view.html
```

* **`Total`**: The cumulative sum of all heap allocations across the entire program lifespan.
* **`At t-gmax`**: The exact moment of **Peak Heap Memory Usage** (global maximum).
* **`At t-end`**: Memory that was **never deallocated** when the program ended (**Memory Leaks!**).

---

## 4. Interpreting Results & Best Practices

To view the detailed interactive report, open the generated `dhat-heap.json` file using the official online DHAT viewer:

1. Open **[https://nnetherote.github.io/dh_view/dh_view.html](https://nnetherote.github.io/dh_view/dh_view.html)** in your web browser.
2. Click **"Load…"** and select your local `dhat-heap.json` file.

### Understanding the DHAT Viewer:
* **Sort by `Total` (Heap Churn):** Shows functions creating millions of short-lived temporary objects (e.g., allocating intermediate `String`s inside a loop instead of reusing a buffer).
* **Sort by `t-gmax` (Peak Memory):** Shows which data structures were sitting in RAM when your application hit its highest memory consumption. Great for sizing container capacities!
* **Sort by `t-end` (Memory Leaks):** Shows exact stack traces of memory that was leaked via `Box::leak`, `std::mem::forget`, or reference-counted cycles (`Rc`/`Arc`).

### Best Practices:
* Remove or conditionally compile `#[global_allocator] static ALLOC: Dhat = Dhat;` in production builds, as DHAT adds runtime tracking overhead to every malloc/free call.
* Use `#[cfg(feature = "dhat-heap")]` to toggle profiling cleanly via `cargo run --release --features dhat-heap`.
