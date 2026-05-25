"""
Central config loader — reads settings.yaml once and exposes typed values.
Import this anywhere instead of hardcoding values.

Usage:
    from config.config import cfg
    print(cfg.llm_model)
    print(cfg.chunk_size)
"""

import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class BazarioConfig:
    # embedding
    embedding_model: str
    embedding_device: str
    embedding_normalize: bool

    # vectorstore
    index_path: str
    chunk_size: int
    chunk_overlap: int

    # retrieval
    top_k: int
    score_threshold: float

    # llm
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int

    # crew
    crew_verbose: bool
    crew_max_iterations: int
    crew_memory: bool

    # paths
    policies_dir: str
    outputs_dir: str
    eval_results_dir: str
    logs_dir: str

    # logging
    log_level: str
    log_save_to_file: bool
    log_file: str


def load_config(path: str = "config/settings.yaml") -> BazarioConfig:
    settings_path = Path(path)
    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")

    with open(settings_path, "r") as f:
        s = yaml.safe_load(f)

    return BazarioConfig(
        # embedding
        embedding_model     = s["embedding"]["model"],
        embedding_device    = s["embedding"]["device"],
        embedding_normalize = s["embedding"]["normalize"],

        # vectorstore
        index_path    = s["vectorstore"]["index_path"],
        chunk_size    = s["vectorstore"]["chunk_size"],
        chunk_overlap = s["vectorstore"]["chunk_overlap"],

        # retrieval
        top_k            = s["retrieval"]["top_k"],
        score_threshold  = s["retrieval"]["score_threshold"],

        # llm
        llm_model       = s["llm"]["model"],
        llm_temperature = s["llm"]["temperature"],
        llm_max_tokens  = s["llm"]["max_tokens"],

        # crew
        crew_verbose        = s["crew"]["verbose"],
        crew_max_iterations = s["crew"]["max_iterations"],
        crew_memory         = s["crew"]["memory"],

        # paths
        policies_dir    = s["paths"]["policies_dir"],
        outputs_dir     = s["paths"]["outputs_dir"],
        eval_results_dir = s["paths"]["eval_results_dir"],
        logs_dir        = s["paths"]["logs_dir"],

        # logging
        log_level        = s["logging"]["level"],
        log_save_to_file = s["logging"]["save_to_file"],
        log_file         = s["logging"]["log_file"],
    )


# Load once at import time — use this everywhere
cfg = load_config()