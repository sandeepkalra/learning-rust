# Guide: Diagnosing Generic & Instruction Cache Bloat with Cargo-LLVM-Lines

## Overview
**Cargo-LLVM-Lines** (`cargo-llvm-lines`) is a specialized static analysis tool designed to measure the size of generic function instantiations in Rust. In systems programming, a common hidden bottleneck is **Monomorphization Bloat**. When a generic function is instantiated across dozens of different types, the Rust compiler generates separate machine code for each type. This can result in massive executable binaries and severe CPU Instruction Cache (i-cache) thrashing. `cargo-llvm-lines` statically counts the exact number of lines of LLVM Intermediate Representation (IR) generated per function, showing you exactly where generic bloat is destroying performance.

---

## 1. How to Download & Install (`download`)

Install `cargo-llvm-lines` directly via Cargo from crates.io:
```bash
cargo install cargo-llvm-lines
```

Verify that the subcommand is available:
```bash
cargo llvm-lines --version
```

---

## 2. How to Configure for Static Analysis (`debug` / `configure`)

To get an accurate measurement of your production binary bloat, always run `cargo-llvm-lines` in release mode. You can also filter by specific crates or packages in a workspace.

### Configuration Flags:
* **`--release`**: Analyzes LLVM IR generated with release optimizations (inlining, loop unrolling).
* **`--lib`**: Analyzes only the library target (ignoring test harnesses or binary wrappers).
* **`--filter <keyword>`**: Filters the output report to show only functions matching a specific module or struct name.

---

## 3. How to Run & Analyze (`profile` / `analyze`)

To generate a complete static report of LLVM IR bloat across your project, execute:
```bash
cargo llvm-lines --release
```

### Understanding the Output Report:
The output is sorted by the total number of LLVM IR lines generated across all copies of a function:
```text
  Lines           Copies        Function name
  -----           ------        -------------
  54321 (18.2%)   42 (12.1%)    my_crate::parser::parse_stream
  12345 ( 4.1%)    1 ( 0.3%)    my_crate::engine::execute_loop
   8765 ( 2.9%)   15 ( 4.3%)    std::collections::hash_map::HashMap<K, V>::insert
```
* **`Lines`**: Total lines of LLVM IR generated for this function across all type instantiations.
* **`Copies`**: How many times this generic function was duplicated (monomorphized) for different concrete types!
* **`42 Copies` of `parse_stream`**: This signals a severe bottleneck! A single function is responsible for 18.2% of your entire compiled codebase because it was duplicated 42 times.

### The Suggested Alternative: The "Inner Function Pattern"
When `cargo-llvm-lines` reveals an oversized generic function, the industry-standard refactoring technique is the **Inner Function Pattern**. You split the generic wrapper from the non-generic core logic:

```rust
// AVOID: 500 lines of logic duplicated for every type T (Thrashes CPU instruction cache!)
pub fn parse_data<T: Read>(mut stream: T) -> Result<Output, Error> {
    let mut buffer = [0u8; 1024];
    stream.read(&mut buffer)?;
    // ... 500 lines of complex data parsing logic ...
}

// ALTERNATIVE: Generic wrapper is tiny; 500 lines of core logic compiled ONLY ONCE!
pub fn parse_data<T: Read>(mut stream: T) -> Result<Output, Error> {
    parse_data_inner(&mut stream) // Generic wrapper is inlineable and trivial
}

fn parse_data_inner(stream: &mut dyn Read) -> Result<Output, Error> {
    let mut buffer = [0u8; 1024];
    stream.read(&mut buffer)?;
    // ... 500 lines of complex data parsing logic compiled exactly once ...
}
```

---

## 4. Interpreting Results & Best Practices

1. **Watch the Copies Column:** A high line count with `Copies = 1` simply means you have a large function. A high line count with `Copies > 10` indicates severe generic bloat that must be refactored using trait objects (`&dyn Trait`) or inner helper functions.
2. **Protect CPU L1/L2 Instruction Caches:** Modern CPU cores have small L1 instruction caches (typically 32 KB or 64 KB). If your hot loop calls generic functions that bloat beyond 64 KB of machine instructions, the CPU will continuously stall while fetching instructions from the slower L2/L3 cache or main RAM.
3. **Audit Third-Party Dependencies:** `cargo-llvm-lines` often reveals that heavy generic serialization libraries (like `serde` or `bincode`) generate tens of thousands of lines of LLVM IR. When optimizing build times and binary size, use this data to justify switching to lighter parsing alternatives or manual serialization for hot paths.
