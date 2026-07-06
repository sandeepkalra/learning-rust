# Rust Q&A: String Concatenation, Ownership, Borrowing, and Multi-Threading

## Question 1: Single-Threaded String Concatenation & Borrowing

### Question
Consider the following Rust program:
```rust
fn main() {
    let mut m = String::from("hello ");
    let mut j = String::from("Kalra ");
    m = m + j.trim() + "!";
    j = String::from("NEW!");
    println!("msg:{m} , {j} ");
}
```
When `j.trim()` returns a slice without modifying the original `j`, and I modify `j` later (`j = String::from("NEW!")`), shouldn't the value of `m` reflect the wrong value or be affected by `j`?

---

### Answer
No, `m` will not be affected when `j` is modified later!

In Rust, the reason `m` retains `"hello Kalra!"` independently of `j` comes down to how string concatenation (`+`) works under the hood: **it copies the slice's bytes into `m`'s heap buffer**.

Here is a step-by-step breakdown of what happens in memory:

#### 1. `j.trim()` borrows `j` temporarily
```rust
j.trim()
```
* This returns a string slice (`&str`), which is a temporary immutable reference pointing to the characters `"Kalra"` inside `j`'s heap buffer.

#### 2. The `+` operator appends by copying bytes
```rust
m = m + j.trim() + "!";
```
* In Rust, using `+` on a `String` calls the `add` method, which has the signature:
  ```rust
  fn add(mut self, other: &str) -> String
  ```
* Notice that `self` (`m`) is taken by **ownership**, while `other` (`j.trim()`) is taken by **reference** (`&str`).
* When `m + j.trim()` executes, Rust takes the heap buffer owned by `m`, reads the characters from the `j.trim()` slice, and **copies those bytes directly into `m`'s buffer**.
* It then copies the `"!"` bytes into `m`'s buffer as well.
* At the end of this line, `m` is a completely independent `String` owning the heap allocation for `"hello Kalra!"`. It holds **no references or links** back to `j`.

#### 3. Modifying `j` later
```rust
j = String::from("NEW!");
```
* Because `m` already copied the text data into its own allocation, replacing `j` with a new `String` simply drops the old memory (`"Kalra "`) and assigns `"NEW!"` to `j`.
* The temporary borrow from `j.trim()` ended immediately after the concatenation line finished, allowing `j` to be safely modified or reassigned.

---

## Question 2: Multi-Threaded Behavior

### Question
What would have happened in a multi-threaded scenario where `m` and `j` are on different threads?

---

### Answer
If `m` and `j` were on different threads, **Rust's compiler would prevent data races at compile time**. You would either get a compile error or (if properly synchronized) the exact same safe outcome where `m` remains unaffected.

Here is what happens depending on how you try to write it:

#### 1. Without Synchronization: Compile Error ❌
If Thread 1 owns `m` and Thread 2 owns `j`, and Thread 1 tries to access `j.trim()` while Thread 2 mutates `j`:

```rust
use std::thread;

fn main() {
    let mut j = String::from("Kalra ");

    // Thread 1 tries to borrow `j`
    thread::scope(|s| {
        s.spawn(|| {
            let mut m = String::from("hello ");
            // ERROR: Cannot borrow `j` while another thread might mutate it!
            m = m + j.trim() + "!"; 
        });

        s.spawn(|| {
            // ERROR: Cannot mutate `j` while another thread borrows it!
            j = String::from("NEW!");
        });
    });
}
```

**Why it fails to compile:**
Rust enforces the fundamental borrowing rule across all threads: **You can have either any number of immutable references (`&T`) or exactly one mutable reference (`&mut T`), but never both at the same time.** 

If one thread could mutate `j`'s heap buffer (freeing old memory and reallocating `"NEW!"`) at the exact millisecond another thread was reading `j.trim()`, it would cause a **Use-After-Free crash or Segmentation Fault** (common in C/C++). Rust makes this impossible at compile time.

#### 2. With Safe Synchronization (`Arc<Mutex<String>>`): Safe & Unaffected ✅
To share `j` safely across threads, you wrap it in an Atomic Reference Count (`Arc`) and a Mutex (`Mutex`):

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let j = Arc::new(Mutex::new(String::from("Kalra ")));
    let j_clone = Arc::clone(&j);

    // Thread 1: Reads j and appends to m
    let handle1 = thread::spawn(move || {
        let mut m = String::from("hello ");
        {
            // Lock the mutex to get read access to j
            let guard = j.lock().unwrap();
            m = m + guard.trim() + "!";
            // Lock is released here when `guard` goes out of scope
        }
        println!("Thread 1 m: {}", m); // Output: hello Kalra!
    });

    // Thread 2: Mutates j
    let handle2 = thread::spawn(move || {
        // Lock the mutex to get write access to j
        let mut guard = j_clone.lock().unwrap();
        *guard = String::from("NEW!");
    });

    handle1.join().unwrap();
    handle2.join().unwrap();
}
```

**What happens here:**
1. **Mutual Exclusion:** The `Mutex` guarantees that only one thread can access `j` at a time.
2. **Safe Copying:** If Thread 1 acquires the lock first, Thread 2 is paused. Thread 1 copies the bytes `"Kalra"` into `m`'s own heap buffer and releases the lock.
3. **Independent Memory:** Once the lock is released, Thread 2 acquires it and overwrites `j` with `"NEW!"`. Because `m` already copied the bytes into its own private allocation on Thread 1, `m` is **completely unaffected**.
