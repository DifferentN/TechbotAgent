#!/usr/bin/env python3
"""Read-only checks for the bundled migration schemas; Python 3.11+ stdlib."""

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SCHEMA_KEYS = {
    "$schema", "$defs", "$ref", "title", "description", "type", "const",
    "enum", "properties", "required", "additionalProperties", "items",
    "minItems", "minLength", "pattern", "minimum",
}
PROTECTED = {".git", ".codebuddy", ".codex", ".agents"}
TEXT = {"type": "string"}
TEXTS = {"type": "array", "items": TEXT}
COMMANDS = {
    "type": "object", "additionalProperties": False,
    "required": ["build_argv", "test_argv"],
    "properties": {"build_argv": TEXTS, "test_argv": TEXTS},
}
CONFIG_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["schema_version", "android_root", "ios_root", "artifact_root",
                 "allowed_write_roots", "default_ui_policy", "validation"],
    "properties": {
        "schema_version": {"const": "1.0"},
        "android_root": TEXT, "ios_root": TEXT, "artifact_root": TEXT,
        "allowed_write_roots": TEXTS,
        "default_ui_policy": {"enum": ["mixed", "native", "visual"]},
        "validation": {
            "type": "object", "additionalProperties": False,
            "required": ["android", "ios"],
            "properties": {"android": COMMANDS, "ios": COMMANDS},
        },
    },
}


def read_json(path):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError(f"invalid JSON constant: {value}")

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=unique_object, parse_constant=invalid_constant,
    )


def document_digest(document):
    if not isinstance(document, dict):
        raise ValueError("digest input must be a JSON object")
    payload = {key: value for key, value in document.items() if key != "approval"}
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def schema_errors(value, schema, label):
    errors = []

    def check_schema(node):
        unknown = set(node) - SCHEMA_KEYS
        if unknown:
            raise ValueError(f"unsupported schema keywords: {sorted(unknown)}")
        if node.get("type") not in (None, "object", "array", "string", "integer"):
            raise ValueError("unsupported schema type")
        if "additionalProperties" in node and node["additionalProperties"] is not False:
            raise ValueError("only additionalProperties=false is supported")
        for key in ("properties", "$defs"):
            for child in node.get(key, {}).values():
                check_schema(child)
        if "items" in node:
            check_schema(node["items"])

    def visit(item, node, location):
        if "$ref" in node:
            reference = node["$ref"]
            if not reference.startswith("#/$defs/"):
                raise ValueError("only local $defs references are supported")
            return visit(item, schema["$defs"][reference.removeprefix("#/$defs/")], location)
        expected = node.get("type")
        valid_type = {
            "object": isinstance(item, dict), "array": isinstance(item, list),
            "string": isinstance(item, str), "integer": type(item) is int,
        }
        if expected and not valid_type[expected]:
            errors.append(f"{location}: expected {expected}")
            return
        if "const" in node and item != node["const"]:
            errors.append(f"{location}: expected constant {node['const']!r}")
        if "enum" in node and item not in node["enum"]:
            errors.append(f"{location}: invalid enum value")
        if isinstance(item, dict):
            properties = node.get("properties", {})
            for key in node.get("required", []):
                if key not in item:
                    errors.append(f"{location}.{key}: missing required field")
            if node.get("additionalProperties") is False:
                for key in item.keys() - properties.keys():
                    errors.append(f"{location}.{key}: unknown field")
            for key in item.keys() & properties.keys():
                visit(item[key], properties[key], f"{location}.{key}")
        elif isinstance(item, list):
            if len(item) < node.get("minItems", 0):
                errors.append(f"{location}: too few items")
            if "items" in node:
                for index, child in enumerate(item):
                    visit(child, node["items"], f"{location}[{index}]")
        elif isinstance(item, str):
            if len(item) < node.get("minLength", 0):
                errors.append(f"{location}: string is too short")
            if "pattern" in node and re.search(node["pattern"], item) is None:
                errors.append(f"{location}: string pattern mismatch")
        elif type(item) is int and "minimum" in node and item < node["minimum"]:
            errors.append(f"{location}: below minimum")

    check_schema(schema)
    visit(value, schema, label)
    return errors


def overlaps(left, right):
    return left.is_relative_to(right) or right.is_relative_to(left)


def root_path(value, label, errors):
    path = Path(value)
    if not value.strip() or not path.is_absolute() or not path.is_dir():
        errors.append(f"{label}: require an existing absolute directory")
        return None
    return path.resolve()


def index_rows(rows, key, label, errors):
    result = {}
    for row in rows:
        identity = row[key]
        if identity in result:
            errors.append(f"{label}: duplicate ID {identity}")
        result[identity] = row
    return result


