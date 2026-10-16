set positional-arguments

patch +FONTS:
  #!/usr/bin/env zsh
  set -e
  fonttools_python=$(sed -n '1s/^#!//p' "$(command -v fonttools)")
  for FILE in "$@"
  do
    temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/fontpatch.XXXXXX")
    trap 'rm -rf "$temp_dir"' EXIT

    patch_input="${temp_dir}/${FILE:t}"
    patch_output="${patch_input:r}-Symbols.${patch_input:e}"
    final_output="${FILE:r}-Symbols.${FILE:e}"

    if [[ "${FILE:e:l}" == otf ]]; then
      uv run --no-cache --no-project --python "$fonttools_python" python ./patch_otf.py "$FILE" "$patch_output" \
        "$HOME/Library/Fonts/nonicons.ttf" "$HOME/Library/Fonts/SymbolsNerdFont-Regular.ttf"
      mv "$patch_output" "$final_output"
      rm -rf "$temp_dir"
      trap - EXIT
      continue
    fi

    cp "$HOME/Library/Fonts/nonicons.ttf" "${temp_dir}/nonicons.ttf"
    cp "$HOME/Library/Fonts/SymbolsNerdFont-Regular.ttf" "${temp_dir}/SymbolsNerdFont-Regular.ttf"

    if ttx -l "$FILE" | grep -qE '^[[:space:]]+fvar[[:space:]]'; then
      fonttools varLib.instancer --static --downgrade-cff2 -o "$patch_input" "$FILE"
    else
      cp "$FILE" "$patch_input"
    fi

    ./patch.ff "$patch_input" "${temp_dir}/nonicons.ttf" "${temp_dir}/SymbolsNerdFont-Regular.ttf"
    mv "$patch_output" "$final_output"
    uv run --no-cache --no-project --python "$fonttools_python" python ./rename_font.py "$FILE" "$final_output"

    rm -rf "$temp_dir"
    trap - EXIT
  done

download:
  test -d "$HOME/Library/Fonts"
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ya2s/nonicons/raw/refs/heads/master/dist/nonicons.ttf"
  wget -nc -P "$HOME/Library/Fonts" "https://github.com/ryanoasis/nerd-fonts/raw/refs/heads/master/patched-fonts/NerdFontsSymbolsOnly/SymbolsNerdFont-Regular.ttf"
