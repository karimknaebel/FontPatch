#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path

from fontTools.ttLib import TTFont


DEFAULT_NAME_SLOTS = (
    (1, 0, 0),
    (3, 1, 0x409),
)


def first_name(font: TTFont, *name_ids: int) -> str:
    for name_id in name_ids:
        for record in font["name"].names:
            if record.nameID != name_id:
                continue
            value = record.toUnicode().strip()
            if value:
                return value
    return ""


def name_slots(font: TTFont, *name_ids: int) -> set[tuple[int, int, int]]:
    return {
        (record.platformID, record.platEncID, record.langID)
        for record in font["name"].names
        if record.nameID in name_ids
    }


def set_name(font: TTFont, source_font: TTFont, name_id: int, value: str, *fallback_ids: int) -> None:
    slots = (
        name_slots(font, name_id)
        or name_slots(source_font, name_id)
        or name_slots(font, *fallback_ids)
        or name_slots(source_font, *fallback_ids)
        or set(DEFAULT_NAME_SLOTS)
    )
    for platform_id, plat_enc_id, lang_id in slots:
        font["name"].setName(value, name_id, platform_id, plat_enc_id, lang_id)


def append_suffix(value: str, suffix: str) -> str:
    if not value or value.endswith(suffix):
        return value
    return value + suffix


def build_full_name(family_name: str, subfamily_name: str) -> str:
    return " ".join(part for part in (family_name, subfamily_name) if part)


def build_postscript_name(family_name: str, subfamily_name: str) -> str:
    family_component = re.sub(r"[^A-Za-z0-9_.-]", "", family_name.replace(" ", ""))
    subfamily_component = re.sub(r"[^A-Za-z0-9_.-]", "", subfamily_name.replace(" ", ""))
    if not subfamily_component:
        return family_component
    return family_component + "-" + subfamily_component


def rename_font(source_path: Path, output_path: Path) -> None:
    source_font = TTFont(source_path)
    output_font = TTFont(output_path)

    family_name = first_name(source_font, 1, 16) or source_path.stem
    subfamily_name = first_name(source_font, 2, 17) or "Regular"
    preferred_family_name = first_name(source_font, 16, 1) or family_name
    preferred_subfamily_name = first_name(source_font, 17, 2) or subfamily_name
    unique_id = first_name(source_font, 3)

    symbols_family_name = append_suffix(family_name, " Symbols")
    symbols_preferred_family_name = append_suffix(preferred_family_name, " Symbols")
    symbols_full_name = build_full_name(symbols_preferred_family_name, preferred_subfamily_name)
    symbols_postscript_name = build_postscript_name(symbols_preferred_family_name, preferred_subfamily_name)
    symbols_unique_id = append_suffix(unique_id or symbols_postscript_name, ";Symbols")

    set_name(output_font, source_font, 1, symbols_family_name, 1, 16)
    set_name(output_font, source_font, 2, subfamily_name, 2, 17)
    set_name(output_font, source_font, 3, symbols_unique_id, 3)
    set_name(output_font, source_font, 4, symbols_full_name, 4, 18)
    set_name(output_font, source_font, 6, symbols_postscript_name, 6)
    set_name(output_font, source_font, 16, symbols_preferred_family_name, 16, 1)
    set_name(output_font, source_font, 17, preferred_subfamily_name, 17, 2)
    set_name(output_font, source_font, 18, symbols_full_name, 18, 4)

    if "fvar" in output_font:
        set_name(output_font, source_font, 25, build_postscript_name(symbols_preferred_family_name, ""))
        for instance in output_font["fvar"].instances:
            if instance.postscriptNameID != 0xFFFF:
                set_name(
                    output_font, source_font, instance.postscriptNameID,
                    build_postscript_name(symbols_preferred_family_name, first_name(source_font, instance.subfamilyNameID)),
                )

    if "CFF " in output_font:
        cff = output_font["CFF "].cff
        cff.fontNames[0] = symbols_postscript_name
        top_dict = cff.topDictIndex[0]
        top_dict.FullName = symbols_full_name
        top_dict.FamilyName = symbols_preferred_family_name
        if preferred_subfamily_name:
            top_dict.Weight = preferred_subfamily_name
        if hasattr(top_dict, "FDArray"):
            for index, font_dict in enumerate(top_dict.FDArray):
                font_dict.FontName = f"{symbols_postscript_name}-FD{index}"

    output_font.save(output_path)
    output_font.close()
    source_font.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_font")
    parser.add_argument("output_font")
    args = parser.parse_args()
    rename_font(Path(args.source_font), Path(args.output_font))


if __name__ == "__main__":
    main()
