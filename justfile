set positional-arguments

patch +FONTS:
  #!/usr/bin/env zsh
  set -e
  temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/fontpatch.XXXXXX")
  trap 'rm -rf "$temp_dir"' EXIT

  for FILE in "$@"
  do
    case "${FILE:e:l}" in
      otf|ttf) ;;
      *) print -u2 "Unsupported font format: $FILE"; exit 1 ;;
    esac

    patch_output="${temp_dir}/${FILE:t:r}-Symbols.${FILE:e}"
    uv run "./patch_${FILE:e:l}.py" "$FILE" "$patch_output" \
      "$HOME/Library/Fonts/nonicons.ttf" "$HOME/Library/Fonts/SymbolsNerdFont-Regular.ttf"
    mv "$patch_output" "${FILE:r}-Symbols.${FILE:e}"
  done

test:
  #!/usr/bin/env zsh
  set -e
  requirements=$(mktemp "${TMPDIR:-/tmp}/fontpatch-test.XXXXXX")
  trap 'rm -f "$requirements"' EXIT

  for format in otf ttf
  do
    uv export --quiet --script "patch_${format}.py" --no-hashes > "$requirements"
    uv run --no-project --with-requirements "$requirements" python -m unittest "test_patch_${format}"
  done

download_symbols:
  test -d "$HOME/Library/Fonts"
  # Last tested with nonicons commit 42b614932a503f1bd4818bc72a2440c3b77a5c8e.
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ya2s/nonicons/raw/refs/heads/master/dist/nonicons.ttf"
  # Last tested with nerd-fonts commit 92a27e07169ff364c058699760c08c47baa67eb7.
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ryanoasis/nerd-fonts/raw/refs/heads/master/patched-fonts/NerdFontsSymbolsOnly/SymbolsNerdFont-Regular.ttf"
