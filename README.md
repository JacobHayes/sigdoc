# sigdoc

[![pypi](https://img.shields.io/pypi/v/sigdoc.svg)](https://pypi.python.org/pypi/sigdoc)
[![downloads](https://pepy.tech/badge/sigdoc/month)](https://pepy.tech/project/sigdoc)
[![versions](https://img.shields.io/pypi/pyversions/sigdoc.svg)](https://github.com/JacobHayes/sigdoc)
[![license](https://img.shields.io/github/license/JacobHayes/sigdoc.svg)](https://github.com/JacobHayes/sigdoc/blob/golden/LICENSE)
[![CI](https://github.com/JacobHayes/sigdoc/actions/workflows/ci.yaml/badge.svg)](https://github.com/JacobHayes/sigdoc/actions/workflows/ci.yaml)
[![codecov](https://codecov.io/gh/JacobHayes/sigdoc/branch/golden/graph/badge.svg?token=6LUCpjcGdN)](https://codecov.io/gh/JacobHayes/sigdoc)

Inline documentation of parameters, returns, and raises.

---

Documenting function parameters and returns in docstrings is tedious - type hints need to be duplicated, the order is hard to maintain, and added/removed params and returns easily get out of sync.

`sigdoc` provides helpers to automatically extend docstrings _at runtime_ by annotating a function's parameter and return type hints "inline". This inline notation greatly increases the locality of the code and documentation, reducing the maintenance burden.

![](https://raw.githubusercontent.com/JacobHayes/sigdoc/main/docs/jupyter-help.png)

As this relies on runtime generation, the full docstring will only be visible to runtime inspection. Luckily, this includes `help(...)` in `python`, `ipython`, and `jupyter` (including `Shift+Tab`). Static analysis tools (such as many IDEs) won't know how to decipher the full docstring, but often show the function's signature, which will still have all of the useful information included.

## Installation

`sigdoc` can be installed from PyPI on python 3.9+ with `pip install sigdoc`.

## Contributing

Everyone is welcome to contribute - feel free to open an issue or PR!
