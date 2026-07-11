# Rust Q&A: Custom Deref Coercion vs. Borrowed Views (`Deref` vs. `.as_view()`)

A common architectural question when working with Rust's type system is whether **Deref Coercion** (`std::ops::Deref`) is exclusive to standard library smart pointers (`Box<T>`, `Arc<T>`, `String`, `Vec<T>`), and whether an owned composite struct (like `struct B { a: String, b: Vec<String> }`) can implement `Deref` to produce a borrowed view struct (`struct A<'a> { a: &'a str, b: Vec<&'a str> }`).

This topic explores how custom `Deref` implementations work, why returning temporary stack allocations from `deref(&self)` fails the borrow checker, and how to idiomatically design memory-safe borrowed views in Rust.

---

## 1. Can Custom Structs Implement `Deref`?

**Yes, you can implement `Deref` (and `DerefMut`) on your own custom structs!** 

Deref coercion is not compiler magic reserved for standard library types. Any custom struct `MyStruct<T>` that implements `std::ops::Deref<Target = U>` automatically gains **Deref Coercion**.

When Rust encounters a reference `&MyStruct` passed to a function expecting `&TargetType`, or when a method belonging to `TargetType` is invoked on `&MyStruct`, the compiler automatically inserts `.deref()` calls at compile time (`&MyStruct -> &TargetType`). If `TargetType` also implements `Deref`, Rust chains the coercions transparently.

---

## 2. Why `struct B` Cannot `Deref` to `struct A<'a>`

Consider the following two structs:

```rust
pub struct A<'a> {
    pub a: &'a str,
    pub b: Vec<&'a str>,
}

pub struct B {
    pub a: String,
    pub b: Vec<String>,
}
```

Attempting to implement `Deref<Target = A<'a>>` for `struct B` reveals the **core memory constraint of the `Deref` trait**:

```rust
impl<'a> std::ops::Deref for B {
    type Target = A<'a>;

    fn deref(&self) -> &Self::Target {
        // 1. To construct `A`, we must allocate a NEW Vec<&str> on the stack
        let temp_a = A {
            a: self.a.as_str(),
            b: self.b.iter().map(|s| s.as_str()).collect(),
        };

        // 2. Attempt to return a reference to the local stack variable
        &temp_a
    }
}
```

### The Borrow Checker Error
```text
error[E0515]: cannot return reference to local variable `temp_a`
  --> src/main.rs
   |
   |         &temp_a
   |         ^^^^^^^ returns a reference to data owned by the current function
```

### Why This Happens
Examine the trait signature:
```rust
pub trait Deref {
    type Target: ?Sized;
    fn deref(&self) -> &Self::Target;
}
```

Notice the return signature: `&Self::Target` (`&A`). Because `deref` takes `&self` (`&B`) and returns `&Self::Target`, **an instance of `Target` must already exist inside `self`'s memory address space.**

When constructing `temp_a` inside `deref()`, `temp_a` (and its inner `Vec<&str>`) is allocated on the local function stack. When `deref()` finishes executing, `temp_a` is dropped from the stack. Returning `&temp_a` would create a **dangling pointer**, which the Rust borrow checker strictly forbids.

---

## 3. The Golden Rule of `Deref` vs. Borrowed Views

1. **When to Use `Deref`:** `Deref` is exclusively designed for **Smart Pointers and Newtype Wrappers** that directly own or wrap an *already-existing* target object inside their memory layout (e.g., `Box<T>` pointing to `T` on the heap, or `struct Wrapper(T)` containing `T`).
2. **When NOT to Use `Deref`:** Never implement `Deref` if producing the target type requires allocating new composite data structures on the fly or performing complex data transformations.

---

## 4. The Idiomatic Approach: Borrowed Views (`.as_view()`)

When converting an owned struct `B` into a lightweight, borrowed view struct `A`, the idiomatic Rust design pattern is to provide an explicit **View Method** or implement the `From` / `Into` traits:

```rust
#[derive(Debug)]
pub struct A<'a> {
    pub a: &'a str,
    pub b: Vec<&'a str>,
}

#[derive(Debug)]
pub struct B {
    pub a: String,
    pub b: Vec<String>,
}

impl B {
    /// Idiomatic View Method: Creates a lightweight borrowed view A directly from &B
    pub fn as_view(&self) -> A<'_> {
        A {
            a: self.a.as_str(),
            b: self.b.iter().map(|s| s.as_str()).collect(),
        }
    }
}

// Implement From<&'a B> for ergonomic type conversions
impl<'a> From<&'a B> for A<'a> {
    fn from(owned: &'a B) -> Self {
        owned.as_view()
    }
}

fn process_view(view: A<'_>) {
    println!("View -> a: '{}', b: {:?}", view.a, view.b);
}

fn main() {
    let owned_b = B {
        a: "Antigravity".to_string(),
        b: vec!["Rust".to_string(), "Coercion".to_string()],
    };

    // 1. Explicit view conversion via method call
    let view = owned_b.as_view();
    process_view(view);

    // 2. Implicit conversion via trait bound
    process_view((&owned_b).into());
}
```

