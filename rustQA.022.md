# Rust Q&A: Managing Local Libraries in Subdirectories (Workspace vs. Modules)

When structuring large Rust projects, organizing internal libraries or helper tools into subdirectories (such as a folder named `my`) is standard practice. However, **where** that folder is located—either parallel to `src/` or nested inside `src/`—dictates how Rust and Cargo compile and link your code.

This guide covers the industry-standard design patterns and step-by-step commands for both architectures:
1. **Workspace Path Dependencies** (When `my/` is parallel to `src/`).
2. **Internal Module Tree** (When `my/` is nested inside `src/my/`).

---

## 1. The Workspace Pattern (`my/` Parallel to `src/`)

When your local libraries sit parallel to your root `src/` directory, they are treated as independent Cargo packages (crates). To link them efficiently without duplicating build artifacts, you should wrap the project in a **Cargo Workspace**.

### Architecture & Directory Layout
```text
app_root/
├── Cargo.toml            <-- Root manifest & Workspace configuration
├── src/
│   └── main.rs           <-- Main binary entry point
└── my/                   <-- Folder containing local library crates
    ├── math_tools/
    │   ├── Cargo.toml    <-- Library 1 manifest
    │   └── src/
    │       └── lib.rs    <-- Library 1 source code
    └── string_tools/
        ├── Cargo.toml    <-- Library 2 manifest
        └── src/
            └── lib.rs    <-- Library 2 source code
```

### Step-by-Step Implementation

#### Step 1: Initialize the Root Binary and Libraries
Open your terminal and generate the project structure using Cargo:

```bash
# 1. Create the main root binary package
cargo new app_root
cd app_root

# 2. Generate the local library crates inside the "my" subdirectory
cargo new --lib my/math_tools
cargo new --lib my/string_tools
```

#### Step 2: Configure the Workspace in `app_root/Cargo.toml`
Open the root `Cargo.toml`. You must define the `[workspace]` table and declare your path dependencies:

```toml
[package]
name = "app_root"
version = "0.1.0"
edition = "2021"

# 1. Define the workspace members so all crates share a single target/ build folder
[workspace]
members = [
    ".",
    "my/math_tools",
    "my/string_tools",
]

# 2. Link local libraries using the relative "path" attribute
[dependencies]
math_tools = { path = "my/math_tools" }
string_tools = { path = "my/string_tools" }
```

> [!TIP]
> **Why use `[workspace]`?** Without a workspace table, Cargo creates independent `target/` directories inside `my/math_tools/` and `my/string_tools/`. This causes redundant compilation of shared third-party dependencies and bloats disk space. With `[workspace]`, all artifacts compile into one unified `app_root/target/` directory and share a single `Cargo.lock`.

#### Step 3: Write Public Library APIs
In Rust library crates, any item (function, struct, enum, or module) intended for use by external binary crates must be explicitly marked with the `pub` keyword.

**`my/math_tools/src/lib.rs`**:
```rust
//! Math Tools Library

/// Adds two integers together.
pub fn add_numbers(a: i32, b: i32) -> i32 {
    a + b
}

/// A 2D Point structure.
#[derive(Debug, Clone, Copy)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    pub fn distance_to_origin(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}
```

**`my/string_tools/src/lib.rs`**:
```rust
//! String Tools Library

/// Capitalizes the first character of a string slice and lowercases the rest.
pub fn capitalize(input: &str) -> String {
    let mut chars = input.chars();
    match chars.next() {
        None => String::new(),
        Some(first) => {
            first.to_uppercase().collect::<String>() + &chars.as_str().to_lowercase()
        }
    }
}
```

#### Step 4: Import and Execute in `src/main.rs`
Because the libraries are declared in your root `Cargo.toml`, you import them into `main.rs` exactly like external crates from crates.io:

```rust
use math_tools::{add_numbers, Point};
use string_tools::capitalize;

fn main() {
    println!("=== Testing Workspace Libraries ===");
    let sum = add_numbers(15, 27);
    println!("15 + 27 = {}", sum);

    let pt = Point::new(3.0, 4.0);
    println!("Point: {:?}, Distance: {:.2}", pt, pt.distance_to_origin());

    let formatted = capitalize("rUSTACEAN");
    println!("Formatted String: {}", formatted);
}
```

