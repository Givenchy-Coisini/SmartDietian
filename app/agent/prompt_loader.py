"""Prompt 模板加载器：基于 Jinja2，统一从 app/agent/prompts/ 目录加载 *.j2 模板。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

PROMPTS_DIR: Path = Path(__file__).parent / "prompts"


@lru_cache(maxsize=1)
def _get_env() -> Environment:
    """返回全局唯一的 Jinja2 Environment（按需懒加载）。"""
    return Environment(
        loader=FileSystemLoader(str(PROMPTS_DIR), encoding="utf-8"),
        autoescape=select_autoescape(enabled_extensions=(), default=False),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_prompt(template_name: str, **context: Any) -> str:
    """渲染指定模板。

    Args:
        template_name: 相对 prompts 目录的模板文件名，如 "personal_chief.j2"。
        **context: 注入模板的上下文变量。

    Returns:
        渲染后的 prompt 文本。
    """
    template = _get_env().get_template(template_name)
    return template.render(**context).strip()
