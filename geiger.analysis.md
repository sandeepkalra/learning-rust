# Guide: Static Unsafe Code Radiation Detection with Cargo-Geiger

## Overview
**Cargo-Geiger** (`cargo-geiger`) is a specialized static analysis tool that acts as a "radiation detector" for Rust projects. When optimizing performance bottlenecks, developers frequently replace standard library defaults with aggressive third-party crates (such as lock-free queues, small-vector optimizations, or custom hashers). While these crates offer significant speedups, they often achieve them by bypassing compiler safety boundaries via `unsafe` code. `cargo-geiger` statically scans your entire workspace and third-party dependency tree, generating a visual heat map of exactly where and how frequently `unsafe` blocks, traits, and functions are used.

---

## 1. How to Download & Install (`download`)

`cargo-geiger` is available as a standalone Cargo subcommand and installs cleanly on stable Rust toolchains.

### Step 1: Install via Cargo
```bash
cargo install cargo-geiger
```

### Step 2: Verify Installation
Verify that the tool is accessible:
```bash
cargo geiger --version
```

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

You can configure `cargo-geiger` to output structured JSON reports for Continuous Integration pipelines or filter out dev-dependencies to focus exclusively on production runtime risks.

### Command-Line Configuration Flags:
* **`--all-dependencies`**: Scans the entire transitive dependency tree (every crate pulled in by `Cargo.lock`).
* **`--output-format json`**: Outputs a machine-readable JSON report for automated security auditing.
* **`--invert-tree`**: Displays the dependency tree inverted, showing which top-level crates pull in the most `unsafe` code at the bottom.

---

## 3. How to Run & Analyze (`profile` / `analyze`)

To generate an interactive ASCII radiation report across your workspace and dependencies, execute:
```bash
cargo geiger
```

### Understanding the Radiation Heat Map:
The output uses color-coded symbols and counters to display the exact "radiation level" of each crate in your dependency tree:
```text
Metric output format: x/y
    x = unsafe code used
    y = total lines of code found

Symbols:
    ☢ = Unsafe code used inside crate
    ☮ = Totally safe crate (No unsafe blocks found!)

Functions  Expressions  Impls  Traits  Methods  Dependency
0/42       0/150        0/5    0/0     0/20     ☮ my_safe_engine 0.1.0
12/85      45/310       2/10   1/2     15/90    ☢ smallvec 1.11.0
0/10       0/50         0/0    0/0     0/5      ☮ once_cell 1.18.0
```
* **`☮ my_safe_engine`**: Zero `unsafe` expressions or traits found! The compiler guarantees total memory safety.
* **`☢ smallvec`**: Contains 45 `unsafe` expressions and 2 `unsafe` trait implementations. This is expected because `SmallVec` optimizes vector bottlenecks by managing raw stack memory directly.

### Using Geiger to Audit Bottleneck Alternatives:
When choosing between two third-party crates to solve a hashing or caching bottleneck, use `cargo-geiger` to compare their safety profiles:

```rust
// SCENARIO: You need a fast concurrent hashmap to replace Mutex<HashMap<K, V>>

// CRATE A: High performance, but cargo-geiger shows 150+ unsafe expressions
// Risk: High vulnerability to memory corruption under edge-case concurrency
use aggressive_lockfree_map::FastMap;

// CRATE B (Alternative): Highly optimized, but cargo-geiger shows 0 unsafe expressions (☮)
// Risk: Zero! Relies entirely on safe compiler abstractions and crossbeam channels
use safe_concurrent_map::SafeMap;
```

---

## 4. Interpreting Results & Best Practices

1. **Establish a Safety Budget:** In enterprise systems programming, establish a strict rule: any new dependency added to solve a CPU or memory bottleneck must be scanned with `cargo geiger`. Prefer crates marked with the peace symbol (`☮`) unless the performance gain of an `unsafe` crate (`☢`) is proven by benchmark data.
2. **Isolate Unsafe Radiation:** If you must write custom `unsafe` code to resolve a bottleneck (such as SIMD intrinsics or raw pointer arena allocation), encapsulate that logic into a tiny, isolated internal micro-crate. This keeps your main application logic 100% safe (`☮`) while confining auditing efforts to a single file.
3. **Automate Dependency Auditing:** Combine `cargo geiger` with `cargo deny` and `cargo vet` in your CI pipeline to prevent developers from accidentally introducing unverified, `unsafe`-heavy dependencies into your software supply chain.
