#!/usr/bin/env python3

from copy import deepcopy
from weakref import ref

from cnorm import nodes

import mangling
from atBrackets import atBrackets
from solveLiteral import SolveLiteral
from cnorm.parsing.declaration import Declaration
from pyrser.passes import to_yml


class TypeSystem:
    def __init__(self, ast, templateVt):
        self.ast = ref(ast)
        self.templateVt = templateVt
        self.expr = {
            "Binary": self.solveBinary,
            "Unary": self.solveUnary
        }

    def solveExpr(self):
        for elem in self.ast().body:
            if hasattr(elem, 'body'):
                for index, decl in enumerate(elem.body.body):
                    if isinstance(decl, nodes.ExprStmt) and self.isKooc(decl):
                        if isinstance(decl.expr, nodes.Func) and hasattr(decl.expr, 'call_expr') and isinstance(
                                decl.expr.call_expr, atBrackets):
                            newDecl = self.solveFunc(decl, decl.expr, elem.body.body)
                            elem.body.body[index] = deepcopy(newDecl)
                        else:
                            self.expr[type(decl.expr).__name__](decl.expr, elem.body.body)

    def solveFunc(self, decl, funcDecl, ref, binary=False):
        listMangledParams = []
        for param in funcDecl.params:
            if isinstance(param, nodes.Id):
                listMangledParams.append(self.solveId(param, ref))
        atBrack = funcDecl.call_expr
        mangleName = self.findFunc(decl, atBrack, funcDecl.params, listMangledParams, binary, ref)
        funcDecl.call_expr = nodes.Id(mangleName)
        if atBrack.isVirtual :
            newDecl = deepcopy(self.templateVt)
            newDecl.expr.call_expr.params[0].value = mangleName
            newDecl.expr.call_expr.call_expr.params[0].params[0]._identifier = '_vtable_' + atBrack.scope
            newDecl.expr.call_expr.call_expr.params[0].params[1].call_expr.value = atBrack.instance
            newDecl.expr.params = funcDecl.params
            return newDecl
        return decl

    def getRealMangledFuncName(self, atBrack, realScope):
        arrayTry = ['@@', '?@@']
        if atBrack.funcName in self.ast().mangle[realScope]:
            return atBrack.funcName
        for index, prefix in enumerate(arrayTry):
            if prefix + atBrack.funcName in self.ast().mangle[realScope]:
                if index == 0:
                    atBrack.isMember = True
                if index == 1:
                    atBrack.isVirtual = True
                return prefix + atBrack.funcName
        return ''

    def findFunc(self, decl, atBrack, paramsFunc, listMangledParams, binary, ref):
        realScope = self.determineMangleScope(atBrack, ref)
        if realScope == '':
            raise Exception(atBrack.scope + ' is not defined')
        realFuncName = self.getRealMangledFuncName(atBrack, realScope)
        if realFuncName:
            # Si on ne connait pas le retour de l'expression (type Unary, Exprcall, ...)
            mangleParamsName = ''
            if atBrack.isMember or atBrack.isVirtual:
                # Member et Virtual : ajout de l'instance en premier parametre
                firstParamForMember = nodes.Decl('self')
                firstParamForMember._ctype = nodes.PrimaryType(atBrack.scope)
                firstParamForMember._ctype._storage = 0
                firstParamForMember._ctype._decltype = nodes.PointerType()
                paramsFunc.insert(0, nodes.Id(atBrack.instance))
                mangleParamsName = mangling.getExtend(firstParamForMember._ctype)

            for param in listMangledParams:
                if not mangleParamsName and param != None :
                    mangleParamsName = mangling.getExtend(param)
                elif param != None :
                    mangleParamsName += '.' + mangling.getExtend(param)

            funcList = self.ast().mangle[realScope][realFuncName]
            if mangleParamsName != '' and not binary :
                for elem in funcList:
                    if elem.find(mangleParamsName) != -1 and mangling.countParams(elem) - 1 == mangling.countParams(mangleParamsName) :
                        mangleFuncName = self.getMangledFuncName(atBrack, funcList, elem, atBrack.scope)
                        return mangleFuncName
            elif not binary :
                mangleFuncName = self.getMangledFuncName(atBrack, funcList, funcList[0], atBrack.scope)
                return mangleFuncName

            # Si on a le retour de l'expression BinaryExpr
            if binary:
                if 'retType' in binary[0] :
                    extend = mangling.getExtend(binary[0]['retType'])
                    if mangleParamsName :
                        tmp = extend + '.' + mangleParamsName
                    else :
                        tmp = extend
                    if tmp in funcList :
                        mangleFuncName = self.getMangledFuncName(atBrack, funcList, tmp, atBrack.scope)
                        return mangleFuncName
                if 'inter' in binary[0]:
                    for retType in binary[0]['inter']:
                        for mangledParams in funcList :
                            if mangleParamsName :
                                tmp = retType + '.' + mangleParamsName
                            else :
                                tmp = retType
                            if tmp in funcList :
                                mangleFuncName = self.getMangledFuncName(atBrack, funcList, tmp, atBrack.scope)
                                mangleLeftName = self.solveInter(binary[0]['atBrack'],
                                                                 binary[0]['inter'],
                                                                 retType)
                                decl.params[binary[0]['index']] = nodes.Id(mangleLeftName)
                                return mangleFuncName
        return ""

    # Only if elem in inter :
    def solveInter(self, atBrack, inter, elem):
        if atBrack.param != None:
            mangleName = ('_'
                          + str(len(atBrack.scope))
                          + atBrack.scope
                          + str(len(atBrack.param))
                          + atBrack.param
                          + '_'
                          + str(inter.index(elem)))
            return mangleName

    def getMangledFuncName(self, atBrack, funcList, internMangledFunc, realScopeName):
        mangleFuncName = '_'
        if atBrack.isVirtual:
            mangleFuncName += '_vi__'
        elif atBrack.isMember:
            mangleFuncName += '_mem__'
        mangleFuncName += (str(len(realScopeName))
                           + realScopeName
                           + str(len(atBrack.funcName))
                           + atBrack.funcName
                           + '_'
                           + str(funcList.index(internMangledFunc)))
        return mangleFuncName

    def solveUnary(self, decl, ref):
        # find in current blockstatement
        ctype = None
        for elem in ref:
            if hasattr(elem, '_name') and decl.params[0].value == elem._name:
                ctype = deepcopy(elem._ctype)
        # find in global scope
        for elem in self.ast().body:
            if hasattr(elem, '_name') and decl.params[0].value == elem._name:
                ctype = elem._ctype
        if ctype and hasattr(decl, 'call_expr') and decl.call_expr.value == '&':
            newElem = nodes.PointerType()
            newElem._decltype = ctype._decltype
            ctype._decltype = newElem
        return ctype

    def solveId(self, decl, ref):
        # find in current blockstmt
        ctype = None
        for elem in ref:
            if hasattr(elem, '_name') and decl.value == elem._name:
                ctype = elem._ctype
        # find in global scope
        for elem in self.ast().body:
            if hasattr(elem, '_name') and decl.value == elem._name:
                ctype = elem._ctype
        return ctype

    def determineRealParam(self, atBrack, ref, realScope) :
        arrayTry = ['@@']
        for elem in arrayTry:
            if (elem + atBrack.param) in self.ast().mangle[realScope] :
                atBrack.isMember = True
                return elem + atBrack.param
        return atBrack.param
        
    def solveAtBrackets(self, root, index, decl, ref, left):
        realScope = self.determineMangleScope(decl, ref)
        save = {}
        if realScope == '':
            raise Exception(decl.scope + ' is not defined')
        if decl.typedef != None:
            mangleName = self.findCast(decl, ref)
            root.params[index] = nodes.Id(mangleName)
            return root.params[index]
        realParam = self.determineRealParam(decl, ref, realScope)
        if realParam in self.ast().mangle[realScope]:
            inter = self.ast().mangle[realScope][realParam]
            save = {'index': index, 'atBrack': decl, 'inter': inter}
        if left and 'atBrack' in left[0]:
            if save:
                leftMangledName = self.solveInterBrack(left[0]['inter'], inter, left[0]['atBrack'])
                root.params[left[0]['index']] = nodes.Id(leftMangledName)
                rightMangledName = self.solveInterBrack(inter, left[0]['inter'], save['atBrack'])
                root.params[index] = nodes.Id(rightMangledName)
        if left and 'retType' in left[0] :
            decl.typedef = left[0]['retType']
            mangleName = self.findCast(decl, ref, realParam)
            if decl.isMember :
                newArrow = nodes.Arrow(nodes.Id(decl.instance), [nodes.Id(mangleName)])
                root.params[index] = newArrow
            else :
                root.params[index] = nodes.Id(mangleName)
            return root.params[index]
        return save

    def solveInterBrack(self, A, B, atBrack):
        # intersection de 2 ensembles de mangle A et B, l'expression mangle voulue est definie par l'expression kooc donne en param
        # le premier ensemble A correspond a atBrack
        mangledName = ''
        interSol = list(set(A).intersection(B))
        if interSol:
            # On choisit le premier element de l'intersection si il existe
            mangledName = self.solveInter(atBrack, A, interSol[0])
        return mangledName

    def solveBinary(self, decl, ref):
        # creation de left et right
        left = []
        for index, elem in enumerate(decl.params):
            if isinstance(elem, atBrackets):
                left.append(self.solveAtBrackets(decl, index, elem, ref, left))
            if isinstance(elem, nodes.Literal):
                if left and 'inter' in left[0]:
                    inter = left[0]['inter']
                else:
                    inter = None
                sl = SolveLiteral(inter)
                if left and 'atBrack' in left[0]:
                    left[0]['atBrack'].typedef = sl.parse(elem.value).typ
                    mangleName = self.findCast(left[0]['atBrack'], ref)
                    decl.params[left[0]['index']] = nodes.Id(mangleName)
                    return;
                else :
                    left.append({'retType':sl.parse(elem.value).typ})
            if isinstance(elem, nodes.Unary):
                if left and 'atBrack' in left[0]:
                    left[0]['atBrack'].typedef = self.solveUnary(elem, ref)
                    mangleName = self.findCast(left[0]['atBrack'], ref)
                    decl.params[left[0]['index']] = nodes.Id(mangleName)
                    return;
                else :
                    left.append({'retType':self.solveUnary(elem, ref)})
            if isinstance(elem, nodes.Id):
                if left and 'atBrack' in left[0]:
                    left[0]['atBrack'].typedef = self.solveId(elem, ref)
                    mangleName = self.findCast(left[0]['atBrack'], ref)
                    decl.params[left[0]['index']] = nodes.Id(mangleName)
                    return;
                else :
                    left.append({'retType':self.solveId(elem, ref)})
            if isinstance(elem, nodes.Func):
                if left and 'atBrack' in left[0]:
                    newDecl = self.solveFunc(decl, elem, ref, left)
                else :
                    newDecl = self.solveFunc(decl, elem, ref, left)
                    elem[index] = newDecl

    def isKooc(self, expr):
        if hasattr(expr, 'params') and expr.params :
            for elem in expr.params :
                if isinstance(elem, atBrackets) :
                    return True
        if hasattr(expr, 'expr') and hasattr(expr.expr, 'params'):
            for elem in expr.expr.params:
                if isinstance(elem, atBrackets):
                    return True
                if isinstance(elem, nodes.Func) and isinstance(elem.call_expr, atBrackets) :
                    return True
        if hasattr(expr, 'expr') and hasattr(expr.expr, 'call_expr'):
            if isinstance(expr.expr.call_expr, atBrackets):
                return True
        return False

    def findCast(self, elem, ref, realParam = False):
        realScope = self.determineMangleScope(elem, ref)
        if realParam :
            tmp = realParam
        else :
            tmp = elem.param
        if realScope == '':
            raise Exception(elem.scope + ' is not defined')
        if tmp in self.ast().mangle[realScope]:
            attr = self.ast().mangle[realScope][tmp]
            toFind = mangling.getExtend(elem.typedef)
            if toFind in attr:
                mangleName = '_'
                if elem.isMember :
                    mangleName += '_mem__'
                mangleName += (str(len(elem.scope))
                               + elem.scope
                               + str(len(elem.param))
                               + elem.param
                               + '_'
                               + str(attr.index(toFind)))
                return mangleName
        raise Exception(elem.param + ' is not defined in ' + elem.scope)

    def determineMangleScope(self, atBrack, ref):
        arrayTry = ['@', '?@']
        for elem in arrayTry:
            if (elem + atBrack.scope) in self.ast().mangle:
                return elem + atBrack.scope
        # gestion de classes, recherche de type reel pour la gestion des appels d'instances, recherche de _name dans ref (local & global)
        for elem in ref:
            if (hasattr(elem, '_name') and elem._name == atBrack.scope):
                atBrack.instance = atBrack.scope
                atBrack.scope = elem._ctype._identifier
                return '?@' + elem._ctype._identifier
        return ''
