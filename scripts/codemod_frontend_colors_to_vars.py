#!/usr/bin/env python3

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


FRONTEND_DIR_DEFAULT = "frontend"
VARIABLES_CSS_DEFAULT = "frontend/static/css/variables.css"
EXCLUDE_SUBSTRINGS_DEFAULT = [os.sep + "static" + os.sep + "js" + os.sep + "dist" + os.sep]


HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGBA_RE = re.compile(r"rgba?\([^)]*\)")
HSLA_RE = re.compile(r"hsla?\([^)]*\)")

CSS_VAR_DECL_RE = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")
CSS_VAR_REF_RE = re.compile(r"var\(--([a-zA-Z0-9_-]+)\)")

CSS_DECL_LINE_RE = re.compile(r"^\s*([a-zA-Z-]+)\s*:\s*(.*?)\s*;\s*$")


@dataclass(frozen=True)
class ColorLiteral:
    kind: str  # hex|rgb|rgba|hsl|hsla
    normalized: str  # normalized string used for de-duping and matching


def _expand_hex3(hex3: str) -> str:
    # hex3 includes leading '#'
    h = hex3[1:]
    return "#" + "".join([c * 2 for c in h])


def normalize_hex(value: str) -> str:
    v = value.strip().lower()
    if len(v) == 4:  # #rgb
        v = _expand_hex3(v)
    return v


