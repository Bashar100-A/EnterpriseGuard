#!/usr/bin/env python3
"""Local, standard-library retrieval-augmented generation utility."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import pickle
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT_DIR / "tools"
ACTIVITY_LOG_PATH = TOOLS_DIR / "activity_log.json"
ARCHIVE_LOG_PATH = TOOLS_DIR / "activity_log.archive.json"
TOKEN_PATTERN = re.compile(r"\w+")
UTC_PATTERN = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> str:
    """Return the current UTC time in strict SIEM-compatible form."""
    return datetime.now(timezone.utc).strftime(UTC_PATTERN)


def atomic_write_text(path: Path, content: str) -> None:
    """Write text atomically in the target directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, value) -> None:
    """Serialize JSON and replace the destination atomically."""
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path, default):
    """Read JSON defensively, returning a detached default on failure."""
    try:
        if not path.is_file():
            return default.copy() if isinstance(default, (dict, list)) else default
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Warning: unable to read JSON {path}: {exc}", file=sys.stderr)
        return default.copy() if isinstance(default, (dict, list)) else default


def _json_documents(value) -> list:
    """Extract document-like values from supported JSON structures."""
    if isinstance(value, dict) and isinstance(value.get("documents"), list):
        return value["documents"]
    if isinstance(value, list):
        return value
    return []


def _document_text(document) -> str:
    if isinstance(document, str):
        return document
    if isinstance(document, dict):
        return json.dumps(document, ensure_ascii=False, sort_keys=True)
    return str(document)


def log_rag_activity(query: str, model_status: str) -> None:
    """Append a RAG event and archive old entries atomically when necessary."""
    current = read_json(ACTIVITY_LOG_PATH, [])
    if isinstance(current, dict):
        entries = current.get("activities", [])
        if not isinstance(entries, list):
            entries = []
    elif isinstance(current, list):
        entries = current
    else:
        entries = []

    entry = {
        "id": f"{utc_now()}-{uuid.uuid4().hex}",
        "timestamp": utc_now(),
        "activity_type": "rag_run",
        "details": {"query": query, "model_status": model_status},
    }
    entries.append(entry)
    if len(entries) > 5000:
        archived = entries[:3000]
        entries = entries[3000:]
        atomic_write_json(ARCHIVE_LOG_PATH, archived)
        entries = entries[-2000:]
    atomic_write_json(ACTIVITY_LOG_PATH, entries)