#### Step 5: Build and Test Across the Workspace
From the root directory (`app_root/`), you can execute Cargo commands across the entire workspace simultaneously:

```bash
# Run the root binary program
cargo run

# Run unit tests across app_root, math_tools, and string_tools in one command
cargo test

# Check syntax and type safety across all workspace members
cargo check --workspace
```

---

## 2. The Internal Module Pattern (`my/` Inside `src/`)

If architectural constraints require the `"my"` directory to live inside `src/` (i.e., `src/my/`), **how Rust treats your code changes fundamentally**.

Anything placed inside `src/` is naturally part of the **same crate**. Therefore, instead of creating independent Cargo packages with separate `Cargo.toml` manifests, you should organize `math_tools` and `string_tools` as **Rust Modules**.

### Architecture & Directory Layout
```text
app_root/
├── Cargo.toml            <-- Only ONE root manifest is needed!
└── src/
    ├── main.rs           <-- Binary entry point
    ├── my.rs             <-- Module declaration file for the "my/" folder
    └── my/               <-- Subdirectory inside src/
        ├── math_tools.rs <-- Module 1 source code
        └── string_tools.rs <-- Module 2 source code
```

### Step-by-Step Implementation

#### Step 1: Declare the Module Tree (`src/my.rs`)
To make Rust recognize the contents of the `src/my/` directory, create a module declaration file named `src/my.rs` (or `src/my/mod.rs`). This file exposes the inner modules:

```rust
// src/my.rs
pub mod math_tools;
pub mod string_tools;
```

#### Step 2: Write Module Source Code
Inside `src/my/math_tools.rs` and `src/my/string_tools.rs`, define your code. Remember that functions and structs must still be marked `pub` to be accessible from `main.rs`:

```rust
// src/my/math_tools.rs
pub fn multiply_numbers(a: i32, b: i32) -> i32 {
    a * b
}
```

```rust
// src/my/string_tools.rs
pub fn reverse_str(input: &str) -> String {
    input.chars().rev().collect()
}
```

#### Step 3: Declare and Import in `src/main.rs`
In your main entry point, declare the top-level module with `mod my;`, and then import items using the `my::` namespace hierarchy:

```rust
// src/main.rs

// 1. Declare the root module (matches src/my.rs)
mod my;

// 2. Bring functions into scope from the internal module tree
use my::math_tools::multiply_numbers;
use my::string_tools::reverse_str;

fn main() {
    println!("=== Testing Internal Modules ===");
    let product = multiply_numbers(6, 7);
    println!("6 * 7 = {}", product);

    let reversed = reverse_str("Antigravity");
    println!("Reversed: {}", reversed);
}
```

---

## 3. Comparison & Best Practices

| Feature / Consideration | Workspace Path Dependencies (`my/` parallel to `src/`) | Internal Modules (`src/my/`) |
| :--- | :--- | :--- |
| **Cargo Manifests** | Requires multiple `Cargo.toml` files (one per library + root). | Requires only ONE root `Cargo.toml`. |
| **Compilation Unit** | Each library compiles as an independent crate (better parallel compilation). | Everything compiles as a single crate (fast for smaller codebases). |
| **Import Syntax** | `use math_tools::...;` (acts like an external crate). | `use my::math_tools::...;` (hierarchical module path). |
| **Publishing** | Each crate can be published independently to crates.io. | Published as a single unified package. |
| **Recommended Use Case** | Large, reusable libraries; multi-crate ecosystems; distinct feature flags. | Internal application logic; helper utilities; tightly coupled subsystems. |

> [!WARNING]
> **Why Nested Cargo Packages Inside `src/` Are Discouraged:**
> While Cargo technically permits placing independent library crates (with their own `Cargo.toml`) inside another crate's `src/` folder by writing `{ path = "src/my/math_tools" }`, this violates Rust conventions. It can cause IDE indexing bugs in `rust-analyzer`, break file watchers like `cargo watch`, and trigger packaging failures during `cargo publish` because packaging tools expect everything under `src/` to be raw source code of the parent crate.
> 
> **Rule of Thumb:**
> * If code lives inside `src/` ➔ Organize as **Rust Modules** (`mod my;`).
> * If code requires independent `Cargo.toml` packages ➔ Place folders **parallel to `src/`** in a Cargo Workspace.

