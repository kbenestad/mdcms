# MD-CMS

Write your content as `.md` files, run one command, and deploy to any static host. All rendering happens in the browser at runtime.

With the GitHub Actions workflow, you can automatically rebuild the navigation structure and search index on each commit.

- - -
## How it works

MD-CMS has two parts:

The web app:

- `index.html` — a single-file browser renderer. It reads your markdown, config,
  and nav at runtime and renders everything client-side. No compilation, no
  framework.
- `config.yml` — contains site configuration.
- `nav.yml` — navigation tree.
- `search.json` — supports site-wide search on static host.

The local app: `mdcms` — a CLI tool that scans your content, generates `nav.yml`
and `search.json`, and can wire up automatic builds via GitHub Actions.

## Installation

**Standalone binary**

1.  Download from the 
    [latest release](https://github.com/kbenestad/mdcms/releases/latest).
2.  Move the binary and make it executable
	- Linux
		- Download the [latest mdcms](latest/linux/mdcms)
		- Move it to `/usr/local/bin/`: `sudo mv mdcms /usr/local/bin/mdcms`
		- Make it executable: `sudo chmod +x /usr/local/bin/mdcms`
	- Mac
		- Download the [latest mdcms](latest/macos/mdcms)
		- Move it to `/usr/local/bin/`: `sudo mv mdcms /usr/local/bin/mdcms`
		- Make it executable: `sudo chmod +x /usr/local/bin/mdcms`
		- Remove the quarantine flag: `xattr -dr com.apple.quarantine /usr/local/bin/mdcms`
	- Windows
		- Download the [latest mdcms](latest/windows/mdcms.exe)
		- Move it to a permanent folder, e.g. `C:\tools\mdcms.exe`
		- Add `C:\tools\` to your PATH: Start → search `"Environment Variables"` → edit the `Path user variable` → add `C:\tools\`
		- Open a new PowerShell window and verify: `mdcms --version`

## Use
To get started, run `mdcms register mysite` to register the current working directory as the `mysite` MD-CMS project directory. You can also specify the project path: `mdcms register mysite /path/to/mysiteNote`.

If there is an existing MD-CMS instance in your specified directory, the app will register this site; if there is no MD-CMS instance present, it will download the latest version from the GitHub repo.

Add your pages, posts, and assets. Once you're ready to upload your site, run `mdcms build mysite` to update `nav.yml` and `search.json`. You can also run `mdcms build --path` to build the website without registering the site.

The final project directory can be uploaded to a static host of your choice.

## File structure
```
[project directory]/
	index.html			← renderer
	config.yml			← site configuration and theme
	nav.yml				← navigation structure
	search.json			← search index
	
	pages/				← Put your permanent pages here
		home.md			← Main page
		...						

	posts/				← Put your time-bound posts here
		...						

	assets/				← Holds directories for non-content files
		required/		← Logo, favicon, and icons go here.
			...

		images/			← Images
			...

		fonts/			← Fonts referenced in config.yml
			...

		files/			← Files for download
			...
```

**IMPORTANT:** All links are read from `index.html` in the root. Therefore, you must provide full paths for each file from the root.

Example: You want to put a link to `page2.md` in `home.md`. `page2.md` is in the same directory as `home.md`.

The correct link is therefore:
```
[Link text](pages/page2.md)
```

This does not link to `page2.md`:
```
[Link text](page2.md)
```

## Further reading

For further documentation, refer to:
	
- [docs/](docs/README.md): Documentation relevant to this repo
- [docs.benestad.net](https://docs.benestad.net/): Further help -- including an example of an MD-CMS site.

## Licence
This software is © 2026 Kristian Benestad. Licensed under the [Apache License, Version 2.0](LICENSE).