def check_refs(values, available, label, errors):
    if len(values) != len(set(values)):
        errors.append(f"{label}: duplicate references")
    for identity in values:
        if identity not in available:
            errors.append(f"{label}: missing reference {identity}")


def check_approval(document, label, ready, errors):
    approval = document["approval"]
    if ready and approval["status"] != "approved":
        errors.append(f"{label}: explicit approval is required")
    if approval["status"] == "approved":
        if not approval["record"].strip():
            errors.append(f"{label}: confirmation record is empty")
        if approval["digest"] != document_digest(document):
            errors.append(f"{label}: approval digest is stale or missing")


def validate(config, workspace_root, ir=None, design=None, stage="draft"):
    errors = schema_errors(config, CONFIG_SCHEMA, "config")
    if stage not in ("draft", "ready"):
        errors.append("stage: expected draft or ready")
    if errors:
        return errors
    ready = stage == "ready"
    workspace = root_path(str(workspace_root), "workspace_root", errors)
    android = root_path(config["android_root"], "android_root", errors)
    ios = root_path(config["ios_root"], "ios_root", errors)
    if workspace is None or android is None or ios is None:
        return errors
    if overlaps(android, ios):
        errors.append("project roots: identical, nested or symlink-equivalent roots are forbidden")
    artifact_value = config["artifact_root"]
    artifact = (workspace / artifact_value).resolve()
    if not artifact_value.strip() or artifact == workspace or not artifact.is_relative_to(workspace):
        errors.append("artifact_root: require a child directory inside the coordinator workspace")
    elif any(part in PROTECTED for part in artifact.relative_to(workspace).parts):
        errors.append("artifact_root: cannot use protected agent or Git metadata directories")
    if any(overlaps(artifact, root) for root in (android, ios)):
        errors.append("artifact_root: must not overlap either project root")
    write_roots = []
    for value in config["allowed_write_roots"]:
        path = root_path(value, "allowed_write_roots", errors)
        if path is not None:
            if path not in (android, ios):
                errors.append("allowed_write_roots: only exact configured project roots are allowed")
            write_roots.append(path)
    if ir is None:
        if design is not None or ready:
            errors.append("IR and design are required for design/ready validation")
        return errors
    errors.extend(schema_errors(ir, read_json(ASSETS / "ir.schema.json"), "ir"))
    if errors:
        return errors
    source, target = (android, ios) if ir["direction"] == "android-to-ios" else (ios, android)
    for name, expected_root, frameworks in (
        ("source", source, {"compose", "xml"} if source == android else {"swiftui", "uikit"}),
        ("target", target, {"compose", "xml"} if target == android else {"swiftui", "uikit"}),
    ):
        actual = root_path(ir[name]["root"], f"ir.{name}.root", errors)
        if actual != expected_root:
            errors.append(f"ir.{name}.root: inconsistent with direction/configuration")
        if ir[name]["ui_framework"] not in frameworks:
            errors.append(f"ir.{name}.ui_framework: incompatible with platform")
    if ready and target not in write_roots:
        errors.append("ready: target is not explicitly listed in allowed_write_roots")
    evidence = index_rows(ir["evidence"], "id", "evidence", errors)
    contracts = index_rows(ir["contracts"], "id", "contracts", errors)
    scenarios = index_rows(ir["scenarios"], "id", "scenarios", errors)
    unknowns = index_rows(ir["unknowns"], "id", "unknowns", errors)
    for contract in contracts.values():
        label = contract["id"]
        check_refs(contract["evidence_ids"], evidence, label, errors)
        if contract["confidence"] == "verified" and not contract["evidence_ids"]:
            errors.append(f"{label}: verified contract requires evidence")
        if ready and contract["confidence"] == "unknown":
            errors.append(f"{label}: unknown contract is not ready")
        states = index_rows(contract["states"], "id", f"{label}.states", errors)
        transitions = index_rows(contract["transitions"], "id", f"{label}.transitions", errors)
        for transition in transitions.values():
            check_refs([transition["from"]], states, transition["id"], errors)
            check_refs([transition["to"]], states, transition["id"], errors)
    coverage = set()
    for scenario in scenarios.values():
        check_refs(scenario["contract_ids"], contracts, scenario["id"], errors)
        check_refs(scenario["evidence_ids"], evidence, scenario["id"], errors)
        coverage.update(scenario["contract_ids"])
    if set(contracts) - coverage:
        errors.append("scenarios: every contract needs acceptance coverage")
    for unknown in unknowns.values():
        check_refs(unknown["contract_ids"], contracts, unknown["id"], errors)
        if unknown["status"] == "resolved" and not unknown["resolution"].strip():
            errors.append(f"{unknown['id']}: resolved question needs an explanation")
        if ready and unknown["status"] == "open" and unknown["severity"] in ("blocker", "high"):
            errors.append(f"{unknown['id']}: unresolved high-risk question")
    check_approval(ir, "ir", ready, errors)
    if design is None:
        if ready:
            errors.append("ready: target design is required")
        return errors
    design_errors = schema_errors(design, read_json(ASSETS / "design.schema.json"), "design")
    errors.extend(design_errors)
    if design_errors:
        return errors
    if design["task_id"] != ir["task_id"] or design["ui_policy"] != ir["ui_policy"]:
        errors.append("design: task/UI policy must match approved IR")
    if design["target_baseline"] != ir["target"]["baseline"]:
        errors.append("design: target baseline differs from analyzed IR")
    binding = design["source_ir_digest"]
    if (ready or binding) and binding != document_digest(ir):
        errors.append("design: source_ir_digest is stale or missing")
    mappings = index_rows(design["mappings"], "contract_id", "mappings", errors)
    if set(mappings) != set(contracts):
        errors.append("design: mappings must cover exactly the IR contracts")
    for identity, mapping in mappings.items():
        if identity not in contracts:
            continue
        contract = contracts[identity]
        expected = {
            "state_ids": {state["id"] for state in contract["states"]},
            "transition_ids": {item["id"] for item in contract["transitions"]},
            "scenario_ids": {sid for sid, scenario in scenarios.items() if identity in scenario["contract_ids"]},
        }
        for field, required in expected.items():
            check_refs(mapping[field], required, f"mapping.{identity}.{field}", errors)
            if set(mapping[field]) != required:
                errors.append(f"mapping.{identity}.{field}: incomplete coverage")
        if mapping["equivalence"] != "strict" and not mapping["user_impact"].strip():
            errors.append(f"mapping.{identity}: non-strict mapping needs user-visible impact")
        if ready and mapping["equivalence"] in ("partial", "unsupported"):
            errors.append(f"mapping.{identity}: unresolved partial/unsupported scope")
    slices = index_rows(design["slices"], "id", "slices", errors)
    slice_contracts, slice_scenarios = set(), set()
    for identity, item in slices.items():
        check_refs(item["contract_ids"], contracts, identity, errors)
        check_refs(item["depends_on"], slices, identity, errors)
        check_refs(item["tests"], scenarios, f"{identity}.tests", errors)
        slice_contracts.update(item["contract_ids"])
        slice_scenarios.update(item["tests"])
        for file_name in item["files"]:
            relative = PurePosixPath(file_name)
            if (relative.is_absolute() or ".." in relative.parts or not relative.parts
                    or any(character in file_name for character in "\\:*?[]")
                    or any(part in PROTECTED for part in relative.parts)):
                errors.append(f"{identity}.files: require literal safe target-relative files")
                continue
            resolved = (target / file_name).resolve()
            if not resolved.is_relative_to(target) or resolved == target or resolved.is_dir():
                errors.append(f"{identity}.files: target path escapes root or names a directory")
    if slice_contracts != set(contracts) or slice_scenarios != set(scenarios):
        errors.append("slices: incomplete contract/scenario coverage")
    visiting, visited = set(), set()

    def check_cycle(identity):
        if identity in visiting:
            errors.append("slices: cyclic dependencies")
            return
        if identity in visited or identity not in slices:
            return
        visiting.add(identity)
        for dependency in slices[identity]["depends_on"]:
            check_cycle(dependency)
        visiting.remove(identity)
        visited.add(identity)

    for identity in slices:
        check_cycle(identity)
    check_approval(design, "design", ready, errors)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--ir", type=Path)
    parser.add_argument("--design", type=Path)
    parser.add_argument("--stage", choices=("draft", "ready"), default="draft")
    parser.add_argument("--digest", type=Path)
    args = parser.parse_args()
    if args.digest and (args.config or args.ir or args.design or args.stage != "draft"):
        parser.error("--digest cannot be combined with validation options")
    if not args.digest and not args.config:
        parser.error("--config is required unless using --digest")
    try:
        if args.digest:
            print(document_digest(read_json(args.digest)))
            return 0
        errors = validate(
            read_json(args.config), args.workspace_root,
            read_json(args.ir) if args.ir else None,
            read_json(args.design) if args.design else None, args.stage,
        )
    except (OSError, ValueError, KeyError, RecursionError) as exc:
        print(f"INVALID: {exc}")
        return 1
    if errors:
        for error in errors:
            print(f"INVALID: {error}")
        return 1
    print("VALID: static migration checks passed; not runtime verification or authorization")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