---

## 5. How Custom `Deref` Works in Practice

To demonstrate a valid custom `Deref` implementation where the target already exists inside `Self`, consider a custom smart pointer that counts how often its underlying data is accessed:

```rust
use std::ops::{Deref, DerefMut};
use std::cell::Cell;

/// A wrapper struct that tracks access frequency
pub struct TrackedWrapper<T> {
    pub inner: T,
    pub access_count: Cell<usize>,
}

impl<T> TrackedWrapper<T> {
    pub fn new(value: T) -> Self {
        Self {
            inner: value,
            access_count: Cell::new(0),
        }
    }
}

// Implement custom Deref coercion
impl<T> Deref for TrackedWrapper<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        // Increment access counter upon deref
        self.access_count.set(self.access_count.get() + 1);
        
        // Return a reference to `inner`, which already lives inside `Self`
        &self.inner
    }
}

fn main() {
    let my_wrapper = TrackedWrapper::new(vec!["apple", "banana", "cherry"]);

    // DEREF COERCION IN ACTION:
    // `my_wrapper` is of type `TrackedWrapper<Vec<&str>>`.
    // `.len()` and `.contains()` are methods belonging to `[T]` / `Vec<T>`.
    // Rust automatically inserts `.deref()` because TrackedWrapper implements Deref!
    println!("Length: {}", my_wrapper.len());
    println!("Contains apple: {}", my_wrapper.contains(&"apple"));

    println!("Total accesses via Deref: {}", my_wrapper.access_count.get());
}
```

---

## 6. Runtime Overhead & Performance: Collected Vector Views vs. Zero-Cost Slice Views

When evaluating the runtime performance of an idiomatic borrowed view (`as_view()`), the exact overhead depends on whether the target view struct contains **collected vectors** (`Vec<&str>`) or **slice references** (`&[String]`).

### Analysis of Collected Vector Views (`struct A`)

When `B::as_view(&self)` generates `A<'a> { a: &'a str, b: Vec<&'a str> }`:

```rust
pub fn as_view(&self) -> A<'_> {
    A {
        a: self.a.as_str(),
        b: self.b.iter().map(|s| s.as_str()).collect(),
    }
}
```

1. **Field `a: &'a str` ➔ Zero-Cost (`O(1)` Time, `0 bytes` Heap Memory)**
   A `&str` is a 16-byte fat pointer (8-byte memory address pointing to the `String` buffer + 8-byte length). Calling `self.a.as_str()` copies those two integers onto the stack. It requires zero character copying and zero heap allocations.
2. **Field `b: Vec<&'a str>` ➔ `O(N)` Time, `O(N)` Heap Allocation**
   Because `struct A` owns a vector (`Vec<&'a str>`), calling `.collect()` **must allocate a new `Vec` buffer on the heap** to hold `N` fat pointers (`&str`). Iterating over `self.b` (`N` strings) and inserting `N` pointers into the new vector takes `O(N)` CPU instructions and `O(N)` heap memory. If `self.b` contains 10,000 items, `as_view()` allocates heap memory for 10,000 pointers on every invocation.

---

### Achieving True Zero-Cost (`O(1)`) Views via Slice References

To make a view struct execute with **zero heap allocations and `O(1)` constant time** across all fields, replace the `Vec<&'a str>` collection with a **Slice Reference (`&'a [String]`)**:

```rust
#[derive(Debug, Clone, Copy)]
pub struct ZeroCostA<'a> {
    pub a: &'a str,
    pub b: &'a [String], // Borrowed slice reference instead of Vec<&str>!
}

impl B {
    /// True Zero-Cost Abstraction: 0 heap allocations, O(1) execution time
    pub fn zero_cost_view(&self) -> ZeroCostA<'_> {
        ZeroCostA {
            a: self.a.as_str(),   // O(1) fat pointer copy (16 bytes)
            b: self.b.as_slice(), // O(1) fat pointer copy (16 bytes)
        }
    }
}
```

### Performance Characteristics of `ZeroCostA`
* Calling `self.b.as_slice()` generates a `&[String]`, which is another 16-byte fat pointer pointing directly to the contiguous array of `String` headers inside `B::b`.
* **Total Cost of `zero_cost_view()`:** Constructing `ZeroCostA` simply copies four 8-byte integers (two fat pointers) onto the CPU stack.
* **Result:** **`0 bytes` allocated on the heap, zero iteration overhead, and `O(1)` constant execution time.** LLVM fully inlines this call to zero machine overhead.

### Architectural Comparison Table

| View Architecture | Field Types | Time Complexity | Heap Allocations | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Collected View** (`A<'a>`) | `a: &'a str`<br>`b: Vec<&'a str>` | `O(N)` ($N$ = vector length) | `O(N)` (allocates vector of pointers on heap) | APIs strictly requiring ownership of a `Vec<&str>`. |
| **Zero-Cost Slice View** (`ZeroCostA<'a>`) | `a: &'a str`<br>`b: &'a [String]` | `O(1)` constant time | **`0 bytes` (Zero Allocations)** | **99% of use cases.** Maximum performance, zero-cost abstractions, ultra-fast views. |

