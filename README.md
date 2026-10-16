Patches arbitrary `ttf` and `otf` fonts with the [nonicons](https://github.com/ya2s/nonicons) and [nerd-fonts](https://github.com/ryanoasis/nerd-fonts) symbol fonts.

Variable OTF fonts retain their axes and named styles. Variable TTF fonts are
instantiated to their default axis values before patching.

Requires `just`, FontForge, FontTools (with CFF2 instancing support), and `uv`.
OTF fonts are patched with FontTools to preserve their existing outlines and layout
tables. Existing characters take priority, followed by nonicons, then Nerd Fonts
when their codepoints overlap.
For monospaced OTF fonts, added symbols keep a single-cell advance but may draw
up to two cells wide, allowing terminals to use adjacent whitespace for wide icons.

## Usage

```bash
# first download symbol fonts to $HOME/Library/Fonts
just download

# then patch a list of fonts. they will be saved with a -Symbols file name suffix
just patch ~/Library/Fonts/JetBrainsMono-Regular.ttf ~/Library/Fonts/JetBrainsMono-Bold.ttf
```

## Example of Patched Font

<img width="589" height="539" src="https://github.com/user-attachments/assets/d6b64110-e963-4c43-a515-fa94e11d736a" />
