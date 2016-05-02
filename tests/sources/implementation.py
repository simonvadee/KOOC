#!/usr/bin/env python3

from copy import deepcopy
from weakref import ref

from cnorm import nodes
from pyrser.error import Severity, LocationInfo

import mangling
from atmember import atMember
from atvirtual import atVirtual


class atImplementation:
    def __init__(self, here, name, data, template, idx, diagnostic, stream):
        self.here = ref(here)
        self._name = name
        self.data = data
        self._idx = idx
        self._dict = None
        self._oldFuncs = []
        self._template = template
        self._diagnostic = diagnostic
        self._stream = stream

    def defineType(self):
        if self._name in self.here().modules:
            self._dict = self.here().modules[self._name]
            return True
        if self._name in self.here().classes:
            self._dict = self.here().classes[self._name]
            return True
        return False

    def getManglingFromName(self, name, index):
        definitions = self._dict[index].items()
        for key, value in definitions:
            if value._name == name:
                return key, value
        self._diagnostic.notify(Severity.ERROR,
                                "function : {} has never been defined in class {}".format(name, self._name),
                                LocationInfo.from_stream(self._stream))
        raise self._diagnostic

    def getMangling(self, elem, index):

        ok = True
        definitions = self._dict[index].items() if index != -1 else self._dict.items()

        for key, value in definitions:
            if value._name == elem._name and value._ctype._identifier == elem._ctype._identifier and len(
                    value._ctype._params) == len(elem._ctype._params):
                for (it1, it2) in zip(elem._ctype._params[1:], value._ctype._params[1:]):
                    if it1._ctype._identifier != it2._ctype._identifier:
                        ok = False
                    else:
                        ok = True
                if ok == True:
                    return key
        cpy_error = deepcopy(elem)
        delattr(cpy_error, 'body')
        self._diagnostic.notify(Severity.ERROR,
                                "function : {} has never been defined in class {}".format(str(cpy_error.to_c()),
                                                                                          self._name),
                                LocationInfo.from_stream(self._stream))
        raise self._diagnostic

    def checkExistsName(self, name, funcList):

        for elem in funcList:
            if elem._name == name:
                return True
        return False

    def checkExists(self, definition, funcList):

        for elem in funcList:
            if (type(definition._ctype) == type(elem._ctype)) and elem._name == definition._name:
                if elem._ctype._identifier != definition._ctype._identifier:
                    continue
                elif elem._ctype._specifier != definition._ctype._specifier:
                    continue
                elif mangling.get_pointers(elem._ctype) != mangling.get_pointers(definition._ctype):
                    continue
                return True
        return False

    def transfo(self):

        """
        for each declaration, check if it has been correctly defined, then transform instances of atMember/atVirtual
        it it's a class implementation, only functions can be defined
        """

        idx = -1
        for elem in self.data.body:
            idx += 1

            if isinstance(elem, nodes.Decl) and self._name in self.here().modules:
                if not self.checkExists(elem, self._dict.values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "unknown function {} in module {}".format(elem._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                self._oldFuncs.append(deepcopy(elem))
                elem._name = self.getMangling(elem, -1)


            elif (isinstance(elem, atMember) and not isinstance(elem, atVirtual)) or (
                            hasattr(elem, '_ctype') and isinstance(elem._ctype, nodes.FuncType) and len(
                            elem._ctype._params) > 0 and elem._ctype._params[
                    0]._ctype._identifier == self._name and isinstance(elem._ctype._params[0]._ctype._decltype,
                                                                       nodes.PointerType)):
                if hasattr(elem, '_stmt') and not self.checkExists(elem._stmt, self._dict[1].values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "unknown function {} in class {}".format(elem._stmt._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                elif hasattr(elem, '_name') and not self.checkExists(elem, self._dict[1].values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "unknown function {} in class {}".format(elem._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                if isinstance(elem, atMember):
                    ctype = nodes.PrimaryType(self._name)
                    ctype._decltype = nodes.PointerType()
                    arg = nodes.Decl('self', ctype)
                    if hasattr(elem._stmt._ctype, '_params'):
                        elem._stmt._ctype._params.insert(0, arg)
                    else:
                        elem._stmt._ctype._params = [arg]
                    if elem._stmt._name == 'init':
                        elem._stmt.body.body.insert(0, deepcopy(self._template[2].body.body[0]))
                        elem._stmt.body.body[0].expr.params[1].params[1].params[0].value += self._name
                    self._oldFuncs.append(deepcopy(elem._stmt))
                    elem._stmt._name = self.getMangling(elem._stmt, 1)
                    self.data.body[idx] = elem._stmt
                else:
                    self.data.body[idx] = elem


            elif isinstance(elem, atVirtual):
                if not self.checkExists(elem._stmt, self._dict[2].values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "unknown function {} in class {}".format(elem._stmt._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                ctype = nodes.PrimaryType(self._name)
                ctype._decltype = nodes.PointerType()
                arg = nodes.Decl('self', ctype)
                elem._stmt._ctype._params.insert(0, arg)
                self._oldFuncs.append(deepcopy(elem._stmt))
                elem._stmt._name = self.getMangling(elem._stmt, 2)
                self.data.body[idx] = elem._stmt


            elif self._name in self.here().classes and (
                hasattr(elem, '_ctype') and isinstance(elem._ctype, nodes.FuncType)):
                if not self.checkExists(elem, self._dict[0].values()):
                    self._diagnostic.notify(Severity.ERROR,
                                            "unknown function {} in class {}".format(elem._name, self._name),
                                            LocationInfo.from_stream(self._stream))
                    raise self._diagnostic
                self._oldFuncs.append(deepcopy(elem))
                elem._name = self.getMangling(elem, 0)


            else:
                self._diagnostic.notify(Severity.ERROR,
                                        "%s invalid definiton or declaration in class/module statement" % str(
                                            elem._name), LocationInfo.from_stream(self._stream))
                raise self._diagnostic
        return

    def addBuiltins(self):

        """
        if the function 'init' does not exists, create one
        create a 'new' function for each function 'init'
        create a 'alloc' and a 'delete' function
        """

        if not self.checkExistsName('init', self._oldFuncs):
            init = deepcopy(self._template[2])
            init._ctype._params[0]._ctype._identifier = self._name
            init.body.body[0].expr.params[1].params[1].params[0].value += self._name
            init._name = self.getMangling(init, 1)
            self.here().body.insert(self._idx + 1, init)

        for key, value in self._dict[1].items():
            if value._name == "init":
                new = deepcopy(self._template[0])
                new._ctype._identifier = self._name
                new.body.body[0]._ctype._identifier = self._name
                alloc_func = self.getManglingFromName('alloc', 0)
                new.body.body[1].expr.params[1].call_expr.value = alloc_func[0]
                new.body.body[2].expr.call_expr.value = self.getMangling(value, 1)
                paramList = [nodes.Id(elem._name) for elem in value._ctype.params[1:]]
                new.body.body[2].expr.params.extend(paramList)
                new._ctype._params = value._ctype._params[1:]
                new._name = self.getMangling(new, 0)
                self.here().body.insert(self._idx + 1, new)

        alloc = deepcopy(self._template[3])
        alloc._ctype._identifier = self._name
        alloc.body.body[0].expr.params[0].params[0]._identifier = self._name
        alloc._name = self.getMangling(alloc, 0)
        self.here().body.insert(self._idx + 1, alloc)

        delete = deepcopy(self._template[4])
        delete._ctype._params[0]._ctype._identifier = self._name
        delete._ctype._params[0]._ctype._specifier = 0
        delete._name = self.getMangling(delete, 1)
        delete.body.body[0].expr.call_expr.call_expr.params[0].params[0]._identifier = '_vtable_' + self._name
        clean_func = self.getManglingFromName('clean', 2)
        delete.body.body[0].expr.call_expr.params[0].value = clean_func[0]
        delete.body.body[0].expr.params[0].params[0]._identifier = clean_func[1]._ctype._params[0]._ctype._identifier
        self.here().body.insert(self._idx + 1, delete)

        name_of_interface = deepcopy(self._template[10])
        name_of_interface._ctype._params[0]._ctype._identifier = self._name
        name_of_interface.body.body[0].expr.value = '\"' + str(self._name) + '\"'
        name_of_interface._name = self.getMangling(name_of_interface, 1)
        self.here().body.insert(self._idx + 1, name_of_interface)

        if len(self._dict[4]) == 2:
            for index in range(5, 10):
                builtin = deepcopy(self._template[index])
                builtin._ctype._params[0]._ctype._identifier = self._name
                builtin._ctype._params[0]._ctype._specifier = 0
                builtin._name = self.getMangling(builtin, 2)
                if index == 8:
                    builtin.body.body[0].condition.params[0].params[1].value = '\"' + self._name + '\"'
                elif index == 6:
                    builtin.body.body[0]._ctype._decltype._expr.value = str(len(self._dict[4]) + 1)
                    for parent in self._dict[4]:
                        builtin.body.body[0]._assign_expr.body.insert(0, nodes.Literal('\"' + parent + '\"'))
                self.here().body.insert(self._idx + 1, builtin)

    def declVtable(self):

        vtable = deepcopy(self._template[1])
        vtable._name += self._name
        vtable._ctype._identifier += self._name
        for key, value in self._dict[2].items():
            vtable._assign_expr.body.append(nodes.Id(key))
        self.here().body.insert(self._idx + 1, vtable)
        self._idx += 1

    def doTrans(self):

        """
        check if its a MODULE or CLASS implementation
        transform MEMBER and VIRTUAL instances
        insert an instance of the class's vtable and assign the right func ptr to its fields
        check if func previously defined
        module -> insert vars, then funcs
        class -> insert vars, then builtins, then users's defined funcs
        """

        if self.defineType() == False:
            self._diagnostic.notify(Severity.ERROR, "type '%s' has never been defined" % self._name,
                                    LocationInfo.from_stream(self._stream))
            raise self._diagnostic

        self.transfo()

        if self._name in self.here().classes:
            self.declVtable()

        for elem in self.data.body:
            if hasattr(elem, '_ctype') and not isinstance(elem._ctype, nodes.FuncType):
                self._diagnostic.notify(Severity.ERROR, "%s is not a function" % elem._name,
                                        LocationInfo.from_stream(self._stream))
                raise self._diagnostic
            self.here().body.insert(self._idx + 1, elem)

        if self._name in self.here().classes:
            self.addBuiltins()

        self._dict = self._dict if self._name in self.here().modules else self._dict[0]

        for key, value in self._dict.items():
            if not isinstance(value._ctype, nodes.FuncType):
                cpy = deepcopy(value)
                cpy._name = key
                self.here().body.insert(self._idx + 1, cpy)
