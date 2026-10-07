# Installing conda (first-time setup)

Only needed if `conda --version` doesn't work in your terminal. If it prints a version, skip this
and go back to [README.md](README.md).

We use **Miniconda**: a small conda installer (~100 MB) without the hundreds of extra packages that
come with full Anaconda. Install it once; it works for every Python project afterwards.

Don't want conda at all? Skip to [No conda: use a venv](#no-conda-use-a-venv) at the bottom.

## macOS

Open **Terminal** (Cmd+Space, type "Terminal").

**With Homebrew** (if `brew --version` works):

```bash
brew install --cask miniconda
conda init zsh
```

**Without Homebrew:** pick the line for your Mac (Apple menu → About This Mac: "Apple M1/M2/M3/M4"
means Apple Silicon, "Intel" means Intel):

```bash
# Apple Silicon
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# Intel
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh
bash Miniconda3-latest-MacOSX-x86_64.sh
```

Press Enter to scroll the license, type `yes` to accept, press Enter to keep the default location
(`~/miniconda3`), and answer `yes` when asked to initialize conda.

**Close the terminal and open a new one**, then check: `conda --version`.

## Linux

```bash
# x86_64 (most laptops/desktops)
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# ARM (e.g. Raspberry Pi 4/5 64-bit, ARM laptops); check with `uname -m`
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh
```

Accept the license, keep the default location, answer `yes` to initialize. Open a new terminal and
check: `conda --version`.

## Windows

Either:

- **winget** (PowerShell): `winget install -e --id Anaconda.Miniconda3`, or
- download the Windows installer from <https://www.anaconda.com/download/success> (scroll to
  **Miniconda Installers**) and run it with the defaults ("Just Me" is fine).

Then open **Anaconda Prompt (miniconda3)** from the Start menu and check: `conda --version`.
Use Anaconda Prompt for all the commands in this repo. (To use PowerShell instead, run
`conda init powershell` once in Anaconda Prompt, then open a new PowerShell.)

## Create the duck environment

From the repo root (`brown-duck/`):

```bash
conda env create -f sim/environment.yml
conda activate brown-duck
```

Your prompt should now start with `(brown-duck)`. Run the sim:

- macOS: `mjpython sim/teleop.py`
- Linux: `python sim/teleop.py`
- Windows: `python sim\teleop.py`

Back in [README.md](README.md) you'll find the controls and troubleshooting.

## Problems installing conda

- **`conda: command not found` after installing.** You didn't open a new terminal, or the init step
  was skipped. Run `~/miniconda3/bin/conda init zsh` (macOS) or `~/miniconda3/bin/conda init bash`
  (Linux), then open a new terminal.
- **`CondaToSNonInteractiveError` / "Terms of Service have not been accepted".** Newer Miniconda asks
  you to accept Anaconda's channel terms once. Run the `conda tos accept ...` commands it prints,
  then retry `conda env create`.
- **Windows: `conda` not recognized in PowerShell or cmd.** Use **Anaconda Prompt**, or run
  `conda init powershell` from Anaconda Prompt and reopen PowerShell.
- **I don't want `(base)` in every terminal.** `conda config --set auto_activate_base false`.

## No conda: use a venv

conda isn't required. Python's built-in `venv` works too, you just need **Python 3.10 to 3.14**
(3.12 recommended) installed yourself:

| OS | Install Python 3.12 |
|---|---|
| macOS | `brew install python@3.12`, or the installer from <https://www.python.org/downloads/> |
| Linux (Ubuntu/Debian) | `sudo apt install python3 python3-venv python3-pip` (check `python3 --version` is ≥ 3.10) |
| Windows | `winget install -e --id Python.Python.3.12`, or python.org (tick **Add python.exe to PATH**) |

Then follow **Option B: venv** in [README.md](README.md#option-b-venv).
