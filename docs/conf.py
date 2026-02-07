# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os


sys.path.insert(0, os.path.abspath('../src'))

project = "manim-pymunk"
copyright = "2026, CoreKSets"
author = "CoreKSets"
release = "v0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon", # 必须添加！
    "myst_parser",

]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {
    '.rst': 'restructuredtext',
}

# 核心配置：自动生成文档页面
autosummary_generate = True  
# 自动提取 docstrings 的设置
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
# 继承图配置
inheritance_diagram_graph_attrs = dict(rankdir="LR")

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