def normalize_paren_color(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def iter_color_literals(text: str) -> Iterable[str]:
    # Order matters a bit, but we collect all and dedupe later.
    for m in HEX_RE.findall(text):
        yield m
    for m in RGBA_RE.findall(text):
        yield m
    for m in HSLA_RE.findall(text):
        yield m


def classify_and_normalize(lit: str) -> ColorLiteral:
    s = lit.strip()
    if s.startswith("#"):
        return ColorLiteral(kind="hex", normalized=normalize_hex(s))
    s_lower = s.lower()
    if s_lower.startswith("rgba("):
        return ColorLiteral(kind="rgba", normalized=normalize_paren_color(s))
    if s_lower.startswith("rgb("):
        return ColorLiteral(kind="rgb", normalized=normalize_paren_color(s))
    if s_lower.startswith("hsla("):
        return ColorLiteral(kind="hsla", normalized=normalize_paren_color(s))
    if s_lower.startswith("hsl("):
        return ColorLiteral(kind="hsl", normalized=normalize_paren_color(s))
    return ColorLiteral(kind="unknown", normalized=s)


def build_existing_value_to_var_map(variables_css_text: str) -> Dict[str, str]:
    value_to_var: Dict[str, str] = {}
    for m in CSS_VAR_DECL_RE.finditer(variables_css_text):
        var_name = m.group(1)
        raw_value = m.group(2).strip()

        # Capture hex and functional colors; ignore other values (shadows, transitions, etc)
        for lit in iter_color_literals(raw_value):
            c = classify_and_normalize(lit)
            # Prefer the first variable we saw for a given value
            value_to_var.setdefault(c.normalized, var_name)

    return value_to_var


def build_semantic_alias_map(variables_css_text: str, semantic_prefix: str) -> Dict[str, str]:
    """Return mapping from generated var name -> semantic var name.

    Example: if variables.css contains:
        --ui-text-muted: var(--color-hex-94a3b8);
    then returns:
        {"color-hex-94a3b8": "ui-text-muted"}
    """

    generated_to_semantic: Dict[str, str] = {}
    for m in CSS_VAR_DECL_RE.finditer(variables_css_text):
        semantic_name = m.group(1)
        if not semantic_name.startswith(semantic_prefix):
            continue

        raw_value = m.group(2).strip()
        ref = CSS_VAR_REF_RE.search(raw_value)
        if not ref:
            continue
        referenced_var = ref.group(1)
        if referenced_var.startswith("color-"):
            generated_to_semantic[referenced_var] = semantic_name

    return generated_to_semantic


def build_var_value_map(variables_css_text: str) -> Dict[str, str]:
    """Return mapping var_name -> raw value string for simple declarations in variables.css."""

    var_to_value: Dict[str, str] = {}
    for m in CSS_VAR_DECL_RE.finditer(variables_css_text):
        var_name = m.group(1)
        raw_value = m.group(2).strip()
        var_to_value[var_name] = raw_value
    return var_to_value


def infer_role_from_line(line: str) -> str:
    m = CSS_DECL_LINE_RE.match(line)
    if not m:
        return "color"
    prop = m.group(1).lower()
    if "background" in prop:
        return "bg"
    if prop.startswith("border") or "border" in prop:
        return "border"
    if prop == "color" or prop.endswith("-color"):
        return "text"
    if "shadow" in prop:
        return "shadow"
    if "stroke" in prop:
        return "stroke"
    if "fill" in prop:
        return "fill"
    return "color"


def sanitize_token_part(value: str) -> str:
    v = value.lower()
    v = re.sub(r"[^a-z0-9]+", "-", v)
    v = re.sub(r"-+", "-", v).strip("-")
    return v


def replace_color_vars_with_feature_tokens(
    text: str,
    file_stem: str,
    var_to_value: Dict[str, str],
    per_file_map: Dict[str, str],
    used_new_tokens: Set[str],
) -> Tuple[str, int, List[Tuple[str, str]]]:
    """Replace var(--color-...) with var(--<file-stem>-<role>-<n>) and return new token declarations.

    Returns: (updated_text, replacement_count, new_vars)
    where new_vars is list of (token_name_without_leading_dashes, literal_value)
    """

    replacements = 0
    new_vars: List[Tuple[str, str]] = []

    lines = text.splitlines(True)
    out_lines: List[str] = []
    for line in lines:
        role = infer_role_from_line(line)

        def _sub(m: re.Match) -> str:
            nonlocal replacements, new_vars
            var_name = m.group(1)
            if not var_name.startswith("color-"):
                return m.group(0)

            # Reuse existing mapping for this file
            token = per_file_map.get(var_name)
            if not token:
                base = f"{sanitize_token_part(file_stem)}-{role}"
                i = 1
                candidate = f"{base}-{i}"
                while candidate in used_new_tokens:
                    i += 1
                    candidate = f"{base}-{i}"
                token = candidate
                per_file_map[var_name] = token
                used_new_tokens.add(token)

                value = var_to_value.get(var_name)
                if not value:
                    # Fallback: keep original reference if we cannot resolve value
                    return m.group(0)
                new_vars.append((token, value))

            replacements += 1
            return f"var(--{token})"

        updated_line = CSS_VAR_REF_RE.sub(_sub, line)
        out_lines.append(updated_line)

    return "".join(out_lines), replacements, new_vars


def remove_color_var_declarations_from_variables_css(variables_css_text: str) -> str:
    lines = variables_css_text.splitlines(True)
    kept: List[str] = []
    for ln in lines:
        if re.match(r"^\s*--color-[a-z0-9_-]+\s*:", ln):
            continue
        kept.append(ln)
    return "".join(kept)


def sanitize_alpha(a: str) -> str:
    return a.replace(".", "_")


def var_name_for_color(color: ColorLiteral) -> str:
    if color.kind == "hex":
        # normalized is #rrggbb or #rrggbbaa
        return f"color-hex-{color.normalized[1:]}"

    if color.kind in {"rgb", "rgba"}:
        inner = color.normalized[color.normalized.find("(") + 1 : color.normalized.rfind(")")]
        parts = [p for p in inner.split(",") if p != ""]
        if color.kind == "rgb" and len(parts) >= 3:
            r, g, b = parts[:3]
            return f"color-rgb-{r}-{g}-{b}"
        if color.kind == "rgba" and len(parts) >= 4:
            r, g, b, a = parts[:4]
            return f"color-rgba-{r}-{g}-{b}-{sanitize_alpha(a)}"

    if color.kind in {"hsl", "hsla"}:
        inner = color.normalized[color.normalized.find("(") + 1 : color.normalized.rfind(")")]
        parts = [p for p in inner.split(",") if p != ""]
        if color.kind == "hsl" and len(parts) >= 3:
            h, s, l = parts[:3]
            return f"color-hsl-{h}-{s}-{l}".replace("%", "pct")
        if color.kind == "hsla" and len(parts) >= 4:
            h, s, l, a = parts[:4]
            return f"color-hsla-{h}-{s}-{l}-{sanitize_alpha(a)}".replace("%", "pct")

    # Fallback to stable hashless label
    return f"color-{color.kind}"


def should_exclude(path: Path, exclude_substrings: List[str]) -> bool:
    s = str(path)
    return any(sub in s for sub in exclude_substrings)


def iter_target_files(frontend_dir: Path, exclude_substrings: List[str]) -> Iterable[Path]:
    for p in frontend_dir.rglob("*"):
        if not p.is_file():
            continue
        if should_exclude(p, exclude_substrings):
            continue
        if p.suffix.lower() not in {".css", ".html", ".js"}:
            continue
        yield p


def insert_new_vars_into_variables_css(variables_css_text: str, new_vars: List[Tuple[str, str]]) -> str:
    # Insert before the closing brace of the :root block.
    m = re.search(r":root\s*\{", variables_css_text)
    if not m:
        raise RuntimeError("Could not find ':root {' in variables.css")

    brace_i = m.end() - 1
    level = 0
    root_end: Optional[int] = None
    for i in range(brace_i, len(variables_css_text)):
        ch = variables_css_text[i]
        if ch == "{":
            level += 1
        elif ch == "}":
            level -= 1
            if level == 0:
                root_end = i
                break
    if root_end is None:
        raise RuntimeError("Could not find end of :root block in variables.css")

    insertion = "\n".join([f"    --{name}: {value};" for name, value in new_vars])
    if insertion:
        insertion = "\n" + insertion + "\n"

    return variables_css_text[:root_end] + insertion + variables_css_text[root_end:]


def replace_literals_in_text(text: str, mapping: Dict[str, str]) -> Tuple[str, int]:
    # Replace by scanning the text and swapping matches with var(--...)
    # We do three passes (hex/rgb/hsl) with normalization-based lookup.
    count = 0

    def _hex_sub(m: re.Match) -> str:
        nonlocal count
        original = m.group(0)
        key = normalize_hex(original)
        var = mapping.get(key)
        if not var:
            return original
        count += 1
        return f"var(--{var})"

    def _paren_sub(m: re.Match) -> str:
        nonlocal count
        original = m.group(0)
        key = normalize_paren_color(original)
        var = mapping.get(key)
        if not var:
            return original
        count += 1
        return f"var(--{var})"

    text2 = HEX_RE.sub(_hex_sub, text)
    text3 = RGBA_RE.sub(_paren_sub, text2)
    text4 = HSLA_RE.sub(_paren_sub, text3)
    return text4, count


def replace_generated_vars_with_semantic_aliases(text: str, generated_to_semantic: Dict[str, str]) -> Tuple[str, int]:
    count = 0

    def _sub(m: re.Match) -> str:
        nonlocal count
        var_name = m.group(1)
        semantic = generated_to_semantic.get(var_name)
        if not semantic:
            return m.group(0)
        count += 1
        return f"var(--{semantic})"

    updated = CSS_VAR_REF_RE.sub(_sub, text)
    return updated, count


def main() -> int:
    parser = argparse.ArgumentParser(description="Codemod: extract frontend color literals to CSS variables and replace usages.")
    parser.add_argument("--frontend-dir", default=FRONTEND_DIR_DEFAULT)
    parser.add_argument("--variables-css", default=VARIABLES_CSS_DEFAULT)
    parser.add_argument("--apply", action="store_true", help="Rewrite files and update variables.css")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude paths containing this substring (can be used multiple times)")
    parser.add_argument(
        "--prefer-semantic",
        action="store_true",
        help="After replacements, also replace var(--color-...) references with semantic aliases (e.g. --ui-*) if defined in variables.css",
    )
    parser.add_argument(
        "--semantic-prefix",
        default="ui-",
        help="Semantic alias prefix to consider when prefer-semantic is enabled (default: ui-)",
    )
    parser.add_argument(
        "--feature-tokens",
        action="store_true",
        help="Replace var(--color-...) references with feature-scoped tokens based on filename (e.g. --sidebar-bg-1) and define them in variables.css",
    )
    parser.add_argument(
        "--purge-color-vars",
        action="store_true",
        help="When used with --feature-tokens and --apply, remove --color-* variable declarations from variables.css after generating feature tokens",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    frontend_dir = (repo_root / args.frontend_dir).resolve()
    variables_css_path = (repo_root / args.variables_css).resolve()

    exclude_substrings = EXCLUDE_SUBSTRINGS_DEFAULT + list(args.exclude)

    variables_css_text = variables_css_path.read_text(encoding="utf-8")
    existing_value_to_var = build_existing_value_to_var_map(variables_css_text)
    var_to_value = build_var_value_map(variables_css_text)
    generated_to_semantic: Dict[str, str] = {}
    if args.prefer_semantic:
        generated_to_semantic = build_semantic_alias_map(variables_css_text, args.semantic_prefix)

    # Gather all literals from target files
    all_literals: Set[ColorLiteral] = set()
    target_files = list(iter_target_files(frontend_dir, exclude_substrings))
    for p in target_files:
        if p.resolve() == variables_css_path:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for lit in iter_color_literals(text):
            all_literals.add(classify_and_normalize(lit))

    # Build mapping: normalized literal -> css var name (without leading --)
    mapping: Dict[str, str] = dict(existing_value_to_var)

    literal_new_vars: List[Tuple[str, str]] = []
    for c in sorted(all_literals, key=lambda x: (x.kind, x.normalized)):
        if c.normalized in mapping:
            continue
        name = var_name_for_color(c)
        # Ensure unique variable names
        base = name
        i = 2
        while any(v == name for v in mapping.values()):
            name = f"{base}-{i}"
            i += 1
        mapping[c.normalized] = name

        # Keep the stored value canonicalized
        if c.kind == "hex":
            value = c.normalized
        else:
            value = c.normalized
        literal_new_vars.append((name, value))

    # Replace in files
    total_replacements = 0
    total_semantic_replacements = 0
    total_feature_replacements = 0
    files_changed = 0

    # Track new vars to add (token_name -> value) so we only add each once
    feature_token_vars: Dict[str, str] = {}
    used_new_tokens: Set[str] = set()
    for p in target_files:
        if p.resolve() == variables_css_path:
            continue
        original = p.read_text(encoding="utf-8", errors="ignore")
        updated, replacements = replace_literals_in_text(original, mapping)

        feature_replacements = 0
        if args.feature_tokens:
            per_file_map: Dict[str, str] = {}
            updated, feature_replacements, feature_new_vars = replace_color_vars_with_feature_tokens(
                updated,
                file_stem=p.stem,
                var_to_value=var_to_value,
                per_file_map=per_file_map,
                used_new_tokens=used_new_tokens,
            )
            for name, value in feature_new_vars:
                feature_token_vars.setdefault(name, value)

        semantic_replacements = 0
        if args.prefer_semantic and generated_to_semantic:
            updated, semantic_replacements = replace_generated_vars_with_semantic_aliases(updated, generated_to_semantic)

        if (replacements or semantic_replacements or feature_replacements) and updated != original:
            files_changed += 1
            total_replacements += replacements
            total_semantic_replacements += semantic_replacements
            total_feature_replacements += feature_replacements
            if args.apply:
                p.write_text(updated, encoding="utf-8")

    updated_vars_css_text = variables_css_text
    if args.apply and literal_new_vars:
        updated_vars_css_text = insert_new_vars_into_variables_css(updated_vars_css_text, literal_new_vars)

    if feature_token_vars:
        # Add feature-scoped tokens to variables.css (even in dry-run for counting purposes we don't write)
        vars_to_add = sorted(feature_token_vars.items(), key=lambda kv: kv[0])
        if args.apply:
            updated_vars_css_text = insert_new_vars_into_variables_css(updated_vars_css_text, vars_to_add)

    if args.apply and args.feature_tokens and args.purge_color_vars:
        updated_vars_css_text = remove_color_var_declarations_from_variables_css(updated_vars_css_text)

    if args.apply and updated_vars_css_text != variables_css_text:
        variables_css_path.write_text(updated_vars_css_text, encoding="utf-8")

    print(f"Target files scanned: {len(target_files)}")
    print(f"Unique color literals found (excluding variables.css): {len(all_literals)}")
    print(f"New variables to add to variables.css: {len(literal_new_vars)}")
    print(f"Files with replacements: {files_changed}")
    print(f"Total replacements: {total_replacements}")
    if args.prefer_semantic:
        print(f"Total semantic alias replacements: {total_semantic_replacements}")
    if args.feature_tokens:
        print(f"Total feature token replacements: {total_feature_replacements}")
        print(f"New feature tokens to add to variables.css: {len(feature_token_vars)}")
    print("Mode:", "APPLY" if args.apply else "DRY-RUN")

    if not args.apply:
        print("\nRun again with --apply to rewrite files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
