#!/usr/bin/env python3

from copy import deepcopy
from weakref import ref

from cnorm import nodes
from pyrser.error import Severity, LocationInfo

import koocNorm
from mangling import mangleModule, get_pointers


class atModule:
    def __init__(self, rootref, body, moduleName, stmt, idx, diagnostic, stream):
        self._ast = ref(rootref) if rootref else ref(body)
        self._body = body
        self._name = moduleName
        self._stmt = stmt
        self._idx = idx
        self._diagnostic = diagnostic
        self._stream = stream
        for elem in self._stmt.body:
            if hasattr(elem, '_ctype') and elem._ctype._storage == 2:
                self._body.types[elem._name] = ref(elem)

    def checkExists(self, func, funcList):
        for elem in funcList:
            if (type(elem._ctype) == type(func._ctype)) and elem._name == func._name:
                if isinstance(elem._ctype, nodes.FuncType) and not koocNorm.sameSignature(elem, func):
                    continue
                elif elem._ctype._identifier != func._ctype._identifier:
                    continue
                elif elem._ctype._specifier != func._ctype._specifier:
                    continue
                elif get_pointers(elem._ctype) != get_pointers(func._ctype):
                    continue
                return True
        return False

    def insertExtern(self, elem):
        cpy = deepcopy(elem)
        if hasattr(cpy, '_assign_expr'):
            cpy._ctype._storage = 4
            delattr(cpy, '_assign_expr')
        self._body.body.insert(self._idx + 1, cpy)
        self._idx += 1

    def doTrans(self):

        """
        for each module, we create a dict that maps the (mangled) name to the definition
        if we find a definition which appends not to be a (function) or a (variable WITHOUT an assignation) : raise
        we map this dict to a name in an other dict called "modules" that will always be available at the tree's origin
        """

        module = {}
        for elem in self._stmt.body:
            if hasattr(elem, '_assign_expr') or isinstance(elem._ctype, nodes.FuncType):
                if self.checkExists(elem, module.values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "ERROR : '{}' already exists in module {}".format(elem._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                elif elem._ctype._storage == 5:
                    self._diagnostic.notify(Severity.ERROR, "'inline' keyword forbidden in module definition",
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                cpy = deepcopy(elem)
                mangleModule(self._ast(), self._name, cpy)
                module[cpy._name] = elem
                self.insertExtern(cpy)
            else:
                if elem._ctype._specifier == 1 or elem._ctype._specifier == 2 or elem._ctype._specifier == 3 or elem._ctype._storage == 2:
                    self._body.body.insert(self._idx + 1, elem)
                else:
                    self._diagnostic.notify(Severity.ERROR,
                                            "Declaration is nor a variable with assignation nor a function",
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic

        self._ast().modules[self._name] = module
