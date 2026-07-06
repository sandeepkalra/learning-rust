# Guide: Static Formal Specification & Verification with Prusti

## Overview
**Prusti** is an open-source formal verification engine for Rust developed by the Laboratory for Automated Reasoning and Analysis at ETH Zurich. Built on top of the Viper verification infrastructure, Prusti allows systems programmers to write mathematical functional specifications—such as pre-conditions, post-conditions, and loop invariants—directly in their code comments or attribute macros. When optimizing mission-critical bottlenecks in aerospace, automotive, or financial systems, Prusti statically proves at compile time that your code never panics, never overflows integers, and never violates business logic invariants, allowing you to safely strip defensive runtime checks.

---

## 1. How to Download & Install (`download`)

Prusti is distributed as a custom Java/Rust verification bundle and IDE plugin. It requires a Java 11+ runtime environment to execute the underlying Viper verification backend.

### Step 1: Install Java Runtime Environment (JRE)
Ensure Java 11 or newer is installed on your system:
```bash
java -version
```

### Step 2: Install Prusti via VS Code Marketplace
The recommended way to use Prusti is via the official **"Prusti Assistant"** extension in the Visual Studio Code Marketplace. Installing the extension automatically downloads the correct Prusti server binaries and Viper verification tools for your operating system.

### Step 3: Command-Line Installation (Optional)
You can also download pre-built release binaries from the official GitHub repository (`viperproject/prusti-dev`) and add `prusti-rustc` to your system `PATH`.

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

To write mathematical specifications in your Rust source files, add the `prusti-contracts` attribute crate to your project dependencies.

### Step 1: Add Contracts Dependency
In your `Cargo.toml`:
```toml
[dependencies]
prusti-contracts = "0.3"
```

### Step 2: Configure Verification Timeout
Because formal verification theorem proving is computationally intensive, configure timeout limits and memory allocation in your IDE settings or environment variables:
```bash
export PRUSTI_LOG=info
export PRUSTI_SERVER_TIMEOUT=120
```

---

## 3. How to Run & Analyze (`profile` / `analyze`)

When using the VS Code extension, Prusti runs automatically on save, displaying verification proofs or mathematical counter-examples directly as editor diagnostics. To run via command line, execute:
```bash
cargo prusti
```

### Using Prusti to Prove Invariants and Strip Runtime Overhead:
In high-performance algorithmic trading or cryptographic loops, even safe integer addition `a + b` can introduce runtime checks or panic risks in debug/checked modes. Prusti allows you to mathematically prove that overflow is impossible, guaranteeing zero-overhead execution:

```rust
use prusti_contracts::*;

// AVOID: Standard loops without specifications require defensive checks or risk panic
pub fn calculate_sum_slow(a: u32, b: u32) -> u32 {
    if u32::MAX - a < b {
        return 0; // Defensive runtime check wastes CPU cycles
    }
    a + b
}

// ALTERNATIVE: Prusti mathematically proves pre-conditions and post-conditions!
// We define a contract: IF pre-condition holds, function is GUARANTEED to never panic or overflow!
#[requires(a <= 1000 && b <= 1000)]
#[ensures(result == a + b)]
#[ensures(result <= 2000)]
pub fn calculate_sum_fast(a: u32, b: u32) -> u32 {
    // Prusti proves at compile time that (1000 + 1000 <= u32::MAX).
    // Zero runtime overflow checks are required; LLVM emits a single raw CPU ADD instruction!
    a + b
}
```

### Proving Array Index Invariants:
```rust
use prusti_contracts::*;

#[requires(index < slice.len())]
#[ensures(*result == slice[index])]
pub fn get_element_fast<'a>(slice: &'a [i32], index: usize) -> &'a i32 {
    // Prusti statically proves index is within bounds; zero runtime check needed!
    &slice[index]
}
```

---

## 4. Interpreting Results & Best Practices

1. **Start with Core Financial / Safety Loops:** Do not attempt to formally verify your entire web server or GUI application. Use Prusti exclusively on critical algorithmic bottlenecks (such as order matching engines, cryptography, or memory allocators) where removing runtime checks yields massive performance gains.
2. **Understand Counter-Examples:** If Prusti fails to prove a post-condition, it outputs a concrete mathematical counter-example (e.g., *"Verification failed when `a = 4294967295` and `b = 1`"*). Use this feedback to tighten your `#[requires(...)]` input contracts.
3. **Combine with Clippy and Mirai:** Use `cargo-clippy` for quick structural refactoring, `MIRAI` for MIR-level abstract interpretation across large modules, and `Prusti` for exhaustive mathematical proof of your 50 most critical lines of code.
