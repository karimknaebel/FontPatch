Patches arbitrary ttf fonts with the [nonicons](https://github.com/ya2s/nonicons) and [nerd-fonts](https://github.com/ryanoasis/nerd-fonts) symbol fonts.

## Usage

```bash
# first download symbol fonts to $HOME/Library/Fonts
just download

# then patch a list of fonts. they will be saved with a -Symbols file name suffix
just patch ~/Library/Fonts/JetBrainsMono-Regular.ttf ~/Library/Fonts/JetBrainsMono-Bold.ttf
```
