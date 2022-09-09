import inspect
from typing import Annotated, Optional

import pytest

from sigdoc import P, R, document, register_style_handler


def test_basic() -> None:
    @document
    def fn(a: Annotated[str, P("blah")]) -> Annotated[str, R("blah")]:
        """Docstring"""
        return a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : str
            blah

        Returns
        -------
        str
            blah
        """
    )


def test_empty() -> None:
    @document
    def fn():  # type: ignore[no-untyped-def] # Test without `-> None`
        pass

    assert fn.__doc__ is None


def test_bare() -> None:
    @document
    def fn():  # type: ignore[no-untyped-def] # Test without `-> None`
        """Docstring"""

    assert fn.__doc__ == "Docstring"


def test_param() -> None:
    @document
    def fn(a: Annotated[str, P("blah")]):  # type: ignore[no-untyped-def] # Test without `-> None`
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : str
            blah
        """
    )


def test_param_default() -> None:
    @document
    def fn(a: Annotated[str, P("blah")] = "default") -> None:
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : str, default: 'default'
            blah

        Returns
        -------
        None
        """
    )


def test_param_default_override() -> None:
    @document
    def fn(
        a: int, b: Annotated[Optional[int], P(default="inferred from `a`")] = None
    ) -> None:
        """Docstring"""
        assert a, b

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : int
        b : typing.Optional[int], default: inferred from `a`

        Returns
        -------
        None
        """
    )


def test_param_dup_hints() -> None:
    def fn(a: Annotated[int, P("1"), P("2")]) -> None:
        """Docstring"""
        assert a

    orig = fn.__doc__
    with pytest.raises(ValueError, match="Only a single Param value can be provided"):
        document(fn)
    assert fn.__doc__ == orig


def test_param_multiline() -> None:
    @document
    def fn(
        a: Annotated[
            str,
            P(
                """some long
                multiline

                description
                """
            ),
        ]
    ) -> None:
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : str
            some long
            multiline

            description

        Returns
        -------
        None
        """
    )


def test_param_type_hint_missing() -> None:
    @document
    def fn(a) -> None:  # type: ignore[no-untyped-def]
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a

        Returns
        -------
        None
        """
    )


def test_param_type_hint_override() -> None:
    @document
    def fn(a: Annotated[str, P(type_hint="Optional[str]")] = None) -> None:  # type: ignore[assignment]
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : Optional[str], default: None

        Returns
        -------
        None
        """
    )


def test_param_vargs_kwargs() -> None:
    @document
    def fn(*args: str, **kwargs: str) -> None:
        """Docstring"""
        assert args, kwargs

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        *args : str
        **kwargs : str

        Returns
        -------
        None
        """
    )


def test_return() -> None:
    @document
    def fn() -> Annotated[int, R("ret")]:
        """Docstring"""

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        int
            ret
        """
    )


def test_return_tuple() -> None:
    @document
    def fn() -> tuple[str, ...]:
        """Docstring"""
        return "a", "b"

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        tuple[str, ...]
        """
    )


def test_return_tuple_doc() -> None:
    @document
    def fn() -> Annotated[tuple[str, ...], R("doc")]:
        """Docstring"""
        return "a", "b"

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        tuple[str, ...]
            doc
        """
    )


def test_return_tuple_empty() -> None:
    @document
    def fn() -> tuple:  # type: ignore[type-arg]
        """Docstring"""
        return "a", "b"

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        tuple
        """
    )


def test_return_multiple() -> None:
    @document
    def fn() -> tuple[str, int]:
        """Docstring"""
        return "a", 1

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        str
        int
        """
    )


def test_return_multiple_doc() -> None:
    @document
    def fn() -> tuple[str, Annotated[int, R("doc")]]:
        """Docstring"""
        return "a", 1

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        str
        int
            doc
        """
    )


def test_return_multiple_root_doc() -> None:
    def fn() -> Annotated[tuple[str, int], R("doc")]:
        """Docstring"""
        return "a", 1

    orig = fn.__doc__
    with pytest.raises(
        ValueError,
        match="Multiple return values were found; provide a Return instance for each separately.",
    ):
        document(fn)
    assert fn.__doc__ == orig


def test_return_none() -> None:
    @document
    def fn() -> None:
        """Docstring"""

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        None
        """
    )


def test_return_type_hint_override() -> None:
    @document
    def fn() -> Annotated[int, R(type_hint="some_type")]:
        """Docstring"""
        return 5

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Returns
        -------
        some_type
        """
    )


def test_string_annotations() -> None:
    @document
    def fn(a: 'Annotated[str, P("blah")]') -> 'Annotated[str, R("blah")]':
        """Docstring"""
        return a

    assert fn.__doc__ == inspect.cleandoc(
        """
        Docstring

        Parameters
        ----------
        a : str
            blah

        Returns
        -------
        str
            blah
        """
    )


def test_style() -> None:
    @document(style="numpydoc")
    def fn(a: Annotated[str, P("blah")]) -> Annotated[str, R("blah")]:
        """Docstring"""
        return a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : str
            blah

        Returns
        -------
        str
            blah
        """
    )


def test_style_dup() -> None:
    def styler(signature: inspect.Signature) -> str:
        assert signature
        return ""

    register_style_handler("test_style_dup")(styler)
    with pytest.raises(
        ValueError, match="A handler for 'test_style_dup' is already registered"
    ):
        register_style_handler("test_style_dup")(styler)


def test_style_unknown() -> None:
    with pytest.raises(ValueError, match="junk"):
        document(style="junk")


def test_tricky_annotation() -> None:
    @document
    def fn(a: Annotated[int, "not a docstring"]) -> Annotated[None, "not a docstring"]:
        """Docstring"""
        assert a

    assert fn.__doc__ == inspect.cleandoc(
        """Docstring

        Parameters
        ----------
        a : int

        Returns
        -------
        None
        """
    )
