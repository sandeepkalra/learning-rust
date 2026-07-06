# Rust Q&A: Tracking Heap Allocations, Frees, and Memory Leak Testing

## Question: How can you intercept heap allocations and run leak tests in Rust?

### Question
In Rust, is there a way to print when internal heap allocations and deallocations (frees) occur, along with their sizes? Furthermore, how do I run leak tests on my code to detect memory leaks?

---

### Answer
Yes! In Rust, you can intercept and print **every single heap allocation and deallocation (free)** along with their exact sizes and alignment by writing a **Custom Global Allocator**. 

Furthermore, because Rust guarantees memory safety but **not** leak freedom (e.g., reference counting cycles with `Rc`/`Arc` or `Box::leak` can leak memory), there are powerful industry-standard tools to run **leak tests** on your code.

Here is the complete guide to printing heap activity and detecting memory leaks in Rust.

---

#### 1. How to Print Heap Allocations & Frees
Rust delegates all heap allocations (`Box`, `Vec`, `String`, `HashMap`, etc.) to a global allocator. You can intercept these calls by defining a wrapper struct around the system allocator (`std::alloc::System`), implementing the **`GlobalAlloc`** trait, and registering it with `#[global_allocator]`.

##### ⚠️ The Re-entrancy Hazard (Infinite Recursion Trap!)
When logging inside `alloc()`, you must be extremely careful: **You cannot use `println!()`, `format!()`, or create a `String`!** 
Why? Because `println!` and formatting macros allocate heap memory for internal buffering. If your custom allocator calls `println!`, which calls `alloc()`, which calls `println!`, your program will instantly crash from **infinite recursion and a stack overflow**.

To log safely, we use simple atomic counters and write primitive debug output to `stderr` (or use raw file descriptors).

##### Complete Runnable Code: The Tracking Allocator
Here is how to build your own custom tracking allocator:

```rust
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

struct TrackingAllocator {
    inner: System,
    allocated_bytes: AtomicUsize,
    deallocated_bytes: AtomicUsize,
}

unsafe impl GlobalAlloc for TrackingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        // 1. Perform the actual heap allocation via system malloc
        let ptr = self.inner.alloc(layout);
        
        if !ptr.is_null() {
            let size = layout.size();
            self.allocated_bytes.fetch_add(size, Ordering::SeqCst);
            
            // 2. Safe low-level printing to stderr
            eprintln!(
                "[HEAP ALLOC]   +{} bytes (align {}) at {:?}",
                size, layout.align(), ptr
            );
        }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        let size = layout.size();
        self.deallocated_bytes.fetch_add(size, Ordering::SeqCst);
        
        eprintln!(
            "[HEAP DEALLOC] -{} bytes (align {}) at {:?}",
            size, layout.align(), ptr
        );
        
        // 3. Perform the actual deallocation via system free
        self.inner.dealloc(ptr, layout);
    }
}

// Register our custom allocator globally for the entire program
#[global_allocator]
static GLOBAL: TrackingAllocator = TrackingAllocator {
    inner: System,
    allocated_bytes: AtomicUsize::new(0),
    deallocated_bytes: AtomicUsize::new(0),
};

fn main() {
    eprintln!("--- Starting Program ---");
    
    // This will trigger [HEAP ALLOC]
    let mut numbers = Vec::with_capacity(4); 
    
    // Pushing elements won't reallocate until capacity (4) is exceeded
    numbers.push(10);
    numbers.push(20);
    numbers.push(30);
    numbers.push(40);
    
    // This push exceeds capacity! Triggers [HEAP ALLOC] (larger buffer)
    // and [HEAP DEALLOC] (freeing the old buffer)!
    numbers.push(50); 

    eprintln!("--- End of Main (Variables dropping next) ---");
    // As `numbers` goes out of scope here, it triggers [HEAP DEALLOC]!
}
```

---

#### 2. How to Run Leak Tests in Rust
How do you find memory leaks or write automated unit tests to prove your code doesn't leak? There are **4 primary approaches** used in the Rust ecosystem:

##### A. The Industry Standard: The `dhat` Crate ⭐
The **`dhat`** crate (Dynamic Heap Analysis Tool) is the gold standard for heap profiling and leak detection in Rust. It is powered by Valgrind's DHAT algorithm but runs natively inside Rust without needing external software!

* It tracks exact allocation counts, peak memory usage, and **prints stack traces of any memory leaks when the program exits**!

