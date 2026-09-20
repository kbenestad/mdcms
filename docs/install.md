# Setting up MD-CMS for your site
This document walks you through the installation of MD-CMS.

## Minimum install
The bare minimum required to run MD-CMS is to download the content in [**app/**](https://github.com/kbenestad/mdcms/tree/main/app) and upload the files and folders to any web-server.

## Recommended install
To properly use MD-CMS you need to download the CLI tool. 

### Linux
To download MD-CMS for Linux, you need to run the appropriate command below in the terminal. Verify which version you have installed by running `mdcms --version`.

Binaries are provided for both **amd64** (regular 64-bit PCs and servers) and **arm64** (64-bit ARM, including Raspberry Pi 3/4/5 running a 64-bit OS). Run `uname -m` if unsure: `x86_64` → amd64, `aarch64` → arm64.

#### Debian and Debian-based distros (including Ubuntu and Raspberry Pi OS)
The .deb package handles all installation details. To download and install, run:

**amd64:**
```
curl -fsSLO https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/amd64/mdcms.deb && sudo dpkg -i mdcms.deb
```

**arm64 (Raspberry Pi):**
```
curl -fsSLO https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/arm64/mdcms.deb && sudo dpkg -i mdcms.deb
```

#### All other Linux distros
For all other Linux distros, please run the following command in the terminal:

**amd64:**
```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/amd64/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
```

**arm64 (Raspberry Pi):**
```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/arm64/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
```

This command fetches the latest binary, moves it to `/usr/local/bin/mdcms` and makes it executable in one go.

### MacOS
Open terminal and run the command matching your Mac. Apple Silicon Macs (M1 and later) use the **silicon** build; older Intel Macs use the **intel** build. If unsure, click the Apple menu → About This Mac and check the chip/processor.

**Apple Silicon:**
```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/macos/silicon/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
```

**Intel:**
```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/macos/intel/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
```

MacOS may block the binary on first run ("cannot be opened because the developer cannot be verified"). If so, run the following command:
```
sudo xattr -d com.apple.quarantine /usr/local/bin/mdcms
```
once to clear it. Verify which version you have installed by running `mdcms --version`.

### Windows

In Windows 10 or 11, open PowerShell and run the following command:

```
Invoke-WebRequest https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/windows/mdcms.exe -OutFile "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\mdcms.exe"
```

Verify which version you have installed by running `mdcms --version`.

## Update

MD-CMS consists of two separate pieces of software: The CLI tool (which you run from the terminal) and the renderer (the index.html file, which the browser reads). To update the CLI, simply rerun the installation command and overwrite `mdcms`. To update the renderer, download the latest index.html and overwrite it in your sites.

## Tab completion

Tab completion is set up for you. The first time you run any `mdcms` command after installing, it switches itself on and says so:

```
Tab completion installed for zsh (added one line to /home/you/.zshrc).
Press Tab after `mdcms ` in a new terminal window to use it.
```

Open a new terminal window and Tab works:

```
mdcms bu<Tab>              →  mdcms build      (or bundle — it shows both)
mdcms build mys<Tab>       →  mdcms build mysite
```

Pressing Tab only fills in text. Nothing runs until you press Enter, exactly as when you Tab-complete a filename. Site names come from your registry, so a new site can be completed the moment you `mdcms register` it.

bash, zsh, and fish are supported. On bash and zsh, mdcms saves a completion script to `~/.config/mdcms/` and adds one line to `~/.bashrc` or `~/.zshrc` that loads it. On fish it writes `~/.config/fish/completions/mdcms.fish`, which fish picks up by itself.

**If you would rather it did not**, set `MDCMS_NO_COMPLETION=1` in your environment before the first run, and mdcms will leave your shell alone. To remove completion after the fact, delete the script file and the line it added; mdcms will not put them back. Nothing is set up when mdcms is not run from a terminal, so CI/CD pipelines and scripts are unaffected.

`mdcms completion` re-runs the setup by hand — useful to put completion back after removing it, or to set it up for a second shell (`mdcms completion fish`).

Two things worth knowing:

- Completion attaches to the installed `mdcms` command. If you run the tool as `python3 mdcms.py` from a checkout, Tab completion does not apply to it.
- Every Tab press runs `mdcms` once to ask it what to offer. With the standalone binary on a slow machine (a Raspberry Pi, say) that can take a noticeable fraction of a second.

## Building your own binary

The commands above download a pre-built binary from the latest GitHub release. If you want to build one yourself instead — from a local checkout, a branch that hasn't been released yet, or a modified copy of `mdcms.py` — you can produce the exact same kind of standalone executable with [PyInstaller](https://pyinstaller.org/), the same tool the release workflow (`.github/workflows/release.yml`) uses.

### Build

PyInstaller needs to run from a normal Python environment, but on most current Linux distros `pip install` refuses to touch the system Python directly (`externally-managed-environment`). A virtual environment sidesteps that safely — it only affects the build, not the resulting binary:

```
python3 -m venv mdcms-build-venv
source mdcms-build-venv/bin/activate       # Windows: mdcms-build-venv\Scripts\activate
pip install pyinstaller click pyyaml certifi
pyinstaller --onefile --name mdcms --collect-data certifi mdcms.py
```

Run this from the directory containing `mdcms.py`. `--collect-data certifi` is required — it bundles certifi's CA bundle into the binary so HTTPS calls (template downloads, theme fetches, `mdcms update`, etc.) work without depending on the system's CA store. Skipping it is the most common way a self-built binary breaks.

The finished binary lands at `dist/mdcms` (`dist/mdcms.exe` on Windows). You can `deactivate` and delete the venv afterwards — the binary itself doesn't need Python or the venv to run.

### Running it without installing

The binary in `dist/` is fully standalone; you don't have to move it anywhere or make it an "installed" command to use it. From the directory containing it:

```
./dist/mdcms --help
./dist/mdcms build --path ./my-site
```

or from anywhere else, by pointing at it with a relative or full path:

```
/full/path/to/dist/mdcms --help
```

This is also the safest way to try a freshly built binary if you already have `mdcms` installed some other way (pip, pipx, or a downloaded release binary) — running `mdcms` bare resolves to whatever comes first on your `PATH`, which is very likely the existing install, not the one you just built. Run `which -a mdcms` to see every `mdcms` your shell can find, in the order it would try them, if you're not sure which one a bare `mdcms` would run.

Only copy the binary onto your `PATH` (e.g. `cp dist/mdcms ~/.local/bin/mdcms`, or `/usr/local/bin/mdcms` as in the install commands above) once you're sure it's the one you want to keep using as your default `mdcms`.