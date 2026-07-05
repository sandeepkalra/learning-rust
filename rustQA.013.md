# Rust Q&A: Named Function Arguments & Idiomatic Method Chaining

## Question 1: Does Rust allow named function calling arguments (like Swift)?

### Question
In Rust function calls, are named arguments allowed like in Swift (`createWindow(width: 800, height: 600)`) or Python?

---

### Answer
**No, standard Rust functions do not support named arguments.**

Unlike Swift or Python, standard function calls in Rust are strictly positional (`create_window(800, 600)`).

Why? The Rust language design team decided that making parameter names part of the public API signature would make refactoring harder (renaming an internal variable inside a function definition would suddenly break third-party code calling it!).

---

#### How Idiomatic Rust Achieves Named Calling ⭐

When a function takes multiple parameters (especially booleans or numbers), Rust programmers use two standard patterns to get named arguments and default values:

##### 1. The Struct Argument Pattern (Options Struct)
You bundle the parameters into a struct. Because Rust struct instantiation requires **named fields**, you get named calling syntax automatically!

```rust
// 1. Define an options struct
#[derive(Default)]
struct WindowConfig {
    width: u32,
    height: u32,
    fullscreen: bool,
}

fn create_window(config: WindowConfig) {
    println!("Creating window: {}x{}", config.width, config.height);
}

fn main() {
    // 2. Call the function using named struct fields!
    create_window(WindowConfig {
        width: 1920,
        height: 1080,
        fullscreen: true,
    });
}
```

###### Bonus: Partial Named Arguments with Defaults!
If your struct derives `Default`, you can specify *only* the named arguments you care about and let Rust fill in the rest using the `..Default::default()` syntax:

```rust
create_window(WindowConfig {
    width: 2560,
    ..Default::default() // Fills height=0 and fullscreen=false automatically!
});
```

---

##### 2. The Builder Pattern (The Gold Standard for Complex APIs)
For complex objects (like HTTP requests, database connections, or GUI widgets), idiomatic Rust uses the **Builder Pattern**. By chaining methods, you get self-documenting, named configuration:

```rust
let client = HttpClientBuilder::new()
    .timeout(30)
    .user_agent("MyRustApp/1.0")
    .enable_ssl(true)
    .build();
```

---

## Question 2: Does idiomatic method chaining prefer returning `&mut Self`?

### Question
For writing code that can be chained idiomatically, does Rust prefer to return `&mut T` (`&mut Self`) from a function?

---

### Answer
**No!** In idiomatic Rust, returning `&mut Self` is **not** the preferred default for method chaining.

Instead, idiomatic Rust builders prefer **taking and returning ownership by value (`mut self -> Self`)**.

Here is why Rust prefers **By-Value Chaining (`Self`)** over **By-Reference Chaining (`&mut Self`)**:

#### 1. The Idiomatic Gold Standard: By-Value Chaining (`mut self -> Self`) ⭐
In by-value chaining, each method takes ownership of `self`, modifies it, and returns the owned `Self` to the caller:

```rust
struct WindowBuilder {
    width: u32,
    height: u32,
}

impl WindowBuilder {
    pub fn new() -> Self {
        WindowBuilder { width: 0, height: 0 }
    }

    // Takes ownership (`mut self`) and returns ownership (`Self`)
    pub fn width(mut self, w: u32) -> Self {
        self.width = w;
        self
    }

    pub fn height(mut self, h: u32) -> Self {
        self.height = h;
        self
    }
}
```

##### Why Rust prefers this:
1. **Clean One-Liner Expressions:** You can construct and chain everything in one smooth, unbroken expression without declaring a temporary `let mut` variable:
   ```rust
   let builder = WindowBuilder::new().width(800).height(600);
   ```
2. **Compile-Time Type-State Transformations:** Because by-value chaining consumes `self`, a method can actually return a **completely different type**! For example, `.authenticate()` can consume `Request<Locked>` and return `Request<Unlocked>`. You cannot do this with `&mut Self`!

---

#### 2. When is `&mut self -> &mut Self` used?
You only return `&mut Self` when your API is specifically designed to modify an **already existing, long-lived object** across multiple lines or inside loops (such as the standard library's `std::process::Command`).

```rust
impl WindowBuilder {
    // Takes a mutable reference and returns a mutable reference
    pub fn set_width(&mut self, w: u32) -> &mut Self {
        self.width = w;
        self
    }
}
```

##### The Downside of `&mut Self` Chaining:
If you try to chain a `&mut Self` builder directly from a constructor in one line:
```rust
// ❌ Can cause borrow-checker lifetime errors about temporary values dropped while borrowed!
let win = WindowBuilder::new().set_width(800); 
```
To use `&mut Self` safely, callers are often forced to write noisy two-step code:
```rust
let mut builder = WindowBuilder::new(); // Must declare `mut` variable first
builder.set_width(800).set_height(600);
```

---

#### Summary Checklist
* Use **`mut self -> Self` (By-Value)** for constructing new objects (Builder Pattern). It gives you clean one-liners and advanced type-state safety.
* Use **`&mut self -> &mut Self` (By-Reference)** only when modifying pre-existing objects in place where the caller already owns the variable.