---

## 7. Demystifying Coercion Rules: `&String -> &str` and `&mut U -> &T` Coercions

Two common sources of confusion when learning `Deref` are why `&String` coerces to `&str` when they appear to be distinct types, and whether mutable references (`&mut U`) can coerce into immutable references (`&T`) on user-constructed structs.

### Why `&String` -> `&str` Works (`std::ops::Deref`)

`String` (a 24-byte owned struct containing `ptr`, `len`, and `capacity`) and `str` (a primitive dynamically sized slice of UTF-8 bytes) appear unrelated. However, `&String` automatically coerces to `&str` because **`std::string::String` implements `std::ops::Deref<Target = str>` directly in the Rust Standard Library**:

```rust
// From Rust Standard Library (std::string::String)
impl ops::Deref for String {
    type Target = str;

    #[inline]
    fn deref(&self) -> &str {
        unsafe { str::from_utf8_unchecked(&self.vec) }
    }
}
```

#### Why Does This Not Violate the `E0515` Local Variable Rule?
When `deref(&self)` is called on `&String`, `&self.vec` points directly to the **heap-allocated byte buffer (`[u8]`) that `String` (`self`) already owns in memory.** 

Because `str` is a raw sequence of UTF-8 bytes (`[u8]`) sitting on the heap inside `self.vec`, returning `&str` creates a 16-byte fat slice pointer (`ptr + len`) pointing directly into `String`'s existing heap allocation. No new composite objects are constructed on the stack, and zero character copies occur. Thus, `String -> &str` uses the exact same `Deref` trait mechanics as user-defined custom structs.

---

### Is `&mut U -> &T` Coercion Allowed for User-Defined Structs?

**Yes, `&mut U -> &T` coercion is fully supported and works across both standard library types and custom user-defined structs.**

This behavior is driven by two independent compiler rules operating sequentially:

1. **Rule 1: Mutability Degradation (`&mut X -> &X`)**
   If you hold an exclusive mutable reference (`&mut X`), it is always memory-safe to temporarily downgrade that access to a shared read-only reference (`&X`) when passing it to a function expecting `&X`. This rule applies universally to primitives, collections, and custom user structs.
2. **Rule 2: Chaining Degradation + Deref (`&mut U -> &U -> &T`)**
   When passing `&mut U` where `&T` is expected, `rustc` executes a two-step coercion chain at compile time:
   * **Step 1 (Downgrade):** `&mut U` weakens to `&U` via Mutability Degradation.
   * **Step 2 (Deref):** If `U` implements `Deref<Target = T>`, `rustc` calls `.deref()` (`&U -> &T`).

#### Complete Code Proof: Custom `&mut UserStruct -> &Target` Coercion

The following example demonstrates that `&mut CustomBox` (`&mut U`) coerces automatically when passed to a function expecting `&Vec<&str>` (`&T`):

```rust
use std::ops::Deref;

/// A custom user-constructed struct
pub struct CustomBox<T> {
    pub inner: T,
}

impl<T> Deref for CustomBox<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        &self.inner
    }
}

/// A function expecting an IMMUTABLE reference to Vec<&str> (&T)
fn inspect_vector(data: &Vec<&str>) {
    println!("Vector inside function: {:?}", data);
}

fn main() {
    let mut my_box = CustomBox {
        inner: vec!["apple", "banana"],
    };

    // WE PASS &mut CustomBox (&mut U) WHERE &Vec<&str> (&T) IS EXPECTED:
    // 1. Rust downgrades &mut CustomBox -> &CustomBox
    // 2. Rust calls Deref: &CustomBox -> &Vec<&str>
    inspect_vector(&mut my_box);
}
```

---

### What About `&mut U -> &mut T`? (`DerefMut`)

If the target function expects `&mut T` (mutable access to the inner target), Rust checks for the **`DerefMut` trait**:

```rust
pub trait DerefMut: Deref {
    fn deref_mut(&mut self) -> &mut Self::Target;
}
```

If your custom struct implements `DerefMut<Target = T>`, passing `&mut MyStruct` where `&mut T` is expected automatically invokes `.deref_mut()`, delegating mutable access directly to the target (`&mut U -> &mut T`).

---

### Summary Checklist of Reference Coercion Rules

| Coercion Pattern | Required Trait / Mechanism | Supported On User Structs? | Example |
| :--- | :--- | :--- | :--- |
| `&U -> &T` | `U: Deref<Target = T>` | **Yes** | `&String -> &str`<br>`&CustomBox<T> -> &T` |
| `&mut U -> &T` | `U: Deref<Target = T>` + Mutability Degradation (`&mut U -> &U -> &T`) | **Yes** | `&mut String -> &str`<br>`&mut CustomBox<T> -> &T` |
| `&mut U -> &mut T` | `U: DerefMut<Target = T>` | **Yes** | `&mut String -> &mut str`<br>`&mut CustomBox<T> -> &mut T` |
| `&U -> &mut T` | **Forbidden** (Violates Aliasing Safety) | **No** | Compile Error (`Cannot borrow immutable local variable as mutable`) |