class EnterpriseRAG:
    """Small local RAG engine with safe model and metadata handling."""

    def __init__(self, model_dir=None):
        if model_dir is None:
            primary = ROOT_DIR / "assets" / "models"
            secondary = ROOT_DIR / "src" / "assets" / "models"
            model_dir = primary if primary.exists() else secondary if secondary.exists() else None
        self.model_dir = Path(model_dir) if model_dir is not None else None
        self.models = {}
        self.model_status = "not_loaded"
        self.documents = []
        self.model_registry = {}
        self._json_values = []

    def _registry_hash(self, filename: str):
        models = self.model_registry.get("models", [])
        if isinstance(models, dict):
            record = models.get(filename, {})
            return record.get("sha256") or record.get("hash") if isinstance(record, dict) else None
        if isinstance(models, list):
            for record in models:
                if isinstance(record, dict) and record.get("file") == filename:
                    return record.get("sha256") or record.get("hash") or record.get("model_hash")
        return None

    def load_models(self):
        """Load verified pickle models and document-bearing JSON metadata."""
        if self.model_dir is None or not self.model_dir.is_dir():
            self.model_status = "no_models"
            return
        registry_path = self.model_dir / "registry" / "model_registry.json"
        registry = read_json(registry_path, {})
        if isinstance(registry, dict):
            self.model_registry = registry

        for json_path in sorted(self.model_dir.rglob("*.json")):
            value = read_json(json_path, None)
            if value is None:
                continue
            self._json_values.append(value)
            self.documents.extend(_json_documents(value))

        for pickle_path in sorted(self.model_dir.rglob("*.pkl")):
            expected = self._registry_hash(pickle_path.name)
            actual = hashlib.sha256(pickle_path.read_bytes()).hexdigest()
            if expected and expected != actual:
                print(f"Warning: SHA-256 mismatch; skipped {pickle_path}", file=sys.stderr)
                continue
            try:
                with pickle_path.open("rb") as handle:
                    self.models[pickle_path.name] = pickle.load(handle)
            except (OSError, pickle.PickleError, EOFError, AttributeError, ImportError, ValueError) as exc:
                print(f"Warning: unable to load {pickle_path}: {exc}", file=sys.stderr)

        self.model_status = "loaded" if self.models or self.documents else "no_models"

    def _tfidf_retrieve(self, query, top_k=5):
        """Return document records ranked by manually computed cosine similarity."""
        if not self.documents:
            return []
        texts = [_document_text(document) for document in self.documents]
        tokenized = [TOKEN_PATTERN.findall(text.lower()) for text in texts]
        query_tokens = TOKEN_PATTERN.findall(str(query).lower())
        document_frequency = collections.Counter()
        for tokens in tokenized:
            document_frequency.update(set(tokens))
        document_count = len(tokenized)
        vocabulary = set(document_frequency)
        query_counts = collections.Counter(query_tokens)

        def vector(tokens):
            counts = collections.Counter(tokens)
            return {
                token: (count / len(tokens)) * math.log((1 + document_count) / (1 + document_frequency[token])) + 1
                for token, count in counts.items()
                if token in vocabulary
            } if tokens else {}

        query_vector = vector(query_tokens)
        query_norm = math.sqrt(sum(value * value for value in query_vector.values()))
        ranked = []
        for document, tokens in zip(self.documents, tokenized):
            document_vector = vector(tokens)
            denominator = query_norm * math.sqrt(sum(value * value for value in document_vector.values()))
            score = sum(query_vector.get(token, 0) * value for token, value in document_vector.items()) / denominator if denominator else 0.0
            ranked.append({"document": document, "score": round(score, 6)})
        return sorted(ranked, key=lambda item: item["score"], reverse=True)[:top_k]

    def retrieve(self, query, top_k=5):
        """Retrieve TF-IDF matches, falling back to substring search over JSON."""
        if self.documents:
            return self._tfidf_retrieve(query, top_k)
        needle = str(query).lower()
        matches = []
        for value in self._json_values:
            text = _document_text(value)
            if needle in text.lower():
                matches.append({"document": value, "score": 1.0})
        return matches[:top_k]

    def generate(self, query):
        """Generate with a compatible loaded model or return retrieval-only output."""
        retrieved = self.retrieve(query)
        try:
            for model in self.models.values():
                generator = getattr(model, "generate", None)
                if callable(generator):
                    return {"answer": str(generator(query)), "context": retrieved}
        except Exception as exc:
            print(f"Warning: generation model failed: {exc}", file=sys.stderr)
        return {"answer": "Retrieval-only mode active. See retrieved documents.", "context": retrieved}


def run_query(query: str) -> dict:
    engine = EnterpriseRAG()
    engine.load_models()
    retrieved = engine.retrieve(query)
    generated = engine.generate(query)
    model_used = next(iter(engine.models), engine.model_status)
    return {
        "query": query,
        "retrieved_documents": retrieved,
        "generated_answer": str(generated.get("answer", "")),
        "model_used": model_used,
        "timestamp": utc_now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local EnterpriseGuard retrieval.")
    parser.add_argument("query", nargs="?", help="Query text")
    args = parser.parse_args()
    if not args.query:
        parser.print_usage(sys.stderr)
        return 1
    try:
        output = run_query(args.query)
        try:
            log_rag_activity(args.query, output["model_used"])
        except Exception as exc:
            print(f"Warning: unable to log RAG activity: {exc}", file=sys.stderr)
        print(json.dumps(output, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"RAG error: {exc}", file=sys.stderr)
        print(json.dumps({"error": True, "query": args.query, "retrieved_documents": [], "generated_answer": "", "model_used": "error", "timestamp": utc_now()}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
