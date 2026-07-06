# Guide: Statistical Micro-Benchmarking with Criterion.rs

## Overview
**Criterion.rs** is the industry standard for statistics-driven micro-benchmarking in Rust. Inspired by Haskell's Criterion library, it runs benchmarks across thousands of iterations, performs rigorous statistical regression analysis (e.g., detecting a +1.2% latency increase with 95% confidence), and generates visual HTML charts using TinyHTML while isolating compiler optimization noise.

---

## 1. How to Download & Install (`download`)

Criterion is configured as a development dependency in your project's `Cargo.toml`.

### Step 1: Add Dependency & Disable Default Harness
Add `criterion` under `[dev-dependencies]`, and declare a `[[bench]]` target with `harness = false` (which tells Cargo to use Criterion's custom benchmark runner instead of the standard library's test harness):

```toml
[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }

[[bench]]
name = "my_benchmark"
harness = false
```

### Step 2: Create the Benchmark File
Create a new directory named `benches/` at the root of your project, and create `benches/my_benchmark.rs`.

---

## 2. How to Configure for Debugging (`debug`)

To write accurate micro-benchmarks, you must prevent LLVM from performing **Dead Code Elimination (DCE)**. If you compute a value inside a benchmark loop but never use it, LLVM's optimizer will delete your entire algorithm at compile time, resulting in fake `0.000 ns` benchmark times!

### The `black_box` Solution
Always wrap your benchmark inputs and outputs in `std::hint::black_box(...)` (or `criterion::black_box(...)`). This forces the compiler to assume the value is dynamically read and written to opaque memory.

### Runnable Benchmark Template (`benches/my_benchmark.rs`):
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

// The function we want to benchmark
fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 1,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn bench_fibonacci(c: &mut Criterion) {
    // 1. Define a benchmark group or single routine
    c.bench_function("fib 20", |b| {
        // 2. b.iter(...) runs the closure thousands of times to gather statistics
        b.iter(|| {
            // 3. Wrap both input and output in black_box!
            fibonacci(black_box(20))
        })
    });
}

// Register benchmark functions and generate main()
criterion_group!(benches, bench_fibonacci);
criterion_main!(benches);
```

---

## 3. How to Run & Profile Benchmarks (`profile`)

### Run All Benchmarks
To execute your benchmarks and perform statistical analysis against previous runs:
```bash
cargo bench
```

### Run a Specific Benchmark Filter
If you have multiple benchmark suites:
```bash
cargo bench -- "fib 20"
```

### Save a Baseline for Regression Testing
When making optimization experiments, save your current performance as a named baseline:
```bash
# Save current code performance as "before_pr":
cargo bench -- --save-baseline before_pr

# Make your code edits... then compare against the baseline:
cargo bench -- --baseline before_pr
```

---

## 4. Interpreting Results & Best Practices

When `cargo bench` finishes, it outputs statistical summaries to the terminal and generates an interactive HTML report suite under `target/criterion/report/index.html`.

### Terminal Output Breakdown:
```text
fib 20                  time:   [26.142 µs 26.205 µs 26.273 µs]
                        change: [-3.412% -2.105% -0.891%] (p = 0.00 < 0.05)
                        Performance has improved.
```
* **`time: [Low Median High]`**: The 95% confidence interval of execution time per iteration.
* **`change: [Low Median High]`**: The percentage difference compared to the last recorded baseline!
* **`p = 0.00 < 0.05`**: The statistical p-value confirming whether the change is a genuine performance shift or random system noise.

### Best Practices:
* **Close Background Apps:** Close web browsers, Docker containers, and Slack before running benchmarks to prevent CPU throttling and OS scheduling noise.
* **Benchmark Across Input Sizes:** Use `c.bench_with_input(...)` and `BenchmarkId` to test algorithms across vectors of size 10, 1,000, and 100,000 elements to observe asymptotic scaling (O(N) vs O(N log N)).
