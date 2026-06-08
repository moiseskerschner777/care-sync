import hashlib
from dataclasses import dataclass
from pathlib import Path

import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree

PY_LANGUAGE = Language(tspython.language())

SMALL_FILE_THRESHOLD = 40


def parse_file(path: Path) -> Tree:
    parser = Parser(PY_LANGUAGE)
    source = path.read_bytes()
    return parser.parse(source)


@dataclass
class Chunk:
    id: str
    file: str
    type: str
    name: str
    decorator: str
    start_line: int
    end_line: int
    text: str
    module: str


def chunk_id(file: str, type: str, name: str) -> str:
    return hashlib.sha1(f"{file}::{type}::{name}".encode()).hexdigest()


def _walk_collect(node, node_type):
    result = []

    def walk(n):
        if n.type == node_type:
            result.append(n)
        for child in n.children:
            walk(child)

    walk(node)
    return result


def _path_has_component(rel_path: str, component: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    return component in parts


def _is_route_file(rel_path: str) -> bool:
    return _path_has_component(rel_path, "routes")


def _is_schema_file(rel_path: str) -> bool:
    return _path_has_component(rel_path, "schemas")


def chunk_file(path: Path, root: Path) -> list:
    source_bytes = path.read_bytes()
    tree = parse_file(path)
    rel_path = str(path.relative_to(root))
    module_name = rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
    stem = path.stem

    source_str = source_bytes.decode()
    lines = source_str.splitlines()
    total_lines = len(lines)

    is_route = _is_route_file(rel_path)
    is_schema = _is_schema_file(rel_path)
    is_small = total_lines <= SMALL_FILE_THRESHOLD

    chunks: list = []

    if is_small:
        chunk_type = "schema" if is_schema else "module"
        chunks.append(Chunk(
            id=chunk_id(rel_path, chunk_type, stem),
            file=rel_path,
            type=chunk_type,
            name=stem,
            decorator="",
            start_line=1,
            end_line=total_lines,
            text=source_str,
            module=module_name,
        ))
        return chunks

    for node in _walk_collect(tree.root_node, "function_definition"):
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "<unknown>"

        decorator_str = ""
        decorator_node = node.child_by_field_name("decorator")
        if decorator_node:
            decorator_str = source_bytes[decorator_node.start_byte:decorator_node.end_byte].decode().strip()

        text = source_bytes[node.start_byte:node.end_byte].decode()
        chunk_type = "schema" if is_schema else "function"

        chunks.append(Chunk(
            id=chunk_id(rel_path, chunk_type, name),
            file=rel_path,
            type=chunk_type,
            name=name,
            decorator=decorator_str,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            text=text,
            module=module_name,
        ))

    for node in _walk_collect(tree.root_node, "class_definition"):
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode() if name_node else "<unknown>"
        text = source_bytes[node.start_byte:node.end_byte].decode()
        chunk_type = "schema" if is_schema else "class"

        chunks.append(Chunk(
            id=chunk_id(rel_path, chunk_type, name),
            file=rel_path,
            type=chunk_type,
            name=name,
            decorator="",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            text=text,
            module=module_name,
        ))

    if not is_route:
        import_texts = []
        import_end = 0
        for child in tree.root_node.named_children:
            if child.type in ("import_statement", "import_from_statement"):
                import_texts.append(source_bytes[child.start_byte:child.end_byte].decode())
                import_end = child.end_point[0] + 1
        if import_texts:
            first_import = next(
                c for c in tree.root_node.named_children
                if c.type in ("import_statement", "import_from_statement")
            )
            chunk_type = "schema" if is_schema else "imports"
            chunks.append(Chunk(
                id=chunk_id(rel_path, chunk_type, stem),
                file=rel_path,
                type=chunk_type,
                name=stem,
                decorator="",
                start_line=first_import.start_point[0] + 1,
                end_line=import_end,
                text="\n".join(import_texts),
                module=module_name,
            ))

    module_type = "schema" if is_schema else "module"
    chunks.append(Chunk(
        id=chunk_id(rel_path, module_type, stem),
        file=rel_path,
        type=module_type,
        name=stem,
        decorator="",
        start_line=1,
        end_line=total_lines,
        text=source_str,
        module=module_name,
    ))

    return chunks


def chunk_codebase(root: Path) -> list:
    skip_dirs = {"__pycache__", ".venv", ".git", "node_modules", "tests", "seed"}
    all_chunks: list = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        if any(p in skip_dirs for p in rel.parts[:-1]):
            continue
        all_chunks.extend(chunk_file(py_file, root))
    return all_chunks