**How to use `dhat`:**
In your `Cargo.toml`:
```toml
[dependencies]
dhat = "0.3"
```

In your `src/main.rs` or test file:
```rust
use dhat::{Dhat, Profiler};

#[global_allocator]
static ALLOC: Dhat = Dhat;

fn main() {
    // 1. Start the profiler at the beginning of main or test
    let _profiler = Profiler::new_heap();

    println!("Running code...");
    
    // Let's intentionally leak memory on the heap!
    let _leaked = Box::leak(Box::new(vec![1, 2, 3, 4, 5])); 

    // 2. When `_profiler` is dropped at the end of scope, DHAT automatically
    //    analyzes the heap, reports leaks, and generates a visual JSON report!
}
```

**Output:**
```text
dhat: Total:     20 bytes in 1 blocks
dhat: At t-gmax: 20 bytes in 1 blocks
dhat: At t-end:  20 bytes in 1 blocks (LEAKED!)
dhat: The data has been saved to dhat-heap.json, and is viewable with dhat/dh-view.html
```
You can open `dhat-heap.json` in a browser to see the exact function and line number where the leaked memory was allocated!

---

##### B. LLVM LeakSanitizer (LSan) via Cargo (Fast & Built-in)
The Rust compiler has built-in support for LLVM's **LeakSanitizer (LSan)** and **AddressSanitizer (ASan)** on nightly Rust. This runs significantly faster than external analysis tools and integrates directly into `cargo test`.

**How to run leak tests:**
```bash
# Run all your unit tests with LeakSanitizer enabled:
RUSTFLAGS="-Zsanitizer=leak" cargo test --target x86_64-unknown-linux-gnu
```
If any unit test leaks memory (such as creating an `Rc`/`Arc` reference cycle that fails to drop), LSan will immediately fail the test and print the exact C++/Rust call stack that allocated the leaked bytes.

---

##### C. In-Code Unit Testing via Custom Allocator
If you want to write automated unit tests in stable Rust without adding external dependencies or nightly flags, you can use our `TrackingAllocator` from Section 1 to assert zero leaks programmatically!

```rust
#[test]
fn test_for_memory_leaks() {
    // 1. Record baseline heap usage before test execution
    let alloc_before = GLOBAL.allocated_bytes.load(Ordering::SeqCst);
    let dealloc_before = GLOBAL.deallocated_bytes.load(Ordering::SeqCst);

    // 2. Run the code or function you want to test
    {
        let mut data = vec![1, 2, 3, 4, 5];
        data.push(6);
        // `data` goes out of scope and drops here
    }

    // 3. Record heap usage after execution
    let alloc_after = GLOBAL.allocated_bytes.load(Ordering::SeqCst);
    let dealloc_after = GLOBAL.deallocated_bytes.load(Ordering::SeqCst);

    let net_bytes_added = (alloc_after - alloc_before) - (dealloc_after - dealloc_before);

    // 4. Assert that every byte allocated during the test was deallocated!
    assert_eq!(
        net_bytes_added, 0,
        "MEMORY LEAK DETECTED! Leaked {} bytes!", net_bytes_added
    );
}
```

---

##### D. Valgrind / Memcheck (System-Level Analysis)
On Linux/macOS, you can run your compiled Rust binary under **Valgrind**:
```bash
cargo build --release
valgrind --leak-check=full --show-leak-kinds=all ./target/release/your_app
```
Valgrind monitors machine-code memory instructions and reports any lost blocks at program termination.

---

#### 3. Summary Comparison Table

| Tool / Method | Ease of Setup | Runtime Overhead | Best Used For |
| :--- | :--- | :--- | :--- |
| **Custom `GlobalAlloc`** | Built-in (No crates needed) | Very Low | Learning how allocators work; logging live allocations to console; simple in-code test assertions. |
| **`dhat` Crate ⭐** | Excellent (Add to Cargo.toml) | Medium | Comprehensive heap profiling; finding peak memory usage; getting visual HTML/JSON leak reports. |
| **LLVM LeakSanitizer (`-Zsanitizer=leak`)** | High (Requires Nightly & target flag) | Low | Running fast, automated CI leak tests across your entire `cargo test` suite. |
| **Valgrind / Memcheck** | External OS installation | High (10x-20x slower) | System-level verification of complex FFI (C/C++) integrations or low-level unsafe Rust. |
