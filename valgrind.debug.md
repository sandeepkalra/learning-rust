# Guide: Deterministic CPU & Cache Miss Debugging with Valgrind Callgrind

## Overview
**Valgrind Callgrind** is a CPU emulation and profiling tool that records deterministic execution metrics. Instead of sampling wall-clock time (which fluctuates due to OS background tasks or CPU boost clock scaling), Callgrind simulates a CPU to count exact machine instructions executed (`Ir`), L1/L2/L3 cache misses, and conditional branch mispredictions. It is paired with **KCachegrind** (or QCachegrind) for visual call-graph analysis.

---

## 1. How to Download & Install (`download`)

### Linux Installation
Install Valgrind and the KCachegrind GUI via your package manager:
```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y valgrind kcachegrind

# Fedora / RHEL
sudo dnf install -y valgrind kcachegrind

# Arch Linux
sudo pacman -S valgrind kcachegrind
```

### macOS Installation
On Apple Silicon macOS, native Valgrind support is limited. We recommend running Callgrind inside a Docker Linux container:
```bash
docker run --rm -it -v $(pwd):/workspace -w /workspace rust:latest bash
# Inside container: apt update && apt install -y valgrind
```
* Note: For native macOS visualization, install `qcachegrind` via Homebrew: `brew install qcachegrind`.

---

## 2. How to Configure for Debugging (`debug`)

To map machine instructions and cache misses directly to your Rust source code lines, ensure DWARF debug symbols are enabled without stripping.

Add this configuration to `Cargo.toml`:

```toml
[profile.release]
debug = true        # Required to map instructions to Rust file line numbers!
strip = false
lto = "thin"
```

### Isolating Specific Function Boundaries
When analyzing small algorithms, LLVM function inlining can merge child functions into their parents, obscuring call graphs. To forbid inlining on a function being investigated, use the attribute:

```rust
#[inline(never)]
pub fn critical_parsing_routine(data: &[u8]) -> u32 {
    // Hot algorithm here...
}
```

---

## 3. How to Run & Profile (`profile`)

### Step 1: Compile Your Release Binary
```bash
cargo build --release
```

### Step 2: Execute Under Callgrind Emulation
Run your compiled binary under Valgrind with instruction dumping and jump/branch tracking enabled:

```bash
valgrind --tool=callgrind \
  --dump-instr=yes \
  --collect-jumps=yes \
  --simulate-cache=yes \
  ./target/release/my_app --arg1 --arg2
```

* **`--simulate-cache=yes`**: Simulates L1 and LL (Last Level / L3) CPU data and instruction caches to count exact cache misses!
* **`--collect-jumps=yes`**: Tracks conditional branch predictions and mispredictions.

### What Happens When Execution Ends?
Valgrind writes a deterministic profile file named `callgrind.out.<PID>` in your current working directory.

---

## 4. Interpreting Results & Best Practices

Open the generated profile file using **KCachegrind** (Linux) or **QCachegrind** (macOS/Windows):

```bash
kcachegrind callgrind.out.<PID>
```

### Key Metrics in KCachegrind:
1. **`Ir` (Instruction Read / Executed):** The total number of x86_64 or ARM assembly instructions executed. **This number is 100% deterministic!** Running the exact same input on a supercomputer or a Raspberry Pi will yield the exact same `Ir` count!
2. **`I1mr` / `ILmr` (Instruction Cache Misses):** Code too large to fit in L1/L3 instruction caches, causing CPU pipeline stalls.
3. **`D1mr` / `DLmr` (Data Cache Misses):** The #1 killer of systems performance! Indicates your algorithm is jumping across fragmented RAM (e.g., pointer-chasing through linked lists or scattered `Box<T>` nodes) instead of accessing contiguous memory (like `Vec<T>`).
4. **`Bc` / `Bcm` (Branch Conditional Mispredictions):** Unpredictable `if`/`else` branches that flush the CPU speculative execution pipeline.

### Systems Optimization Workflow:
* Replace pointer-based data structures (`LinkedList`, graph nodes with `Rc<RefCell<T>>`) with contiguous flat arrays (`Vec<T>`, `SlotMap`).
* Re-run Callgrind and watch `D1mr` (Data Cache Misses) plummet by orders of magnitude!
