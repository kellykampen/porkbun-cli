# Setting Up Porkbun CLI

This guide provides detailed instructions for setting up and configuring the Porkbun CLI tool.

## System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- Porkbun account with API access enabled

## Installation Methods

### Method 1: Using Virtual Environment (Recommended)

This method isolates the Porkbun CLI dependencies from your system Python packages.

```bash
# Clone the repository
git clone https://github.com/ragelink/porkbun-cli.git
cd porkbun-cli

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install a regular package that keeps working if the checkout moves
python -m pip install .

# Verify the installed launcher without making API calls
porkbun --help
```

Contributors can use `python -m pip install -e .` for an editable install.
Editable installs depend on the checkout's absolute path. After moving a checkout,
reinstall it with the same Python interpreter that owns the launcher:

```bash
/path/to/python -m pip install --force-reinstall --no-deps /new/path/to/porkbun-cli
```

This regular install copies the package into that interpreter's site-packages and
regenerates `porkbun` to call `porkbun.cli:cli`. Add `-e` if you still need editable
development. Reinstalling the package does not change saved API credentials.

To deactivate the virtual environment when you're done:

```bash
deactivate
```

### Method 2: Docker Installation

Using Docker avoids installing Python and dependencies directly on your system.

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/ragelink/porkbun-cli.git
cd porkbun-cli

# Build the Docker image
docker build -t porkbun-cli .

# Run a command using the Docker container
docker run -v ~/.porkbun:/root/.porkbun porkbun-cli config list
```

The volume mount (`-v ~/.porkbun:/root/.porkbun`) ensures your configuration persists between container runs.

## API Access Setup

Before using the CLI, you need to obtain API credentials from Porkbun:

1. Log in to your Porkbun account at [https://porkbun.com/account/login](https://porkbun.com/account/login)
2. Navigate to "Account" → "API Access"
3. Click "Create API Key"
4. Save both the API key and Secret key securely
5. For each domain you want to manage:
   - Go to the domain management page
   - Enable "API Access" for that domain
   - This step is crucial; the API won't work for domains without this enabled

## CLI Configuration

The CLI supports multiple profiles, allowing you to manage different API keys (e.g., for different Porkbun accounts).

### Adding a Profile

```bash
# Activate your virtual environment if using Method 1
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Add a new profile (default)
python -m porkbun.cli config add default --api-key YOUR_API_KEY --secret-key YOUR_SECRET_KEY --make-default

# Add additional profiles (optional)
python -m porkbun.cli config add work --api-key WORK_API_KEY --secret-key WORK_SECRET_KEY
```

### Managing Profiles

```bash
# List all configured profiles
python -m porkbun.cli config list

# Switch to a different profile
python -m porkbun.cli config use work

# Remove a profile
python -m porkbun.cli config remove profile_name
```

## Verifying Installation

To verify that the CLI is properly installed and configured:

```bash
# Test API connectivity
python -m porkbun.cli account ping

# If configured correctly, you should see a success message with your IP address
```

## Using with Shell Aliases (Optional)

For convenience, you can set up a shell alias to avoid typing the full command:

### Bash/Zsh

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias porkbun='python -m porkbun.cli'
```

Then reload your shell:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

Now you can use shortened commands:

```bash
porkbun domains list-all
```

## Upgrading

To update to the latest version:

```bash
# Navigate to your porkbun-cli directory
cd /path/to/porkbun-cli

# Pull the latest changes
git pull

# Activate your virtual environment (if using Method 1)
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Reinstall in development mode (if needed)
pip install -e .
```

## Troubleshooting

### Common Installation Issues

1. **Python Version Error**:
   - Error: `Python 3.8 or higher is required`
   - Solution: Install a newer version of Python

2. **Dependency Conflicts**:
   - Error: `Package 'X' conflicts with 'Y'`
   - Solution: Use a virtual environment to isolate dependencies

3. **Permission Denied**:
   - Error: `Permission denied` when running pip install
   - Solution: Add `--user` flag to pip command or use a virtual environment

### API Connection Issues

1. **Authentication Errors**:
   - Error: `Authentication failed`
   - Solution: Verify your API keys are correct in the configuration

2. **Domain Not Found**:
   - Error: `Domain not found` or `Not authorized for domain`
   - Solution: Ensure API access is enabled for the specific domain in your Porkbun account

3. **API Rate Limiting**:
   - Error: `Too many requests`
   - Solution: Wait a few minutes before trying again

## Next Steps

- Browse the [User Guide](user-guide/index.md) for detailed usage instructions
- Check the [Command Reference](api/commands.md) for all available commands
- Review [Examples](examples/index.md) for common use cases

## Developer Notes

### Next Session Tasks

#### DNS Async Operation Fix

The DNS retrieve command currently has an issue with asynchronous operations not being properly awaited. To fix:

1. Open `porkbun/commands/dns.py`
2. Focus on the `retrieve` and `retrieve_records` functions
3. Import the `asyncio` module at the top of the file
4. Wrap the `make_request` calls with `asyncio.run()` to properly handle the coroutines
5. This should fix the "coroutine was never awaited" warning

#### Domain API Access Error Handling

When a domain is not opted in to API access, the error message is not very helpful. To improve:

1. Add try/except blocks in the DNS functions to catch the specific 400 error
2. When catching the "Domain is not opted in to API access" error, provide a clear message
3. Include instructions on how to enable API access in the Porkbun dashboard
4. Consider adding a `check_domain_api_access` helper function in the API module

#### Testing Strategy

1. Test the DNS retrieve command with `ragelink.com` first (has API access issue)
2. Test with a domain that has API access enabled
3. Verify both the async fix and the improved error messages

#### Code Improvement Opportunities

1. Look for other async functions in the codebase that might have similar issues
2. Enhance table formatting for DNS record output
3. Add colorized output for error messages
4. Consider adding batch operations for DNS records
