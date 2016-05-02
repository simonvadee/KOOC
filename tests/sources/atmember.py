#!/usr/bin/env python3

from weakref import ref

from cnorm import nodes
from pyrser.error import Severity


class atMember:
    def __init__(self, ast, stmt, idx, diagnostic, stream):
        self._ast = ref(ast)
        self._stmt = stmt
        self._idx = idx
        self._diagnostic = diagnostic
        self._stream = stream

    def doTrans(self, name):

        """
        if its a function definition, add a first parameter (ptr on the instance) 'self'
        """

        if not hasattr(self._stmt, '_ctype') or (
            not isinstance(self._stmt._ctype, nodes.FuncType) and not isinstance(self._stmt._ctype,
                                                                                 nodes.PrimaryType)) or hasattr(
                self._stmt, "_assign_expr"):
            self._diagnostic.notify(Severity.ERROR, "wrong usage of '@member'")
            raise self._diagnostic

        if isinstance(self._stmt._ctype, nodes.FuncType):
            ctype = nodes.PrimaryType(name)
            ctype._decltype = nodes.PointerType()
            arg = nodes.Decl('self', ctype)
            if hasattr(self._stmt._ctype, '_params'):
                self._stmt._ctype._params.insert(0, arg)
            else:
                self._stmt._ctype._params = [arg]
        return
