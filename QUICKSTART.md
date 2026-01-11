# Quick Start Guide

Get up and running with BaserowScripts in 3 easy steps.

## 1. Run Setup

### Linux / macOS
```bash
./setup.sh
```

### Windows
```batch
setup.bat
```

This will:
- Create a Python virtual environment in `venv/`
- Install all required dependencies
- Set up everything you need to run the scripts

## 2. Configure Your Credentials

Copy the example environment file and add your Baserow credentials:

```bash
cp .env.example .env
```

Edit `.env` with your favorite text editor:
```env
BASEROW_API_URL=https://api.baserow.io
BASEROW_API_TOKEN=your_actual_token_here
CONTACTS_TABLE_ID=12345
TABLE_ID=67890
```

### Getting Your API Token

1. Log into Baserow
2. Click your profile icon (top-right)
3. Go to Settings → API Tokens
4. Create a new token
5. Copy it to your `.env` file

### Finding Your Table ID

1. Open your table in Baserow
2. Look at the URL: `https://baserow.io/database/xxx/table/12345`
3. The number after `/table/` is your table ID

## 3. Run the Scripts

### Activate the Virtual Environment

**Linux / macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```batch
venv\Scripts\activate.bat
```

### Run Scripts

**Update Contacts (from Excel):**
```bash
python update_contacts.py --excel-file enrollment.xlsx --dry-run
```

**Deduplicate Table:**
```bash
python deduplicate_table.py --identifying-field Email --dry-run
```

### Or Use the Helper Scripts (Linux/macOS)

```bash
./run_update_contacts.sh --excel-file enrollment.xlsx --dry-run
./run_deduplicate.sh --identifying-field Email --dry-run
```

## Using with VSCode / VSCodium

The repository includes `.vscode/settings.json` which configures the Python interpreter to use the virtual environment.

**Steps:**
1. Open the repository folder in VSCode/VSCodium
2. Run `./setup.sh` (or `setup.bat` on Windows)
3. Reload VSCode/VSCodium
4. The correct Python interpreter (`venv/bin/python`) should now be selected
5. Open any Python file - imports should work without hanging

**If imports still hang:**
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Python: Select Interpreter"
3. Choose the one from `./venv/bin/python`
4. Reload the window

## Running Tests

To verify everything is working:

```bash
source venv/bin/activate  # or venv\Scripts\activate.bat on Windows
python test_update_contacts.py
```

You should see:
```
✓ ALL TESTS PASSED!
```

## Troubleshooting

### "python: command not found" or "python3: command not found"
Install Python 3.7 or higher from [python.org](https://www.python.org/downloads/)

### "ModuleNotFoundError: No module named 'requests'"
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat  # Windows
```

### Imports hanging in VSCode/VSCodium
1. Make sure `venv/` exists (run `./setup.sh`)
2. Select the correct interpreter (see "Using with VSCode/VSCodium" above)
3. Try reloading the window: `Ctrl+Shift+P` → "Reload Window"

### Permission denied on setup.sh
```bash
chmod +x setup.sh run_update_contacts.sh run_deduplicate.sh
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check the example `.env.example` for configuration options
- Review command-line options with `python update_contacts.py --help`

## Need Help?

Check the main [README.md](README.md) for:
- Detailed usage examples
- Complete API documentation
- Troubleshooting guides
- Common scenarios
