set positional-arguments

patch +FONTS:
  #!/usr/bin/env zsh
  for FILE in "$@"
  do
    ./patch.ff $FILE "$HOME/Library/Fonts/nonicons.ttf" "$HOME/Library/Fonts/SymbolsNerdFont-Regular.ttf"
  done

download:
  test -d "$HOME/Library/Fonts"
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ya2s/nonicons/raw/refs/heads/master/dist/nonicons.ttf"
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ryanoasis/nerd-fonts/raw/refs/heads/master/patched-fonts/NerdFontsSymbolsOnly/SymbolsNerdFont-Regular.ttf"
