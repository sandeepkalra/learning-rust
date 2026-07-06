# Rust Q&A: Operator Overloading (`std::ops`), Custom Operators, and Macros

## Question 1: Can programmers overload the `+` operator for custom types like C++ `operator+()`?

### Question
In string operations in Rust, a `+` operator can be used (`String + &str`). Is this `+` operator similar to C++'s `operator+()`? If yes, can programmers implement it for custom types, or is it restricted to the standard library?

---

### Answer
**Yes, it is exactly like C++'s `operator+()`!** 

And no, it is **not** reserved for the standard library—**any Rust programmer can implement the `+` operator for their own custom types!**

In Rust, the `+` operator is simply syntactic sugar for calling the `.add()` method from the `std::ops::Add` trait. By implementing `std::ops::Add` for your struct, you unlock the `+` operator immediately.

#### Example 1: Adding two custom structs (`Point + Point`)
Let's create a 2D `Point` struct and overload the `+` operator so we can add two points together:

```rust
use std::ops::Add;

#[derive(Debug, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}

// 1. Implement the `Add` trait for our Point struct
impl Add for Point {
    type Output = Point; // Tells Rust what type `a + b` should return

    fn add(self, other: Point) -> Point {
        Point {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

fn main() {
    let p1 = Point { x: 10, y: 20 };
    let p2 = Point { x: 5,  y: 15 };

    // 2. We can now use the `+` operator directly!
    let p3 = p1 + p2; 

    println!("Result: {:?}", p3); // Output: Point { x: 15, y: 35 }
}
```

#### Example 2: Adding two *different* types (Just like `String + &str`!)
Notice how `String + &str` adds two completely different types together. You can do the exact same thing in your custom code!

For example, let's allow adding `Centimeters` to `Meters`:

```rust
use std::ops::Add;

#[derive(Debug)]
struct Meters(f64);
struct Centimeters(f64);

// Implement `Add<Centimeters>` on `Meters`
impl Add<Centimeters> for Meters {
    type Output = Meters;

    fn add(self, rhs: Centimeters) -> Meters {
        // Convert centimeters to meters and add
        Meters(self.0 + (rhs.0 / 100.0))
    }
}

fn main() {
    let length = Meters(5.0);
    let extra  = Centimeters(250.0);

    // Adds Meters + Centimeters cleanly!
    let total = length + extra; 

    println!("Total meters: {:?}", total); // Output: Meters(7.5)
}
```

---

## Question 2: What is the exhaustive list of overloadable operators in Rust?

### Question
Is the list of overloadable operators exhaustive, or which operators can be overloaded? Are there any operators that cannot be overloaded?

---

### Answer
All mathematical, bitwise, indexing, and comparison operators in Rust map to traits in `std::ops` or `std::cmp`. Here is the **complete list of all overloadable operators in Rust**:

#### 1. Arithmetic & Bitwise (`std::ops`)
* **Binary Arithmetic:** `+` (`Add`), `-` (`Sub`), `*` (`Mul`), `/` (`Div`), `%` (`Rem`)
* **Unary Operators:** `-x` (`Neg`), `!x` (`Not`)
* **Bitwise Operators:** `&` (`BitAnd`), `|` (`BitOr`), `^` (`BitXor`), `<<` (`Shl`), `>>` (`Shr`)

#### 2. Compound Assignments (`std::ops`)
* `+=` (`AddAssign`), `-=` (`SubAssign`), `*=` (`MulAssign`), `/=` (`DivAssign`), `%=` (`RemAssign`)
* `&=` (`BitAndAssign`), `|=` (`BitOrAssign`), `^=` (`BitXorAssign`), `<<=` (`ShlAssign`), `>>=` (`ShrAssign`)

#### 3. Indexing & Dereferencing (`std::ops`)
* **Array/Map Indexing:** `container[key]` (`Index` for immutable reads, `IndexMut` for mutable writes)
* **Pointer Dereferencing:** `*ptr` (`Deref` and `DerefMut`)

#### 4. Comparisons (`std::cmp`)
* **Equality:** `==`, `!=` (`PartialEq`, `Eq`)
* **Ordering:** `<`, `>`, `<=`, `>=` (`PartialOrd`, `Ord`)

#### What operators CANNOT be overloaded? ❌
* **Logical Short-Circuiting (`&&`, `||`):** Forbidden because overloading them would destroy Rust's short-circuit evaluation guarantees.
* **Assignment (`=`):** Standard variable assignment and moving cannot be overridden.
* **Range Operators (`..`, `..=`):** These are built-in syntax for creating `Range` structs.

---

## Question 3: Can we invent brand new custom operators (like `operator$()`)?

### Question
Can we create our own custom symbolic operator that does not even exist in normal grammar—let's say `operator$()`?

---

### Answer
**No, you cannot invent brand new symbolic operators like `a $ b` or `a <+> b` in normal Rust syntax.**

Languages like Swift, Scala, or Haskell allow developers to invent custom symbolic operators. Rust explicitly forbids this by design. 

#### Why does Rust forbid inventing operators?
Rust prioritizes **code readability and deterministic parsing**. If libraries were allowed to invent custom symbolic syntax like `a @! b` or `x #$~ y`, large codebases would turn into unreadable "symbol soup" where developers would have no idea what precedence or meaning a symbol has without memorizing library internals.

---

#### The Escape Hatch: Macros (`macro_rules!`) ⭐

If you *really* need custom symbolic syntax for a domain-specific language (DSL)—such as mathematical formulas, hardware register manipulation, or query languages—Rust lets you invent custom operators **inside macros**!

For example, here is how you can invent a custom `$` operator using a macro:

```rust
macro_rules! calculate {
    // We invent custom syntax where two expressions are separated by `$`
    ($left:expr , $right:expr) => {
        // Define what the `$` operator actually does:
        ($left * 2) + ($right * 3)
    };
}

fn main() {
    // Inside the macro call, we can use our invented syntax!
    let result = calculate!(10 , 5); // (10 * 2) + (5 * 3) = 35
    
    println!("Custom operator result: {}", result);
}
```

#### Summary
* **Overloading Existing Operators:** Yes, you can implement almost any standard operator (`+`, `*`, `[]`, `==`) for your custom types.
* **Inventing New Operators (`$`):** Not in standard code (to keep syntax readable), but **yes** if you write a custom macro!
