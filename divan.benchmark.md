# Guide: Fast & Lightweight Micro-Benchmarking with Divan

## Overview
**Divan** is a modern, ultra-fast micro-benchmarking framework for Rust. Designed as a simpler and significantly faster alternative to Criterion.rs, Divan leverages Rust attribute macros (`#[divan::bench]`), requires zero external HTML dependencies, natively counts heap allocations per benchmark, and supports effortless generic type benchmarking across multiple input sizes.

---

## 1. How to Download & Install (`download`)

Add `divan` as a development dependency in your `Cargo.toml`, and declare your benchmark target with `harness = false`:

```toml
[dev-dependencies]
divan = "0.1"

[[bench]]
name = "my_benchmark"
harness = false
```

Create your benchmark file under `benches/my_benchmark.rs`.

---

## 2. How to Configure for Debugging (`debug`)

Divan makes writing benchmark harnesses incredibly concise using procedural attribute macros. Like Criterion, always wrap inputs/outputs in `divan::black_box` to prevent compiler dead-code elimination.

### Runnable Benchmark Template (`benches/my_benchmark.rs`):

```rust
use divan::{black_box, Bencher};

fn main() {
    // Run all registered Divan benchmarks
    divan::main();
}

// 1. Simple benchmark using attribute macro
#[divan::bench]
fn bench_sorting() {
    let mut data = vec![5, 2, 8, 1, 9, 3];
    data.sort();
    black_box(data);
}

// 2. Benchmarking across multiple generic types!
#[divan::bench(types = [i32, i64, f64])]
fn bench_math<T: Copy + std::ops::Add<Output = T> + Default>() {
    let a = black_box(T::default());
    let b = black_box(T::default());
    black_box(a + b);
}

// 3. Benchmarking across multiple input sample sizes!
#[divan::bench(args = [10, 1_000, 100_000])]
fn bench_vec_allocation(len: usize) {
    let vec: Vec<u64> = Vec::with_capacity(black_box(len));
    black_box(vec);
}
```

---

## 3. How to Run & Profile Benchmarks (`profile`)

### Run All Benchmarks
To execute your benchmarks and view the terminal histogram:
```bash
cargo bench
```

### Enable Heap Allocation Tracking ⭐
One of Divan's greatest superpowers is its ability to track exact heap allocation counts and bytes allocated per iteration without needing external tools like DHAT!

```bash
cargo bench -- --alloc
```

### Filter Benchmarks by Name
```bash
cargo bench -- bench_vec_allocation
```

---

## 4. Interpreting Results & Best Practices

Divan outputs clean, colorful histograms and comparative tables directly to your terminal without cluttering your disk with HTML files.

### Terminal Output Breakdown (with `--alloc`):
```text
Timer precision: 41 ns
my_benchmark            fastest       │ slowest       │ median        │ mean          │ samples │ iter │ alloc / iter
├─ bench_vec_allocation               │               │               │               │         │      │
│  ├─ 10                14.21 ns      │ 45.12 ns      │ 15.01 ns      │ 16.32 ns      │ 10000   │ 800  │ 1 B, 1 count
│  ├─ 1000              112.4 ns      │ 310.2 ns      │ 118.5 ns      │ 122.1 ns      │ 10000   │ 800  │ 8 KB, 1 count
│  ╰─ 100000            8.412 µs      │ 24.15 µs      │ 8.910 µs      │ 9.102 µs      │ 10000   │ 800  │ 800 KB, 1 count
```

* **`median` / `mean`**: Shows the measures of central tendency for execution latency.
* **`alloc / iter`**: Shows the exact number of heap allocations (`1 count`) and total bytes (`800 KB`) allocated during a single execution of your function!

### Best Practices:
* **Use Divan for Allocation Auditing:** When writing zero-allocation parsers or high-frequency networking code, run `cargo bench -- --alloc` in CI to ensure your functions maintain `0 B, 0 count` allocations!
* **Use Criterion when Statistical Regression Graphs are Needed:** If your team requires HTML regression charts and p-value proof across GitHub Pull Requests, use Criterion. If you want developer speed, simplicity, and allocation counting, use Divan!
