# Guide: Static Dependency & Bloat Pruning with Cargo-Machete & Cargo-Udeps

## Overview
In Rust systems programming, a frequent cause of slow compilation times, inflated executable binary sizes, and redundant symbol bloat is carrying **unused or duplicate third-party dependencies**. When working on large workspaces, developers often add crates like `regex`, `serde`, or `tokio` for temporary features and forget to remove them. **Cargo-Machete** (`cargo-machete`) and **Cargo-Udeps** (`cargo-udeps`) are static analysis tools designed to audit your project schema and Abstract Syntax Trees (ASTs) to identify and eliminate unused dependency bloat.

---

## 1. How to Download & Install (`download`)

Both tools can be installed directly via Cargo. `cargo-machete` is extremely fast and runs on stable Rust, whereas `cargo-udeps` requires the nightly toolchain for deep compiler HIR analysis.

### Install Cargo-Machete (Recommended - Fast & Stable):
```bash
cargo install cargo-machete
```

### Install Cargo-Udeps (Deep Compiler Analysis - Nightly Required):
```bash
cargo install cargo-udeps --locked
```

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

You can configure ignore lists and workspace filters to prevent false positives when analyzing procedural macros or conditionally compiled crates.

### Cargo-Machete Configuration (`machete.toml` or `Cargo.toml`):
If your project uses special build scripts or implicit linking that static AST scanning might miss, add an ignore list to `Cargo.toml`:
```toml
[package.metadata.cargo-machete]
ignored = ["prost-build", "sqlx-cli"]
```

### Cargo-Udeps Configuration:
Because `cargo-udeps` hooks into the compiler's dependency tracking, invoke it using the nightly toolchain:
```bash
rustup toolchain install nightly
```

---

## 3. How to Run & Analyze (`profile` / `analyze`)

### Option A: Lightning-Fast AST Scan with Cargo-Machete
Run `cargo-machete` from your workspace root. It scans your Rust source files in milliseconds:
```bash
cargo machete
```

**Sample Output Report:**
```text
Analyzing workspace...
found unused dependencies in my_engine:
  - regex
  - rand
  - reqwest
Done! 3 unused dependencies found in 1 package.
```
* **The Diagnosis:** Your package `my_engine` is linking three massive crates (`reqwest` pulls in entire networking and TLS stacks!) that are never actually referenced in any `.rs` file.

### Option B: Deep Compiler Verification with Cargo-Udeps
For exhaustive analysis across all feature flag combinations and target architectures, run `cargo-udeps`:
```bash
cargo +nightly udeps --all-targets --all-features
```

### The Suggested Alternative: Dependency Pruning & Feature Stripping
1. **Remove Unused Crates:** Immediately delete the flagged dependencies from your `Cargo.toml`. This can reduce release link times by several seconds and shrink the executable binary footprint significantly.
2. **Strip Default Features:** If a dependency is used, but only for a tiny subset of its functionality, disable its default features to prevent compiling bloat:

```toml
# AVOID: Compiles dozens of unused networking, HTTP2, and JSON modules
reqwest = "0.11"

# ALTERNATIVE: Compiles ONLY the lightweight blocking client with rustls
reqwest = { version = "0.11", default-features = false, features = ["blocking", "rustls-tls"] }
```

---

## 4. Interpreting Results & Best Practices

1. **Integrate into CI Pipelines:** Add `cargo machete` as a mandatory step in your Continuous Integration linting job. Because it runs in under 500 milliseconds, it prevents dependency rot without slowing down PR reviews.
2. **Combine with `cargo-deny`:** Use `cargo machete` to remove unused crates, and pair it with `cargo deny check duplicate` to ensure your dependency graph isn't accidentally compiling two different major versions of the same crate (e.g., `syn 1.0` and `syn 2.0`), which doubles compilation time and instruction cache footprint.
3. **Audit Macro Dependencies:** Be cautious when removing crates used exclusively inside procedural macro attributes or `build.rs` scripts; always run `cargo test --all-targets` after pruning to verify that implicit build-time requirements remain satisfied.
