Adds [nonicons](https://github.com/ya2s/nonicons) and [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) symbols to `.ttf` and `.otf` fonts.

## Requirements

Install `just` and `uv`.

## Usage

```bash
# Download the symbol fonts to ~/Library/Fonts
just download_symbols

# Patch one or more fonts
just patch ~/Library/Fonts/JetBrainsMono-Regular.ttf ~/Library/Fonts/TX-02-Variable.otf
```

Each patched copy is saved beside its original with a `-Symbols` filename suffix.
Select the font with **Symbols** in its family name in your app, such as **JetBrains Mono Symbols**.

Variable OTF fonts retain their weight, width, and other controls.
Variable TTF fonts become static fonts at their default settings.

## Example of Patched Font

<img width="589" height="539" src="https://github.com/user-attachments/assets/d6b64110-e963-4c43-a515-fa94e11d736a" />
