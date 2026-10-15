import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from ..core.config import settings
import json

def get_db_path():
    raw = settings.database_url
    if raw.startswith("sqlite:///"):
        return raw.replace("sqlite:///", "")
    return ":memory:"

_memory_conn = None

def get_db_connection():
    global _memory_conn
    path = get_db_path()
    if path == ":memory:":
        if _memory_conn is None:
            _memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
        return _memory_conn
    return sqlite3.connect(path)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Audit log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL
    )
    """)
    
    # Programs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agc_programs (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        craft TEXT NOT NULL,
        description TEXT NOT NULL,
        source_code TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    # Program variants table (for Luminary/Comanche comparison)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agc_program_variants (
        id TEXT PRIMARY KEY,
        program_id TEXT NOT NULL,
        craft TEXT NOT NULL,  -- 'LM' for Luminary, 'CM' for Comanche
        variant_name TEXT NOT NULL,
        source_code TEXT NOT NULL,
        parsed_ast_json TEXT,  -- JSON serialized AST
        metadata_json TEXT,    -- additional metadata (bank count, instruction count, etc.)
        created_at TEXT NOT NULL,
        FOREIGN KEY (program_id) REFERENCES agc_programs (id)
    )
    """)
    
    # Benchmark runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        metrics_json TEXT NOT NULL
    )
    """)
    
    conn.commit()
    if get_db_path() != ":memory:":
        conn.close()

def log_audit(user_id: str, action: str, details: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO audit_logs (timestamp, user_id, action, details) VALUES (?, ?, ?, ?)",
        (now, user_id, action, json.dumps(details))
    )
    conn.commit()
    if get_db_path() != ":memory:":
        conn.close()

def fetch_audit_logs(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, user_id, action, details FROM audit_logs ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    rows = cursor.fetchall()
    if get_db_path() != ":memory:":
        conn.close()
    return [
        {"id": r[0], "timestamp": r[1], "user_id": r[2], "action": r[3], "details": r[4]}
        for r in rows
    ]

def save_program(id: str, name: str, craft: str, description: str, source_code: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "INSERT OR REPLACE INTO agc_programs (id, name, craft, description, source_code, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (id, name, craft, description, source_code, now)
    )
    conn.commit()
    if get_db_path() != ":memory:":
        conn.close()

def get_program(id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, craft, description, source_code, created_at FROM agc_programs WHERE id = ?", (id,))
    row = cursor.fetchone()
    if get_db_path() != ":memory:":
        conn.close()
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "craft": row[2],
            "description": row[3],
            "source_code": row[4],
            "created_at": row[5]
        }
    return None

def list_all_programs() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, craft, description, created_at FROM agc_programs ORDER BY name ASC")
    rows = cursor.fetchall()
    if get_db_path() != ":memory:":
        conn.close()
    return [
        {"id": r[0], "name": r[1], "craft": r[2], "description": r[3], "created_at": r[4]}
        for r in rows
    ]

def save_program_variant(
    variant_id: str,
    program_id: str,
    craft: str,
    variant_name: str,
    source_code: str,
    parsed_ast_json: str,
    metadata_json: str
):
    """Save a program variant (Luminary or Comanche version)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        """INSERT OR REPLACE INTO agc_program_variants 
        (id, program_id, craft, variant_name, source_code, parsed_ast_json, metadata_json, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (variant_id, program_id, craft, variant_name, source_code, parsed_ast_json, metadata_json, now)
    )
    conn.commit()
    if get_db_path() != ":memory:":
        conn.close()

def get_program_variant(variant_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific program variant"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, program_id, craft, variant_name, source_code, parsed_ast_json, metadata_json, created_at FROM agc_program_variants WHERE id = ?",
        (variant_id,)
    )
    row = cursor.fetchone()
    if get_db_path() != ":memory:":
        conn.close()
    if row:
        return {
            "id": row[0],
            "program_id": row[1],
            "craft": row[2],
            "variant_name": row[3],
            "source_code": row[4],
            "parsed_ast_json": row[5],
            "metadata_json": row[6],
            "created_at": row[7]
        }
    return None

def get_program_variants(program_id: str) -> List[Dict[str, Any]]:
    """Get all variants for a program (typically Luminary and Comanche)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, program_id, craft, variant_name, source_code, parsed_ast_json, metadata_json, created_at FROM agc_program_variants WHERE program_id = ? ORDER BY craft",
        (program_id,)
    )
    rows = cursor.fetchall()
    if get_db_path() != ":memory:":
        conn.close()
    return [
        {
            "id": r[0],
            "program_id": r[1],
            "craft": r[2],
            "variant_name": r[3],
            "source_code": r[4],
            "parsed_ast_json": r[5],
            "metadata_json": r[6],
            "created_at": r[7]
        }
        for r in rows
    ]
