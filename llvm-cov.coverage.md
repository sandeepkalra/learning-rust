# Guide: Source-Based Code Coverage with cargo-llvm-cov

## Overview
`cargo-llvm-cov` is the modern industry standard for tracking code coverage in Rust. It leverages LLVM's native source-based coverage instrumentation (built directly into the `rustc` compiler via `-C instrument-coverage`). It produces 100% exact line, branch, and region coverage without needing external debugging utilities or `ptrace`.

---

## 1. How to Download & Install (`download`)

### Step 1: Install the Cargo Subcommand
Install `cargo-llvm-cov` via Cargo:

```bash
cargo install cargo-llvm-cov
```

### Step 2: Install the LLVM Tools Preview Component
Because `llvm-cov` relies on LLVM binaries shipped with the Rust toolchain (`llvm-cov` and `llvm-profdata`), install the Rustup component:

```bash
rustup component add llvm-tools-preview
```

---

## 2. How to Configure for Debugging (`debug`)

`cargo-llvm-cov` works seamlessly with standard `cargo test` suites without requiring edits to `Cargo.toml`. 

However, if you want to test code coverage across multi-threaded tests or integration tests that spawn subprocesses, set the following environment variable in your terminal or CI pipeline:

```bash
# Ensure subprocesses inherit coverage instrumentation tracking:
export CARGO_LLVM_COV_SETUP=1
```

### Enabling Branch Coverage (Nightly Rust Only)
By default, stable Rust tracks **Line Coverage** and **Region Coverage**. To track **Branch Coverage** (checking whether both `if` and `else` paths were evaluated), run with Rust Nightly:

```bash
rustup toolchain install nightly
```

---

## 3. How to Run & Profile Coverage (`profile`)

### Generate a Quick Terminal Summary
To run your entire test suite and print a clean percentage table to the console:

```bash
cargo llvm-cov
```

**Sample Output:**
```text
Filename                      Regions    Missed Regions     Cover   Lines  Missed Lines     Cover
-------------------------------------------------------------------------------------------------
src/lib.rs                         45                 3    93.33%     120             4    96.67%
src/parser.rs                     112                18    83.93%     310            22    92.90%
-------------------------------------------------------------------------------------------------
TOTAL                             157                21    86.62%     430            26    93.95%
```

### Generate and Open an Interactive HTML Report ⭐
To generate a detailed line-by-line HTML report and automatically open it in your browser:

```bash
cargo llvm-cov --open
```

### Generate LCOV / Cobertura Reports for CI/CD
For integration with GitHub Actions, Codecov, or SonarQube:

```bash
# Generate lcov.info:
cargo llvm-cov --lcov --output-path lcov.info

# Generate Cobertura XML:
cargo llvm-cov --cobertura --output-path cobertura.xml
```

---

## 4. Interpreting Results & Best Practices

When viewing the interactive HTML report (`target/llvm-cov/html/index.html`):

1. **Bright Green Lines:** Code paths that were executed at least once during `cargo test`. The number in the left margin shows the exact execution count (e.g., `42x`).
2. **Bright Red Lines:** Code paths that were **never executed** by any test case!
3. **Yellow / Partial Regions:** Lines containing multiple branches (e.g., `if a && b`) where only one condition was tested.

### Best Practices for Systems Programmers:
* **Target Error Handling:** In systems programming, unhandled error paths (`Err(...)` or `match` fallback arms) are the #1 source of production bugs. Use `llvm-cov` to ensure every custom error enum variant is explicitly triggered by a test!
* **Ignore Boilerplate:** Use the `#[cfg(not(tarpaulin_include))]` or `#[no_coverage]` (nightly) attributes to exclude derived traits or CLI formatting boilerplate from skewing your coverage statistics.
* **CI Quality Gating:** Enforce a minimum coverage threshold in CI:
  ```bash
  cargo llvm-cov --fail-under-lines 85
  ```
