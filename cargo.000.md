# Guide to Working Offline with Rust and Cargo

By default, the Rust package manager (`cargo`) relies on an active internet connection to download crates from the central registry (crates.io) and update its index. However, Cargo provides robust mechanisms to work completely offline, minimize network requests, or establish an entirely air-gapped development environment.

This guide outlines the three primary strategies for running `cargo build` without an internet connection, followed by instructions on setting up a **Global Vendor Directory** to share local dependencies across multiple distinct projects.


## 1. Quick-Start Offline Strategies

Before setting up a global sharing mechanism, you can use these three built-in Cargo commands depending on your immediate network scenario:

### Strategy A: The `--offline` Flag
If you have already built your project at least once while connected to the internet, Cargo caches all necessary crates locally. You can enforce offline mode by appending the `--offline` flag:

```bash
cargo build --offline

```

* **Mechanism:** Forces Cargo to ignore the crates.io index and use only the crates stored in your machine's local cache (`~/.cargo/`).
* **Limitation:** If you add a new dependency or version requirement to `Cargo.toml` that hasn't been cached yet, the build will fail.

### Strategy B: Pre-fetching with `cargo fetch`

If you are currently online but anticipate going offline soon (e.g., boarding a flight), you can pre-load your workspace dependencies:

```bash
cargo fetch

```

* **Mechanism:** Reads your `Cargo.lock` file and downloads all specified dependencies into your local cache without initiating compilation. Once completed, you can run `cargo build --offline` at any point.

### Strategy C: Local Project Vendoring with `cargo vendor`

To make an individual project completely self-contained and portable (e.g., to transfer via a USB drive to a secure computer):

1. **Download dependencies into the project root:**
```bash
cargo vendor

```


2. **Configure the local project:**
The command will generate a snippet. Copy and paste it into `.cargo/config.toml` inside your project folder:
```toml
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"

```



---

## 2. Setting Up a Shared Global Vendor Directory

If you want to prevent *every* new project from reaching out to the internet, you can maintain a single, shared directory on your system where Cargo will look for crate source code.

### Step 1: Create the Shared Folder

Choose an appropriate, permanent location on your file system to act as your local mirror:

```bash
# On Linux / macOS
mkdir -p ~/.cargo/global-vendor

# On Windows (PowerShell)
New-Item -ItemType Directory -Path "$HOME\\.cargo\\global-vendor"

```

### Step 2: Populate the Global Mirror

`cargo vendor` operates within the context of a project. To populate or update your global folder, navigate to any project containing the dependencies you want to store and specify the target path:

```bash
# From within a project directory:
cargo vendor ~/.cargo/global-vendor

```

*Note: If you run this across multiple projects over time, Cargo will automatically merge the new dependencies and versions into this central directory without overwriting existing ones.*

### Step 3: Apply Global Configuration

To instruct Cargo to check your global folder before attempting to resolve crates online, you must edit your global configuration file.

Open or create `~/.cargo/config.toml` (or `C:\\Users\\<Username>\\.cargo\\config.toml` on Windows) and append the source replacement configuration:

```toml
[source.crates-io]
replace-with = "global-vendored-sources"

[source.global-vendored-sources]
# CRITICAL: Use the full absolute path. Cargo does not resolve '~' or '$HOME' here.
directory = "/home/your_username/.cargo/global-vendor"

```

*(Replace `/home/your_username/.cargo/global-vendor` with your actual absolute path, e.g., `C:/Users/YourName/.cargo/global-vendor` on Windows).*

---

## 3. Crucial Caveats & Workflow for Global Offline Environments

While the global vendor setup resolves crate compilation, Cargo's dependency resolution engine has strict requirements regarding the **Crates.io Index** (the manifest list of every crate version in existence). To use your global mirror seamlessly offline, adapt your workflow to these constraints:

### Explicit Version Tagging

When creating or editing a new project while completely offline, Cargo cannot query crates.io to determine the latest semantic version. You must explicitly reference a version string that exists within your global vendor directory.

Instead of running an implicit command like `cargo add serde`, manually declare the dependency in your local `Cargo.toml`:

```toml
[dependencies]
# This exact version string must exist inside your global-vendor folder
serde = { version = "1.0.152" } 

```

### Enforcing the Offline Flag

Even with source replacement configured, a routine `cargo build` on a new project may try to connect to the internet to sync the registry index metadata. Always combine your local development commands with the offline flag:

```bash
cargo build --offline
cargo test --offline
cargo run --offline

```

By supplying the absolute path in your global configuration and enforcing `--offline`, Cargo will satisfy all dependency graphs straight from your local filesystem.
"""
