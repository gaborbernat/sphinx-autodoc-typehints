# coding=utf-8
""" Extend typing"""

import inspect
from inspect import unwrap
from typing import Any, AnyStr, GenericMeta, TypeVar

from pytypes import get_type_hints
from sphinx.util import logging
from sphinx.util.inspect import Signature

TYPE_MARKER = "# type: "

LOGGER = logging.getLogger(__name__)


def format_annotation(annotation, aliases):  # pylint: disable=too-many-return-statements
    if inspect.isclass(annotation) and annotation.__module__ == "builtins":
        if annotation.__qualname__ == "NoneType":
            return "``None``"
        return ":class:`{}`".format(annotation.__qualname__)

    annotation_cls = annotation if inspect.isclass(annotation) else type(annotation)
    if annotation_cls.__module__ in ("typing",):
        return format_typing_annotation(annotation, annotation_cls, aliases)
    elif annotation is Ellipsis:
        return "..."
    elif inspect.isclass(annotation):
        extra = ""
        if isinstance(annotation, GenericMeta):
            extra = "\\[{}]".format(", ".join(format_annotation(param, aliases) for param in annotation.__parameters__))
        module_name, annotation_name = annotation.__module__, annotation.__qualname__
        if (module_name, annotation_name) in aliases:
            module_name, annotation_name = aliases[module_name, annotation_name]
        return ":class:`~{}.{}`{}".format(module_name, annotation_name, extra)
    else:
        return str(annotation)


def format_typing_annotation(annotation, annotation_cls, aliases):
    params = None
    prefix = ":class:"
    extra = ""
    class_name = annotation_cls.__qualname__
    if annotation is Any:
        return ":data:`~typing.Any`"
    elif annotation is AnyStr:
        return ":data:`~typing.AnyStr`"
    elif isinstance(annotation, TypeVar):
        return handle_type_var(annotation)
    elif class_name in ("Union", "_Union"):
        class_name, params, prefix = format_union_annotation(annotation, class_name, params, prefix, aliases)
    elif annotation_cls.__qualname__ == "Tuple" and hasattr(annotation, "__tuple_params__"):
        prefix = ":data:"
        # initial behavior, reworked in 3.6
        params = annotation.__tuple_params__  # pragma: no coverage
        if annotation.__tuple_use_ellipsis__:  # pragma: no coverage
            params += (Ellipsis,)  # pragma: no coverage
    elif annotation_cls.__qualname__ == "Tuple" and hasattr(annotation, "__args__"):
        prefix = ":data:"
        params = annotation.__args__  # pragma: no coverage
    elif annotation_cls.__qualname__ == "Callable":
        params, prefix = format_callable_annotation(annotation, params, prefix, aliases)
    elif hasattr(annotation, "type_var"):
        # Type alias
        class_name = annotation.name
        params = (annotation.type_var,)
    elif getattr(annotation, "__args__", None) is not None:
        params = annotation.__args__
    elif hasattr(annotation, "__parameters__"):
        params = annotation.__parameters__
    if params:
        extra = "\\[{}]".format(", ".join(format_annotation(param, aliases) for param in params))
    return "{}`~typing.{}`{}".format(prefix, class_name, extra)


def handle_type_var(annotation):
    if annotation.__constraints__:
        args = ", ".join(format_annotation(c, {}) for c in annotation.__constraints__)
        return ':class:`~typing.TypeVar`\\("{}", {})'.format(annotation.__name__, args)
    elif annotation.__bound__:
        return ':class:`~typing.TypeVar`\\("{}", bound= {})'.format(
            annotation.__name__, format_annotation(annotation.__bound__, {})
        )
    return "\\%r" % annotation


def format_callable_annotation(annotation, params, prefix, aliases):
    prefix = ":data:"
    arg_annotations = result_annotation = None
    if hasattr(annotation, "__result__"):
        # initial behavior, reworked in 3.6
        arg_annotations = annotation.__args__  # pragma: no coverage
        result_annotation = annotation.__result__  # pragma: no coverage
    elif getattr(annotation, "__args__", None) is not None:
        arg_annotations = annotation.__args__[:-1]
        result_annotation = annotation.__args__[-1]
    if arg_annotations in (Ellipsis, (Ellipsis,)):
        params = [Ellipsis, result_annotation]
    elif arg_annotations is not None:
        params = [
            "\\[{}]".format(", ".join(format_annotation(param, aliases) for param in arg_annotations)),
            result_annotation,
        ]
    return params, prefix


