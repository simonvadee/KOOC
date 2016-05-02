#!/usr/bin/env python3

from collections import OrderedDict
from copy import deepcopy

from cnorm import nodes
from pyrser.error import Severity

from atmember import atMember
from atvirtual import atVirtual
from mangling import mangle, ClassType
from module import atModule


class atClass(atModule):
    def __init__(self, rootref, body, name, data, idx, template, parent, diagnostic, stream):
        super(atClass, self).__init__(rootref, body, name, data, idx, diagnostic, stream)
        self._template = template
        self._parent = parent
        self._corresp = {0: ClassType.default, 1: ClassType.member, 2: ClassType.virtual, 3: ClassType.member}

    def checkExistsName(self, name, funcList):
        for elem in funcList:
            if isinstance(elem._ctype, nodes.FuncType) and elem._name == name:
                return True
        return False

    def addDict(self, elem, dic, extern=True):
        if dic != 2 and self.checkExists(elem, self._ast().classes[self._name][dic].values()):
            self._diagnostic.notify(Severity.ERROR, "{} already exists in class {}".format(elem._name, self._name))
            raise self._diagnostic
        elif elem._ctype._storage == 5:
            self._diagnostic.notify(Severity.ERROR, "'inline' keyword forbidden class definition")
            raise self._diagnostic
        manglingType = self._corresp[dic]
        cpy = deepcopy(elem)
        mangle(self._ast(), self._name, cpy, manglingType)
        if extern:
            self.insertExtern(cpy)
        self._ast().classes[self._name][dic][cpy._name] = elem

    def initClass(self):

        """
        add 'Object' as parent's name in _ast().classes[className][4]
        add tons of builtins functions (kinda boring)
        """

        self._ast().classes[self._name][4].append('Object')
        self._ast().classes[self._name][4].append(self._name)
        self._body.body.insert(self._idx + 1, self._template[0])
        self._idx += 1
        self._body.body.insert(self._idx + 1, self._template[1])
        self._idx += 1
        for elem in self._template[8:]:
            cpy = deepcopy(elem)
            cpy._ctype._params[0]._ctype._identifier = self._name
            self.addDict(cpy, 2, True)
            self.addDict(cpy, 3, False)

    def inherits(self):

        """
        if the class does inherits from another, inherits from Object*
        add members variables of the parent ( -> classes[parentName][1]) in classes[ownName][3]
        add virtuals functions of the parent (-> classes[parentName][2]) in classes[ownName][2]
        """

        if not self._parent:
            self.initClass()
            return

        elif self._parent not in self._ast().classes:
            self._diagnostic.notify(Severity.ERROR, "{} does not exists".format(self._parent))
            raise self._diagnostic

        for parent in self._ast().classes[self._parent][4]:
            self._ast().classes[self._name][4].append(parent)
        self._ast().classes[self._name][4].append(self._name)

        for key, value in self._ast().classes[self._parent][1].items():
            self._ast().classes[self._name][3][key] = value

        for key, value in self._ast().classes[self._parent][2].items():
            self._ast().classes[self._name][2][key] = value


    def createVtable(self):

        """
        create the vtable that contains functions ptr defined in classes[ownName][2]
        """

        vtable = deepcopy(self._template[6])
        vtable._ctype._identifier += self._name

        for key, value in self._ast().classes[self._name][2].items():
            ptrfunc = deepcopy(value)
            ctype = deepcopy(value._ctype)
            ptrfunc._name = key
            ptrfunc._ctype = nodes.PrimaryType(ctype._identifier)
            ptrfunc._ctype._decltype = nodes.PointerType()
            ptrfunc._ctype._decltype._decltype = nodes.ParenType()
            ptrfunc._ctype._decltype._decltype._decltype = ctype._decltype
            ptrfunc._ctype._decltype._decltype._params = ctype._params
            vtable._ctype.fields.append(ptrfunc)

        return vtable

    def createStruct(self, vtable_identifier):

        """
        create a new struct that contains (in that exact order):
        a ptr on the vtable we just defined
        members variables of the parent
        member variable of the actual class
        """
        ctype = nodes.ComposedType(self._name + '_mangled')
        ctype.fields = []
        ctype._specifier = 1

        vtable_ptr = nodes.Decl("VT")
        vtable_ptr._ctype._identifier = "void"
        vtable_ptr._ctype._decltype = nodes.PointerType()
        ctype.fields.append(vtable_ptr)

        for key, value in self._ast().classes[self._name][3].items():
            if not isinstance(value._ctype, nodes.FuncType):
                cpy = deepcopy(value)
                cpy._name = key
                ctype.fields.append(cpy)

        for key, value in self._ast().classes[self._name][1].items():
            if not isinstance(value._ctype, nodes.FuncType):
                cpy = deepcopy(value)
                cpy._name = key
                ctype.fields.append(cpy)

        struct = nodes.Decl('', ctype)
        return struct

    def addBuiltins(self):

        """
        if not already, defined a 'init' function
        define a 'alloc' and 'delete' function
        define a 'new' function for each 'init'
        """

        if not self.checkExistsName('init', self._ast().classes[self._name][1].values()):
            init = deepcopy(self._template[5])
            init._ctype._params[0]._ctype._identifier = self._name
            self.addDict(init, 1)

        alloc = deepcopy(self._template[2])
        alloc._ctype._identifier = self._name
        self.addDict(alloc, 0)

        delete = deepcopy(self._template[3])
        delete._ctype._params[0]._ctype._identifier = self._name
        self.addDict(delete, 1)

        name_of_interface = deepcopy(self._template[7])
        name_of_interface._ctype._params[0]._ctype._identifier = self._name
        self.addDict(name_of_interface, 1)

        for key, value in self._ast().classes[self._name][1].items():
            if value._name == "init":
                new = deepcopy(self._template[4])
                new._ctype._identifier = self._name
                new._ctype._params = value._ctype._params[1:]
                self.addDict(new, 0)

    def doTrans(self):

        """
        if double definition raise
        inherits from baseObject or other class
        add builtins functions
        fill self._ast().classes[className] as follows :
        -if non member var/func -> add in [0]
        -if member var/func -> add in [1]
        -if virtual var/func -> add in [1] and [2]
        create vtable
        create structure with the class member vars
        """

        if self._name in (self._ast().classes or self._ast().modules):
            self._diagnostic.notify(Severity.ERROR, "%s is already a class or a module" % self._name)
            raise self._diagnostic

        self._ast().classes[self._name] = [{}, {}, OrderedDict(), {}, []]
        self.inherits()

        for elem in self._stmt.body:
            if isinstance(elem, nodes.Decl):
                if isinstance(elem._ctype, nodes.FuncType) and len(elem._ctype._params) > 0 and elem._ctype._params[
                    0]._ctype._identifier == self._name and isinstance(elem._ctype._params[0]._ctype._decltype,
                                                                       nodes.PointerType):
                    self.addDict(elem, 1)
                else:
                    if not isinstance(elem._ctype, nodes.FuncType) and not hasattr(elem, '_assign_expr'):
                        self._diagnostic.notify(Severity.ERROR,
                                                "missing assignation to variable {} in class {}".format(elem._name,
                                                                                                        self._name))
                        raise self._diagnostic
                    self.addDict(elem, 0)
            elif isinstance(elem, atMember) and not isinstance(elem, atVirtual):
                elem.doTrans(self._name)
                self.addDict(elem._stmt, 1, True if isinstance(elem._stmt._ctype, nodes.FuncType) else False)
            elif isinstance(elem, atVirtual):
                elem.doTrans(self._name)
                self.addDict(elem._stmt, 2, True)

        self.addBuiltins()

        vtable = self.createVtable()
        self._body.body.insert(self._idx + 1, vtable)

        struct = self.createStruct(vtable._ctype._identifier)
        self._body.body.insert(self._idx + 2, struct)
