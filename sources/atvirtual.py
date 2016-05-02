#!/usr/bin/env python3

from collections import OrderedDict
from copy import deepcopy

from cnorm import nodes
from pyrser.error import Severity, LocationInfo

import koocNorm
from atmember import atMember
from mangling import mangle, ClassType


class atVirtual(atMember):
    def doTrans(self, name):

        """
        a virtual function is a member function, it inherits from atmMember
        '@virtual' can only be used on functions
        if the function is already defined in a parent and that the signatures are matching, replace it in the vtable
        else, juste add the function to the vtable
        it adds the function definition to ast().classes[classname][2][mangled_func_name]
        """

        super(atVirtual, self).doTrans(name)
        if not isinstance(self._stmt._ctype, nodes.FuncType):
            self._diagnostic.notify(Severity.ERROR, "'@virtual' can only be used on functions",
                                    LocationInfo.from_stream(self._stream))
            raise self._diagnostic

        for key, value in self._ast().classes[name][2].items():
            if value._name == self._stmt._name and koocNorm.sameSignature(self._stmt, value) == True:
                cpy = deepcopy(self._stmt)
                mangle(self._ast(), name, cpy, ClassType.virtual)
                self._ast().classes[name][2] = self.modifyVtable(name, key, cpy._name, self._stmt)
                return

    def modifyVtable(self, className, oldKey, newKey, newValue):
        new = OrderedDict()
        for key, value in self._ast().classes[className][2].items():
            if key == oldKey:
                new[newKey] = newValue
            else:
                new[key] = value
        return new
