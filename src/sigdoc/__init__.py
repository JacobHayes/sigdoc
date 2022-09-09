'''Inline documentation of parameters, returns, and raises.

Examples
--------
    >>> from typing import Annotated
    >>> from sigdoc import P, R, document
    >>>
    >>> @document
    ... def div(
    ...     a: Annotated[int, P("the numerator")], b: Annotated[int, P("the denominator")]
    ... ) -> Annotated[float, R("the result, rounded to 2 digits")]:
    ...     """Divide a by b."""
    ...     return round(a / b, 2)
    ...
    >>> print(div.__doc__)
    Divide a by b.
    <BLANKLINE>
    Parameters
    ----------
    a : int
        the numerator
    b : int
        the denominator
    <BLANKLINE>
    Returns
    -------
    float
        the result, rounded to 2 digits
'''
import dataclasses
import importlib.metadata
import inspect
import sys
import textwrap
import types
from collections import defaultdict
from collections.abc import Callable
from typing import _GenericAlias  # type: ignore[attr-defined]
from typing import (
    Annotated,
    Any,
    Optional,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

__all__ = [
    "P",
    "Param",
    "R",
    "Return",
    "document",
]
__version__ = importlib.metadata.version("sigdoc")


@dataclasses.dataclass(frozen=True)
class Param:
    """Document a parameter via the type hint.

    Parameters
    ----------
    description : Optional[str], default: None
        text describing the parameter
    default : Optional[str], default: pulled from the function
        text to show as the default; set explicitly to override
    type_hint : Optional[str], default: pulled from the function
        text of the type hint; set explicitly to override

    Notes
    -----
    Aliased as `sigdoc.P`.

    Examples
    --------
    See the module documentation for usage.
    """

    description: Optional[str] = None
    default: Optional[str] = None
    type_hint: Optional[str] = None

    def populate(self: "Param", param: inspect.Parameter) -> "Param":
        s = self
        if s.default is None and param.default is not param.empty:
            s = dataclasses.replace(s, default=repr(param.default))
        if s.type_hint is None and param.annotation is not param.empty:
            s = dataclasses.replace(s, type_hint=_stringize_type_hint(param.annotation))
        return s


P = Param


@dataclasses.dataclass(frozen=True)
class Return:
    """Document a return value via the type hint.

    Parameters
    ----------
    description : Optional[str], default: None
        text describing the parameter
    type_hint : Optional[str], default: pulled from the function
        text of the type hint; set explicitly to override

    Notes
    -----
    Aliased as `sigdoc.R`.

    Examples
    --------
    See the module documentation for usage.
    """

    description: Optional[str] = None
    type_hint: Optional[str] = None

    def populate(self: "Return", return_annotation: Any) -> "Return":
        s = self
        if s.type_hint is None and return_annotation is not inspect.Signature.empty:
            s = dataclasses.replace(
                s, type_hint=_stringize_type_hint(return_annotation)
            )
        return s


R = Return


FUNC = TypeVar("FUNC", bound=Callable[..., Any])
PARAM_KIND_PREFIX = defaultdict(
    str,
    {
        inspect.Parameter.VAR_POSITIONAL.name: "*",
        inspect.Parameter.VAR_KEYWORD.name: "**",
    },
)
STYLE_HANDLER = Callable[[inspect.Signature], str]
STYLE_HANDLERS = dict[str, STYLE_HANDLER]()


def register_style_handler(
    style: str,
) -> Callable[[STYLE_HANDLER], STYLE_HANDLER]:
    def register(fn: STYLE_HANDLER) -> STYLE_HANDLER:
        if (existing := STYLE_HANDLERS.get(style)) is not None:
            raise ValueError(
                f"A handler for '{style}' is already registered: {existing}"
            )
        STYLE_HANDLERS[style] = fn
        return fn

    return register


@overload
def document(fn: FUNC) -> FUNC:
    ...


@overload
def document(*, style: str = ...) -> Callable[[FUNC], FUNC]:
    ...


def document(
    fn: Optional[FUNC] = None, *, style: str = "numpydoc"
) -> Union[FUNC, Callable[[FUNC], FUNC]]:
    """Update the docstring to include parameters, returns, etc from the signature.

    New styles can be registered with `register_style_handler`.

    Examples
    --------
    See the module documentation for usage.
    """
    if (handler := STYLE_HANDLERS.get(style)) is None:
        raise ValueError(
            f"Unknown documentation style '{style}', known: {list(STYLE_HANDLERS)}"
        )

    def wrap(fn: FUNC) -> FUNC:
        signature = _signature(fn)
        # Remove trailing newlines so we have a known starting point
        base = inspect.getdoc(fn) or ""
        assert handler is not None  # Checked before creating this func
        addendum = handler(signature)
        if base or addendum:
            fn.__doc__ = f"{base}{addendum}"
        return fn

    if fn is None:
        return wrap
    return wrap(fn)


@register_style_handler("numpydoc")
def _document_numpydoc(signature: inspect.Signature) -> str:
    addendum = ""
    if signature.parameters:
        addendum += "\n"
        addendum += "\nParameters"
        addendum += "\n----------"
        for name, param in signature.parameters.items():
            param_doc = (
                _get_from_annotation(Param, param.annotation) or Param()
            ).populate(param)
            addendum += f"\n{PARAM_KIND_PREFIX[param.kind.name]}{name}"
            if param_doc.type_hint is not None:  # Could it be empty?
                addendum += f" : {param_doc.type_hint}"
            if param_doc.default is not None:
                addendum += f", default: {param_doc.default}"
            if param_doc.description is not None:
                addendum += f"\n{_format_description(param_doc.description)}"
    if signature.return_annotation is not signature.empty:
        addendum += "\n"
        addendum += "\nReturns"
        addendum += "\n-------"
        for return_annotation in _split_return_annotation(signature.return_annotation):
            return_doc = (
                _get_from_annotation(Return, return_annotation) or Return()
            ).populate(return_annotation)
            # NOTE: The type_hint will be `"None"` if it was explicitly provided, but should
            # never be `None` given we've already checked for `signature.empty`.
            assert return_doc.type_hint is not None
            addendum += f"\n{return_doc.type_hint}"
            if return_doc.description is not None:
                addendum += f"\n{_format_description(return_doc.description)}"
    return addendum


_T = TypeVar("_T")


def _discard_Annotated(annotation: Any) -> Any:
    return (
        get_args(annotation)[0] if get_origin(annotation) is Annotated else annotation
    )


def _format_description(description: str) -> str:
    return textwrap.indent(inspect.cleandoc(description), "    ")


def _get_from_annotation(klass: type[_T], annotation: Any) -> Optional[_T]:
    if not get_origin(annotation) is Annotated:
        return None
    matches = [hint for hint in get_args(annotation)[1:] if isinstance(hint, klass)]
    if len(matches) == 0:
        return None
    if len(matches) > 1:
        raise ValueError(
            f"Only a single {klass.__name__} value can be provided, found multiple in {annotation}"
        )
    return matches[0]


def _is_generic_alias(type_: Any) -> bool:
    return isinstance(type_, (_GenericAlias, types.GenericAlias))


def _split_return_annotation(type_hint: Any) -> tuple[Any, ...]:
    unwrapped = _discard_Annotated(type_hint)
    if get_origin(unwrapped) is tuple:
        args = get_args(unwrapped)
        if len(args) == 2 and args[1] == ...:
            return (type_hint,)
        # If we have multiple return values, there should be *no* Return hint on the
        # base `tuple`; instead, annotate each sub-value. Eg, this is not supported:
        #     -> Annotated[tuple[str, str], R(...)]
        #
        # We may want to support in the future (eg: when you want to document a
        # "well know" thing like a `Point` together as one), but it adds some
        # ambiguity we'll avoid for now.
        if _get_from_annotation(Return, type_hint) is not None:
            raise ValueError(
                "Multiple return values were found; provide a Return instance for each separately."
            )
        return tuple(args)
    return (type_hint,)


def _stringize_type_hint(type_hint: Any) -> str:
    type_hint = _discard_Annotated(type_hint)
    if type_hint is None.__class__:
        return str(None)  # Avoid showing "NoneType"
    if isinstance(type_hint, type) and not _is_generic_alias(type_hint):
        return type_hint.__name__  # Show `int` instead of `<class 'int'>`
    return str(type_hint)


if sys.version_info < (3, 10):  # pragma: no cover

    # `inspect.signature` on python <3.10 will return string annotations for cases like:
    # - modules using `from __future__ import annotations`
    # - hard coded string annotations (such as future refs) like `x: "str"`
    def _signature(fn: Callable[..., Any]) -> inspect.Signature:
        sig = inspect.signature(fn)
        type_hints = get_type_hints(fn, include_extras=True)
        return sig.replace(
            parameters=[
                p.replace(annotation=type_hints.get(p.name, p.annotation))
                for p in sig.parameters.values()
            ],
            return_annotation=type_hints.get("return", sig.return_annotation),
        )

else:

    def _signature(fn: Callable[..., Any]) -> inspect.Signature:
        return inspect.signature(fn, eval_str=True)
