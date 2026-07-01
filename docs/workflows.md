# Setting up MD-CMS for your site
This document walks you through the installation of MD-CMS.

## Minimum install
The bare minimum required to run MD-CMS is to download the content in [**app/**](https://github.com/kbenestad/mdcms/tree/main/app) and upload the files and folders to any web-server.

## Recommended install
To properly use MD-CMS you need to download the CLI tool. 

### Linux
To download MD-CMS for Linux, you need to run the appropriate command below in the terminal. Verify which version you have installed by running `mdcms --version`.

#### Debian and Debian-based distros (including Ubuntu)
The .deb package handles all installation details. To download and install, run:
```
curl -fsSLO https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/mdcms.deb && sudo dpkg -i mdcms.deb
```

#### All other Linux distros
For all other Linux distros, please run the following command in the terminal:
```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/linux/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
```

This command fetches the latest binary, moves it to `/usr/local/bin/mdcms` and makes it executable in one go.

### MacOS
Open terminal and run this command to install `mdcms`:

```
sudo curl -fsSL https://raw.githubusercontent.com/kbenestad/mdcms/main/latest/macos/mdcms -o /usr/local/bin/mdcms && sudo chmod +x /usr/local/bin/mdcms
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