---

## 4. How to Create and Declare Internal Modules (No Cargo Commands Required)

A common misconception among developers new to Rust is looking for a Cargo command like `cargo add --mod` or `cargo new --mod` to generate modules. 

Because modules are internal structural units of your existing crate rather than external packages, **there are NO special Cargo commands for creating modules!** You create modules simply by creating `.rs` files or directories in your filesystem and declaring them in your crate root (`src/main.rs` or `src/lib.rs`).

### The 2 Module File Structures
```text
my_project/
├── Cargo.toml
└── src/
    ├── main.rs            <-- Crate Root (declares top-level modules)
    ├── network.rs         <-- 1. Single-File Module
    ├── database.rs        <-- 2. Directory Module Root File
    └── database/          <-- Folder containing database sub-modules
        ├── models.rs      <-- Sub-module 1
        └── queries.rs     <-- Sub-module 2
```

### Step-by-Step Walkthrough

#### Step 1: Create Module Files in the Terminal
Use standard shell commands (`touch`, `mkdir`) or your IDE to create the files inside `src/`:

```bash
# Navigate to your project root
cd my_project

# 1. Create a Single-File Module (src/network.rs)
touch src/network.rs

# 2. Create a Directory Module with sub-modules (src/database.rs + src/database/)
touch src/database.rs
mkdir -p src/database
touch src/database/models.rs src/database/queries.rs
```

#### Step 2: Write Module Code
In Rust, everything inside a module is **private by default**. Any struct, enum, function, or sub-module intended for access from outside the module **must be marked with `pub`** (public).

**`src/network.rs`**:
```rust
/// Connects to a remote server.
pub fn connect(url: &str) {
    println!("Connecting to {}...", url);
}
```

**`src/database.rs`** (Directory Module Root):
```rust
// Declare and re-export the sub-modules inside the "src/database/" folder
pub mod models;
pub mod queries;
```

**`src/database/models.rs`**:
```rust
#[derive(Debug)]
pub struct User {
    pub id: u64,
    pub username: String,
}
```

**`src/database/queries.rs`**:
```rust
use super::models::User; // Use "super" to reference sibling modules

pub fn fetch_user(id: u64) -> User {
    User {
        id,
        username: "antigravity_user".to_string(),
    }
}
```

#### Step 3: Declare the Modules in Your Crate Root
Rust does not automatically scan your filesystem for `.rs` files. You **must explicitly declare** top-level modules in your crate root (**`src/main.rs`** for binaries or **`src/lib.rs`** for libraries) using `mod <name>;`.

**`src/main.rs`**:
```rust
// 1. DECLARE THE TOP-LEVEL MODULES
// Tells Rust: "Look for src/network.rs and src/database.rs and compile them!"
mod network;
mod database;

// 2. BRING ITEMS INTO SCOPE
use crate::network::connect;
use crate::database::{models::User, queries::fetch_user};

fn main() {
    println!("=== Testing Network Module ===");
    connect("https://api.rust-lang.org");

    println!("\n=== Testing Database Module ===");
    let user: User = fetch_user(42);
    println!("Fetched User: {:?}", user);
}
```

#### Step 4: Verify and Execute Using Standard Cargo Commands
Once your module files are created and declared with `mod`, use standard Cargo commands from your terminal to verify syntax and run:

```bash
# Super fast type and syntax check across all modules
cargo check

# Compile and run the binary
cargo run
```

> [!IMPORTANT]
> **Core Rule of Rust Modules:**
> * **`mod foo;` (with a semicolon)** in `main.rs` or `lib.rs` means: *"Go find `src/foo.rs` or `src/foo/mod.rs` and compile it into the crate tree here."* You only write `mod foo;` **once** per module in its parent file.
> * **`use foo::bar;`** means: *"Bring the symbol `bar` from the already-declared module `foo` into my current scope."*

