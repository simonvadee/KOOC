#!/usr/bin/env python3

from cnorm import nodes
from enum import Enum


class ClassType(Enum):
    member = 1
    virtual = 2
    default = 3


# specifiers : n[0]  -> normal,
#              st[1] -> struct,
#              u[2]  -> union,
#              l[3]  -> long,
#              ll[4] -> long long,
#              sh[5] -> short
#
#
#   ---

arrayMangle = {'_specifier': ["n", "st", "u", "e", "l", "ll", "sh"],
               }

def countParams(interMangled) :
    count = 0
    for elem in interMangled.split('.') :
        if elem not in arrayMangle['_specifier'] and elem not in ['p'] :
            count += 1
    return count

def mangleMember(ast, rawName, decl):
    name = "__mem__" + str(len(rawName)) + rawName
    memberName = "@@" + decl._name
    mangleCtype(ast, name, decl, "?@" + rawName, memberName)


def mangleVirtual(ast, rawName, decl):
    name = "__vi__" + str(len(rawName)) + rawName
    virtualName = "?@@" + decl._name
    mangleCtype(ast, name, decl, "?@" + rawName, virtualName)


def mangleAsModule(ast, rawName, decl):
    name = "_" + str(len(rawName)) + rawName
    mangleCtype(ast, name, decl, "?@" + rawName, decl._name)


def mangleModule(ast, rawName, decl):
    name = "_" + str(len(rawName)) + rawName
    moduleName = "@" + rawName
    newChain = ast.mangle.new_child();
    if not moduleName in ast.mangle:
        ast.mangle[moduleName] = {}
    mangleCtype(ast, name, decl, moduleName, decl._name)


def mangleCtype(ast, name, decl, scope, identifier):
    if hasattr(decl, '_ctype'):
        if not identifier in ast.mangle[scope]:
            ast.mangle[scope][identifier] = []
        name += str(len(decl._name)) + decl._name
        extend = getExtend(decl._ctype)
        if isinstance(decl._ctype, nodes.FuncType):
            for param in decl._ctype._params:
                extend += '.' + getExtend(param._ctype)
        if not extend in ast.mangle[scope][identifier]:
            ast.mangle[scope][identifier].append(extend)
        name += "_" + str(ast.mangle[scope][identifier].index(extend))
        decl._name = name


classDict = {
    ClassType.member: mangleMember,
    ClassType.virtual: mangleVirtual,
    ClassType.default: mangleAsModule
}


def checkExistsClass(rawName, ast):
    className = "?@" + rawName
    if not className in ast.mangle:
        ast.mangle[className] = {}


def mangle(ast, rawName, decl, sType=ClassType.default):
    mangleClass(ast, rawName, decl, sType) if rawName in ast.classes else mangleModule(ast, rawName, decl)


def mangleClass(ast, rawName, decl, classType):
    checkExistsClass(rawName, ast)
    classDict[classType](ast, rawName, decl)


def get_pointers(node):
    ret = ''
    if hasattr(node, '_decltype') and isinstance(node._decltype, nodes.PointerType):
        ret += 'p.'
        ret += get_pointers(node._decltype)
    return ret


def getExtend(node):
    ret = get_pointers(node)
    ret += arrayMangle['_specifier'][node._specifier] + '.' + node._identifier
    return ret
