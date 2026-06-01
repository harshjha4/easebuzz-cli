# Easebuzz CLI

A powerful, developer-first command-line interface for testing, integrating, and simulating transactions with the Easebuzz Payment Gateway. 

Built for speed and precision, the Easebuzz CLI allows merchants and QA engineers to execute manual checkouts, simulate high-load bulk transactions, verify payment statuses, and debug S2S (Server-to-Server) seamless flows without writing a single line of API boilerplate.

---

## Features

* **Zero Dependency Installation:** Distributed as a standalone compiled binary. No Python, `pip`, or virtual environments required.
* **Interactive Terminal UI:** Built with `Typer` and `Rich` to provide beautiful tables, secure password prompts (for CVVs), and color-coded diagnostic data.
* **Dynamic Payload Engine:** Supports passing massive lists of optional Easebuzz fields (like `udf1`, `city`, `zipcode`) on the fly via CLI flags or interactive terminal wizards.
* **Asynchronous Bulk Testing:** Fire off 10, 50, or 100+ concurrent, highly randomized transactions using `Faker` to load-test your webhooks and database parsers.
* **Seamless S2S Support:** Native, two-step state machine orchestration for handling Credit Cards, UPI, NetBanking, and EMI seamlessly from the terminal.
* **Multi-Environment Aware:** Instantly switch between `sandbox`, `dev`, and `production` routing.

---

## Installation

### macOS & Linux
Install the CLI globally in seconds using our self-bootstrapping script.
```bash
curl -fsSL [https://raw.githubusercontent.com/harshjha4/easebuzz-cli/main/install.sh](https://raw.githubusercontent.com/harshjha4/easebuzz-cli/main/install.sh) | bash

```

### Windows

Open **PowerShell** and execute the native installer:

```powershell
Invoke-Expression (New-Object System.Net.WebClient).DownloadString('[https://raw.githubusercontent.com/harshjha4/easebuzz-cli/main/install.ps1](https://raw.githubusercontent.com/harshjha4/easebuzz-cli/main/install.ps1)')

```

*(Note: Restart your terminal after installation on Windows).*

---

## Configuration

Before making API calls, configure the CLI with your Easebuzz Merchant Credentials. The CLI securely saves these in a local `~/.easebuzz/config.json` file.

```bash
easebuzz configure

```

You will be prompted to enter your:

* **Merchant Key**
* **Merchant Salt**
* **Environment** (`sandbox` or `production`)

---

## Usage & Commands

### 1. Initiate Standard Payment

Generate a standard checkout link. You can pass fields directly or use the interactive flag `-i` to trigger the optional fields wizard.

```bash
easebuzz payment initiate --amount 500.00 --name "John Doe" --email "john@test.com" --phone "9999999999"

# Trigger interactive wizard for UDFs and Address fields
easebuzz payment initiate --amount 199.00 -i

```

### 2. Seamless Payment (S2S)

Bypass the Easebuzz UI and process raw payment instruments directly. The CLI securely masks sensitive inputs like CVVs.

```bash
# Initiate a Seamless Credit Card Transaction
easebuzz payment seamless --amount 1500.00 --mode CC

# Initiate a Seamless UPI Transaction
easebuzz payment seamless --amount 10.00 --mode UPI

```

### 3. Bulk Load Testing (Chaos Engine)

Simulate high-load concurrency. The CLI uses `Faker` to generate highly randomized user data, injects optional chaos (like random cities or UDF tracking), and executes workers in parallel.

```bash
# Dispatch 50 random test transactions
easebuzz payment bulk --count 50 --amount 100.00

# Dispatch 20 transactions, strictly tagged with a specific UDF for your webhooks
easebuzz payment bulk --count 20 --amount 49.00 --udf1 "Q3_Webhook_LoadTest"

```

### 4. Check Transaction Status

Query the Easebuzz database to verify the exact status of a specific transaction without logging into the merchant dashboard.

```bash
easebuzz payment status --txnid "TXN123456789" --amount 500.00 --email "john@test.com" --phone "9999999999"

```

---

## Development & Building from Source

If you wish to contribute or compile the binaries yourself, you will need Python 3 installed.

1. **Clone the repository:**
```bash
git clone [https://github.com/harshjha4/easebuzz-cli.git](https://github.com/harshjha4/easebuzz-cli.git)
cd easebuzz-cli

```


2. **Install dependencies:**
```bash
pip install -r requirements.txt

```


3. **Run from source:**
```bash
python main.py --help

```



### Compiling Binaries (PyInstaller)

To compile a zero-dependency executable for your current operating system, run:

```bash
pyinstaller --onefile --clean --name easebuzz-cli --hidden-import dynaconf --hidden-import faker main.py

```

Your compiled executable will be available in the `dist/` folder.

---

## License

This project is for integration testing and development purposes. Please refer to the official [Easebuzz API Documentation](https://docs.easebuzz.in/) for strict production PCI-DSS compliance guidelines regarding Server-to-Server payment handling.