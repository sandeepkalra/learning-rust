# Guide: Static Memory Safety & Unsafe Analysis with Rudra

## Overview
**Rudra** is an advanced static analysis tool developed by researchers at Georgia Tech and UC Irvine, specifically designed to detect memory safety vulnerabilities and Undefined Behavior (UB) in Rust `unsafe` code. When systems programmers optimize critical bottlenecks by replacing standard library defaults with custom lock-free data structures, raw pointer manipulation, or intrusive linked lists, they bypass compiler safety guarantees. Rudra deeply analyzes the Mid-level Intermediate Representation (MIR) to identify panic-safety hazards, Send/Sync variance bugs, and higher-order invariant violations. It has famously discovered over 80 memory safety CVEs across major production crates, including `tokio`, `futures`, and `smallvec`.

---

## 1. How to Download & Install (`download`)

Rudra operates as a custom rustc compiler driver and requires a specific nightly toolchain to analyze the compiler's internal data structures.

### Step 1: Install via Git & Cargo
Clone the official repository and install the Rudra driver:
```bash
git clone https://github.com/sslab-gatech/rudra.git
cd rudra
rustup toolchain install nightly-2021-10-21
cargo +nightly-2021-10-21 install --path .
```

### Step 2: Verify Installation
Verify that the `cargo-rudra` custom subcommand is executable:
```bash
cargo rudra --version
```

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

Rudra is configured via environment variables to select specific analysis algorithms and define report output formats.

### Core Analysis Algorithms:
* **`UnsafeDataflow`**: Tracks data flow across raw pointer dereferences to find uninitialized reads and dangling pointers.
* **`SendSyncVariance`**: Verifies that custom `Send` and `Sync` trait implementations do not introduce thread data races across generic boundaries.
* **`PanicSafety`**: Ensures that if a function panics inside an `unsafe` block, memory is left in a consistent, non-dangling state.

### Configuration Example:
```bash
export RUDRA_ANALYZER="UnsafeDataflow,SendSyncVariance,PanicSafety"
export RUDRA_REPORT_PATH="./rudra_report.json"
```

---

## 3. How to Run & Analyze (`profile` / `analyze`)

To statically scan your project and all of its local modules for `unsafe` concurrency and memory bugs, run:
```bash
cargo rudra
```

### Understanding Rudra Bottleneck Refactoring Scenarios:
When optimizing memory bottlenecks, developers often implement custom `Send` or `Sync` traits on wrapper types to pass data across worker threads without atomic reference counting (`Arc`). Rudra statically catches when this optimization introduces data races:

```rust
// THE BOTTLENECK OPTIMIZATION: A custom container designed to avoid Arc overhead
pub struct FastContainer<T> {
    ptr: *mut T,
}

// AVOID: Implementing Sync without verifying inner type thread safety!
// Rudra flags this as a critical SendSyncVariance CVE hazard!
unsafe impl<T> Sync for FastContainer<T> {}

// ALTERNATIVE: Correctly constraining generic variance for thread safety
// Rudra verifies that Sync is only granted when the underlying type T is truly Sync!
unsafe impl<T: Sync> Sync for FastContainer<T> {}
```

### Catching Panic-Safety Hazards in High-Performance Buffers:
When writing zero-copy parsing buffers, developers often modify pointers before initialization is complete. Rudra flags locations where a panic in user code could lead to double-free anomalies:

```rust
// AVOID: If item.clone() panics, vector length is updated leaving uninitialized memory!
pub unsafe fn push_unchecked<T: Clone>(vec: &mut Vec<T>, item: &T) {
    let len = vec.len();
    vec.set_len(len + 1); // Rudra warns: Length updated BEFORE initialization!
    std::ptr::write(vec.as_mut_ptr().add(len), item.clone());
}

// ALTERNATIVE: Write memory first, then update invariants safely
pub unsafe fn push_unchecked_safe<T: Clone>(vec: &mut Vec<T>, item: &T) {
    let len = vec.len();
    std::ptr::write(vec.as_mut_ptr().add(len), item.clone());
    vec.set_len(len + 1); // Safe: Invariant updated only after successful write
}
```

---

## 4. Interpreting Results & Best Practices

1. **Audit Every `unsafe impl Send/Sync`:** If Rudra flags a `SendSyncVariance` warning, treat it as a P0 blocker. Improper `Sync` implementations on lock-free data structures cause undefined behavior and silent memory corruption in multi-threaded production environments.
2. **Enforce Panic Safety in Zero-Copy Code:** When writing high-frequency network parsers or serialization buffers, ensure that raw pointer writes happen *before* modifying length or capacity metadata.
3. **Combine with Miri:** Use Rudra as your first line of defense in static analysis to catch structural safety bugs across entire crates, and then run `cargo mirai` and `cargo miri test` on your hot paths to dynamically verify execution correctness.