def format_union_annotation(annotation, class_name, params, prefix, aliases):  # pylint: disable=unused-argument
    prefix = ":data:"
    class_name = "Union"
    if hasattr(annotation, "__union_params__"):
        # initial behavior, reworked in 3.6
        un_params = annotation.__union_params__  # pragma: no coverage
    else:
        un_params = annotation.__args__
    if un_params and len(un_params) == 2:
        first_is_none = getattr(un_params[0], "__qualname__", None) == "NoneType"
        second_is_none = getattr(un_params[1], "__qualname__", None) == "NoneType"
        if first_is_none or second_is_none:
            class_name = "Optional"
            un_params = (un_params[0] if second_is_none else un_params[1],)
    return class_name, un_params, prefix


# noinspection PyUnusedLocal
def process_signature(
    app,
    what: str,
    name: str,
    obj,  # pylint: disable=too-many-arguments,unused-argument
    options,
    signature,
    return_annotation,
):  # pylint: disable=unused-argument
    if callable(obj):
        if what in ("class", "exception"):
            obj = getattr(obj, "__init__")

        obj = unwrap(obj)
        signature = Signature(obj)
        parameters = [
            param.replace(annotation=inspect.Parameter.empty) for param in signature.signature.parameters.values()
        ]

        if parameters:
            if what in ("class", "exception"):
                del parameters[0]
            elif what == "method":
                outer = inspect.getmodule(obj)
                if outer is None:
                    return 
                for clsname in obj.__qualname__.split(".")[:-1]:
                    outer = getattr(outer, clsname)

                method_name = obj.__name__
                if method_name.startswith("__") and not method_name.endswith("__"):
                    # If the method starts with double underscore (dunder)
                    # Python applies mangling so we need to prepend the class name.
                    # This doesn't happen if it always ends with double underscore.
                    class_name = obj.__qualname__.split(".")[-2]
                    method_name = "_{c}{m}".format(c=class_name, m=method_name)

                method_object = outer.__dict__[method_name]
                if not isinstance(method_object, (classmethod, staticmethod)):
                    del parameters[0]

        signature.signature = signature.signature.replace(
            parameters=parameters, return_annotation=inspect.Signature.empty
        )

        return signature.format_args().replace("\\", "\\\\"), None


# noinspection PyUnusedLocal
def process_docstring(app, what, name, obj, options, lines):  # pylint: disable=too-many-arguments,unused-argument
    if isinstance(obj, property):
        obj = obj.fget  # pragma: no coverage

    if callable(obj):
        if what in ("class", "exception"):
            obj = getattr(obj, "__init__")

        obj = unwrap(obj)
        try:
            type_hints = get_type_hints(obj)
        except (AttributeError, TypeError):
            return  # Introspecting a slot wrapper will raise TypeError

        if not type_hints:
            LOGGER.debug("[autodoc-typehints][no-type] %s %s", id(obj), getattr(obj, "__qualname__", None))

        LOGGER.debug(
            "[autodoc-typehints][process-docstring] for %d id %s got %s",
            id(obj),
            getattr(obj, "__qualname__", None),
            "|".join("{} - {}".format(k, v) for k, v in type_hints.items()),
        )

        insert_type_hints(lines, type_hints, what, app.config.sphinx_autodoc_alias)


def insert_type_hints(lines, type_hints, what, aliases):
    for arg_name, annotation in type_hints.items():
        formatted_annotation = format_annotation(annotation, aliases)
        if arg_name == "return":
            if what in ("class", "exception"):
                # Don't add return type None from __init__()
                continue

            insert_index = len(lines)
            for i, line in enumerate(lines):
                if line.startswith(":rtype:"):
                    insert_index = None
                    break
                elif line.startswith(":return:") or line.startswith(":returns:"):
                    insert_index = i
                    break

            if insert_index is not None:
                lines.insert(insert_index, ":rtype: {}".format(formatted_annotation))
        else:
            search_for = ":param {}:".format(arg_name)
            for i, line in enumerate(lines):
                if line.startswith(search_for):
                    lines.insert(i, ":type {}: {}".format(arg_name, formatted_annotation))
                    break


def setup(app):
    app.connect("autodoc-process-signature", process_signature)
    app.connect("autodoc-process-docstring", process_docstring)
    app.add_config_value("sphinx_autodoc_alias", {}, False)
    return dict(parallel_read_safe=True)
