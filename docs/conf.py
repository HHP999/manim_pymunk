# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from pathlib import Path
import sys
import os

import manim_pymunk
from manim.utils.docbuild.module_parsing import parse_module_attributes

sys.path.insert(0, os.path.abspath("../src"))

project = "manim-pymunk"
copyright = "2026, CoreKSets"
author = "CoreKSets"
release = "v1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    # "sphinx.ext.napoleon",
    "myst_parser",
    "manim.utils.docbuild.manim_directive",
    "manim.utils.docbuild.autoaliasattr_directive",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {
    ".rst": "restructuredtext",
}

# 核心配置：自动生成文档页面
autosummary_generate = True
# 自动提取 docstrings 的设置
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
# 继承图配置
inheritance_diagram_graph_attrs = dict(rankdir="LR")

html_title = f"Manim Community v{manim_pymunk.__version__}"
# generate documentation from type hints
ALIAS_DOCS_DICT = parse_module_attributes()[0]
autodoc_typehints = "description"
autodoc_type_aliases = {
    alias_name: f"~manim.{module}.{alias_name}"
    for module, module_dict in ALIAS_DOCS_DICT.items()
    for category_dict in module_dict.values()
    for alias_name in category_dict
}
autoclass_content = "both"
latex_engine = "lualatex"
# controls whether functions documented by the autofunction directive
# appear with their full module names
add_module_names = False
# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
html_static_path = ["_static"]
html_favicon = str(Path("_static/LOGO.png"))
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_css_files = ["custom.css"]
html_static_path = ["_static"]
graphviz_output_format = "svg"
