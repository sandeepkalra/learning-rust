# Rust Q&A: Zero-Sized Types (ZSTs), Unit Tuples `()`, Empty Enums, and Unit Structs

## Question 1: Are size-0 tuples and size-0 enums allowed in Rust, and what are their uses?

### Question
Are tuples and enums of size 0 allowed in Rust? What are the practical use cases for them?

---

### Answer
**Yes, absolutely!** Both size-0 tuples and size-0 enums are not only allowed, but they are foundational pillars of Rust's standard library.

Despite both being **0 bytes (`std::mem::size_of::<T>() == 0`)**, they serve completely opposite mathematical purposes:

#### 1. The Size-0 Tuple: The Unit Type `()`
A tuple with zero elements `()` is called the **Unit Type**. It has exactly **one valid value** (written as `()`).

##### Real-world uses:
* **Replacing C/C++ `void` as a First-Class Type:** In C/C++, `void` is a special keyword that cannot be stored in variables. In Rust, functions that don't return anything implicitly return `()`:
  ```rust
  fn print_msg() -> () {
      println!("Hello!");
  } // Returns `()` taking 0 bytes!
  ```
* **Zero-Cost Event Signaling & Channels:** If you are sending thread signals or async channel notifications where you only care *when* an event happens (not sending data), you use `()` as the payload:
  ```rust
  let (tx, rx) = std::sync::mpsc::channel::<()>();

  // Sending a signal across threads sends literally 0 bytes of payload memory!
  tx.send(()); 
  ```
* **`Result<(), Error>` for Success Signals:** When a function performs an action (like writing to a file) that can fail with an `Error`, but returns no data on success, you return `Ok(())`.

---

#### 2. The Size-0 Enum: Uninstantiable Enums (`enum Void {}` / `Infallible`)
An enum with **zero variants** (`enum Void {}` or standard library `std::convert::Infallible`) is completely legal. It has **zero valid values**.

Because it has no variants, **it is physically and logically impossible to ever create an instance of this enum at runtime!**

##### Real-world uses:
* **Compile-Time Proof that an Error is Impossible (`Infallible`):** Imagine you implement a standard interface that returns a `Result<T, Error>`. If your specific implementation is mathematically guaranteed **never to fail**, you set the error type to a 0-variant enum (`std::convert::Infallible`):
  ```rust
  use std::convert::TryFrom;

  // Converting a small u8 into a larger u32 can NEVER fail!
  // Therefore, standard library sets the Error type to `Infallible` (0-variant enum).
  let result: Result<u32, std::convert::Infallible> = u32::try_from(10_u8);
  ```
  Because the compiler knows an instance of `Infallible` can never exist in the universe, it **optimizes away all error-checking branches at compile time**!

---

#### Summary Comparison Table

| Type | Syntax Example | Valid Runtime Values | Primary Meaning / Use Case |
| :--- | :--- | :---: | :--- |
| **Size-0 Tuple** | `()` | Exactly **1** (`()`) | *"This operation completed successfully and carries 0 bytes of data."* |
| **Size-0 Enum** | `enum Void {}` | Exactly **0** (Impossible) | *"This situation/error is mathematically impossible to ever occur."* |

---

## Question 2: How is `struct Name()` different from `let object = ()`?

### Question
How is an instance of a unit tuple struct (`struct Name()`) different from an instance of the unit primitive (`let object = ()`)?

---

### Answer
At the hardware memory level, they are **100% identical**: both take up **0 bytes** of memory (`size_of::<Name>() == 0` and `size_of::<()>() == 0`).

However, at the compiler and type-system level, they are **fundamentally different**:

#### 1. Distinct Type Identity (Nominal vs. Structural Typing)
* **`()` (Unit Type):** Is a built-in global primitive type. Every `()` anywhere in your entire codebase is the exact same type.
* **`struct Name();`:** Creates a brand new, unique **Nominal Type**. 

Because Rust enforces strict type safety, you **cannot** pass `Name()` into a function expecting `()`, nor can you pass `()` into a function expecting `Name()`:

```rust
struct Name();
struct Other();

fn process_unit(item: ()) {}
fn process_name(item: Name) {}

fn main() {
    let a = Name();
    let b = ();

    // process_unit(a); // ❌ COMPILE ERROR! Expected `()`, found `Name`
    // process_name(b); // ❌ COMPILE ERROR! Expected `Name`, found `()`
}
```

#### 2. Trait Implementations (The Orphan Rule)
In Rust, the **Orphan Rule** forbids you from implementing external traits on external types. 
* Because `()` is a standard library primitive, you cannot implement custom third-party traits on `()` in your crate.
* Because `struct Name();` belongs to your crate, **you can implement any trait you want on it!**

```rust
struct Name();

// Perfectly legal! You can attach behaviors and methods to your 0-byte struct:
impl Iterator for Name {
    type Item = i32;
    fn next(&mut self) -> Option<i32> { None }
}
```

---

#### Why would a programmer use `struct Name()` instead of `()`? ⭐

Because `struct Name()` gives you a unique, distinct type name while costing **0 bytes of RAM**, senior Rust developers use it for two powerful patterns:

##### A. Compile-Time Security Tokens (Type-State Pattern)
Imagine you are building a secure API where certain actions require administrative privileges:
```rust
struct AdminToken(); // 0 bytes!
struct GuestToken(); // 0 bytes!

fn delete_database(token: AdminToken) {
    println!("Database deleted!");
}
```
If a user only has a `GuestToken()`, the compiler will **block them at compile time** from calling `delete_database`. Yet, because `AdminToken` is 0 bytes, passing it around costs **zero hardware runtime overhead**!

##### B. Stateless Action Handlers / Strategies
If you need to pass a stateless algorithm or configuration struct into a generic function (`fn run<T: Strategy>(handler: T)`), passing a 0-byte struct (`struct FastStrategy();`) lets the compiler inline all methods with zero memory allocation.
