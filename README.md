# mirrordash-krisinformation

Swedish crisis and societal disruption information from Krisinformation.se.

This module retrieves active crisis announcements and alerts directly from the official Krisinformation API v3 and displays them inside a clean card.

## Features

- **County Filtering**: Filter announcements by standard Swedish counties (Län) via the built-in dropdown setting.

## Installation

On the mirror's admin page, open **Modules**: the module is in the list, install it with one click.
Or paste `git+https://github.com/Menturan/mirrordash-krisinformation.git` under **Modules → Install a Module from GitHub**.

Developing it: `uv run pytest` runs its tests, and `uvx mirrordash-sdk validate .` checks it.

## Configuration & API Keys

* **API Key Retrieval**: No API key is required. This module uses the public open data endpoint provided by Krisinformation.se.
* **Setup**: Open the MirrorDash Admin Dashboard, navigate to the **Modules** page, add `mirrordash_krisinformation`, and select your desired county filter.

## Screenshot

![Screenshot](screenshot.png)

## License
[PolyForm Noncommercial License 1.0.0](LICENSE.md)
