# Guide: Abstract Interpretation & Invariant Verification with MIRAI

## Overview
**MIRAI** (Mid-level Intermediate Representation Abstract Interpreter) is an advanced static analysis tool developed by Meta (Facebook). It performs abstract interpretation over the Rust compiler's Mid-level Intermediate Representation (MIR). In high-frequency systems and core infrastructure, performance bottlenecks are frequently caused by excessive runtime assertions, defensive bounds checking, and integer overflow checks. MIRAI statically proves that mathematical invariants, array bounds, and panic conditions are never violated across inter-procedural call boundaries without executing the binary. This enables developers to safely replace defensive runtime checks with zero-overhead unchecked alternatives.

---

## 1. How to Download & Install (`download`)

MIRAI requires a specific nightly Rust toolchain because it links directly against the internal compiler libraries of `rustc`.

### Step 1: Install Dependencies & Toolchain
Check the MIRAI repository for the required nightly toolchain version, and install it via `rustup`:
```bash
rustup toolchain install nightly-2023-08-25
rustup component add rustc-dev llvm-tools-preview --toolchain nightly-2023-08-25
```

### Step 2: Install MIRAI via Cargo
Install the analyzer directly from crates.io or GitHub:
```bash
cargo +nightly-2023-08-25 install --locked mirai
```

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

To instruct MIRAI to verify your custom business logic and invariants, add the lightweight `mirai-annotations` crate to your project dependencies.

### Step 1: Add Annotations Dependency
In your `Cargo.toml`:
```toml
[dependencies]
mirai-annotations = "1.11"
```

### Step 2: Configure Verification Flags
Set environment variables to control verification depth and diagnostic verbosity:
```bash
export MIRAI_LOG=warn
export MIRAI_FLAGS="--diag=default --single_func=my_hot_function"
```

---

## 3. How to Run & Analyze (`profile` / `analyze`)

To run MIRAI across your project, use its custom Cargo wrapper:
```bash
cargo mirai
```

### How MIRAI Proves Invariants to Resolve Bottlenecks:
When optimizing hot inner loops (such as parsing network packets or matrix multiplication), standard vector indexing `buffer[index]` introduces runtime bounds checks on every iteration. While `get_unchecked` eliminates this overhead, using it without proof risks catastrophic memory corruption.

MIRAI allows you to statically prove that the index is always within bounds:

```rust
use mirai_annotations::{verify, assume};

// AVOID: Every array access introduces a runtime CPU branch for bounds checking!
pub fn process_matrix_slow(matrix: &[f64; 100], indices: &[usize]) -> f64 {
    let mut sum = 0.0;
    for &idx in indices {
        if idx < 100 { // Defensive runtime check slows down loop
            sum += matrix[idx];
        }
    }
    sum
}

// ALTERNATIVE: MIRAI statically proves bounds; zero runtime checks required!
pub fn process_matrix_fast(matrix: &[f64; 100], indices: &[usize]) -> f64 {
    let mut sum = 0.0;
    for &idx in indices {
        // We instruct MIRAI to statically prove that idx < 100 at compile time:
        verify!(idx < 100);
        
        // Because MIRAI mathematically proved the invariant, we safely eliminate runtime bounds checks:
        unsafe {
            sum += *matrix.get_unchecked(idx);
        }
    }
    sum
}
```

---

## 4. Interpreting Results & Best Practices

1. **Verify Unsafe Boundaries:** Whenever you optimize a bottleneck by replacing safe standard library calls with `unsafe` pointer arithmetic or unchecked indexing, add `mirai_annotations::verify!` pre-conditions. MIRAI will act as an automated mathematical theorem prover during CI.
2. **Handle False Positives:** Because abstract interpretation is conservative, MIRAI may report potential panics if a loop bound depends on complex external IO. Use `mirai_annotations::assume!` to document assumptions that are guaranteed by external hardware or OS protocols.
3. **Target Hot Functions Only:** Inter-procedural abstract interpretation is computationally intensive. When analyzing massive codebases, use `--single_func=<name>` to focus MIRAI's formal verification exclusively on your top 5 performance bottlenecks identified by CPU profilers.
