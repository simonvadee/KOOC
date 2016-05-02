#!/usr/bin/env python3

from collections import ChainMap
from copy import deepcopy
from os import environ
from weakref import ref

from cnorm import nodes
from cnorm.parsing.declaration import Declaration
from cnorm.parsing.expression import Expression
from pyrser import error
from pyrser import meta
from pyrser.grammar import Grammar
from pyrser.parsing.node import Node

from atBrackets import atBrackets
from atclass import atClass
from atmember import atMember
from atvirtual import atVirtual
from implementation import atImplementation
from include import atImport
from mangling import get_pointers
from module import atModule
from typeSystem import TypeSystem

class KoocNorm(Grammar, Declaration, Expression):
    def __init__(self, filename, path, importFiles=[], root=None):
        Grammar.__init__(self)
        Declaration.__init__(self)
        self.importFiles = importFiles
        self._rootref = root
        self._filename = filename
        self._path = path
        if 'KOOCPATH' not in environ:
            self.diagnostic.notify(error.Severity.ERROR, "please do 'export KOOCPATH=/home/$USER/rendu/kooc/.conf'")
            raise self.diagnostic
        factory = Declaration()
        res = factory.parse_file(environ["KOOCPATH"] + '/builtins_class.kp')
        self._classTemplate = deepcopy(res.body)
        res = factory.parse_file(environ["KOOCPATH"] + '/builtins_implem.kp')
        self._implemTemplate = deepcopy(res.body)

    entry = "translation_unit"
    grammar = """
    translation_unit =
    [
        @ignore("C/C++")
        [
                __scope__:current_block
                #new_root(_, current_block)
                #build_ast(_)
                [
                        declaration
                ]*
        ]
        Base.eof
    ]

    primary_expression = [
                           Declaration.primary_expression:>_
                           | atBrackets:>_
                         ]
    
    atBrackets = [
                   #initNodeParams(_)
                   ["@!(" type_name:t #update_type(_, t) ')' ]?
                   '['
                   [
                      identifiant_module_instance:scope
                      [
                         [identifiant_fonction:attr param_list:pl #addParams(_, attr, pl)]
                         | [identifiant_variable:attr #addParams(_, attr)]
                      ]
                   ]
                   ']'
                   #addBrackets(_, scope)
                ]
    
    param_list = [ #initParamsList(_) [':' assignement_expression:a #addParamList(_, a) ]* ]

    identifiant_module_instance = [ id:>_ ]

    identifiant_fonction = [ [id:function_name] #addFuncName(_, function_name) ]

    identifiant_variable = [ "." [id:var] #addAttr(_, var)]

    declaration =
    [
        Declaration.declaration |
        atImport |
        atModule |
        atClass |
        atImplementation
    ]

    atImport =
    [
        "@import" '"' header:file '"'
        #addInclude(current_block, file)
    ]

    header =
    [
        id  "." id
    ]

    atClass =
    [
        "@class"
        id:className #addTypedef(current_block, className)
        [':'? id?:parent]
        class_statement:stmt
        #addClass(current_block, className, stmt, parent)
    ]

    class_statement =
    [
        '{'
        __scope__:current_block
        #new_blockstmt(_, current_block)
        [
                line_of_code |
                atMember |
                atVirtual
        ]*
        '}'
    ]

    atMember =
    [
        [ "@member" compound_statement:data #addMultipleMembers(current_block, data)] |
        [ "@member" member_statement:stmt #addMember(current_block, stmt, 1)]
    ]

    member_statement =
    [
    __scope__:current_block
    #new_blockstmt(_, current_block)
    line_of_code
    ]
    
    atVirtual =
    [
        [ "@virtual" compound_statement:data #addMultipleVirtuals(current_block, data)] |
        [ "@virtual" virtual_statement:stmt  #addVirtual(current_block, stmt, 1)]
    ]

    virtual_statement =
    [
    __scope__:current_block
    #new_blockstmt(_, current_block)
    line_of_code
    ]

    
    atModule =
    [
        "@module"
        id:moduleName
        Statement.compound_statement:stmt
        #addModule(current_block, moduleName, stmt)
    ]

    atImplementation =
    [
        "@implementation"
        id:i
        implem_statement:st
        #addImplementation(current_block, i, st)
    ]

    implem_statement =
    [
        '{'
        __scope__:current_block
        #new_blockstmt(_, current_block)
                [
                line_of_code |
                atVirtual |
                atMember
                ]*
        '}'
    ]
    
    """


@meta.hook(KoocNorm)
def build_ast(self, ast):
    if self._rootref is None:
        ast.units = {}
        ast.modules = {}
        ast.mangle = ChainMap()
        ast.classes = {}
        self._rootref = ast
    else:
        ast.units = self._rootref.units
        ast.modules = self._rootref.modules
        ast.mangle = self._rootref.mangle
        ast.classes = self._rootref.classes
    return True


@meta.hook(KoocNorm)
def addInclude(self, ast, filename):
    """
    update 'importFiles' to avoid double inclusion
    do not wait til the parsing is done to transform atInclude -> need to add types definitons to the tree
    """
    
    if self.value(filename) == self._filename:
        self.diagnostic.notify(error.Severity.ERROR, '"%s": cannot self include' % self.value(filename))
        return False
    inc = atImport(ast.ref, self.value(filename), self._path, len(ast.ref.body), self.importFiles, self.diagnostic,
                   self._stream)
    if not (inc.checkExists()):
        self.diagnostic.notify(error.Severity.ERROR, '"%s": file does not exist' % self.value(filename))
        return False
    ast.ref.body.append(inc)
    try:
        inc.doTrans()
    except error.Diagnostic as e:
        print (e)
        return False
    return True


@meta.hook(KoocNorm)
def initNodeParams(self, ast):
    ast.typ = None
    ast.attr = None
    ast.brack = None
    return True


@meta.hook(KoocNorm)
def initParamsList(self, ast):
    ast.params = []
    return True


@meta.hook(KoocNorm)
def addParams(self, ast, attr, params=None):
    ast.attr = attr
    if params == None:
        ast.params = []
    else:
        ast.params = params.params
    return True


@meta.hook(KoocNorm)
def addParamList(self, ast, param):
    ast.params.append(param)
    return True


@meta.hook(KoocNorm)
def update_type(self, ast, typ):
    decl = Declaration()
    ast.typ = decl.parse(self.value(typ) + ';').body[0]._ctype
    return True

@meta.hook(KoocNorm)
def addAttr(self, ast, attr):
    ast.func = None
    ast.attr = self.value(attr)
    return True

@meta.hook(KoocNorm)
def addFuncName(self, ast, func_name):
    ast.func = self.value(func_name)
    ast.attr = None
    return True


@meta.hook(KoocNorm)
def addBrackets(self, ast, scope):
    ast.brack = atBrackets(ast.typ, self.value(scope), ast.attr.attr, ast.attr.func)
    if (ast.attr.func != None):
        ast.set(nodes.Func(ast.brack, ast.params))
    return True

@meta.hook(KoocNorm)
def addModule(self, ast, moduleName, stmt):
    if self._rootref != None:
        module = atModule(self._rootref, ast.ref, self.value(moduleName), stmt, len(ast.ref.body), self.diagnostic,
                          self._stream)
    else:
        module = atModule(None, ast.ref, self.value(moduleName), stmt, len(ast.ref.body), self.diagnostic, self._stream)
    ast.ref.body.append(module)
    return True

@meta.hook(KoocNorm)
def addTypedef(self, ast, className):
    ctype = nodes.ComposedType(self.value(className) + '_mangled')
    ctype._storage = 2
    ctype._specifier = 1
    typedef = nodes.Decl(self.value(className), ctype)
    ast.ref.body.append(typedef)
    ast.ref.types[self.value(className)] = ref(typedef)
    return True


@meta.hook(KoocNorm)
def addClass(self, ast, className, stmt, parent):
    if self._rootref != None:
        classElem = atClass(self._rootref, ast.ref, self.value(className), stmt, len(ast.ref.body), self._classTemplate,
                            self.value(parent), self.diagnostic, self._stream)
        self._rootref.types[self.value(className)] = ref(ast)
    else:
        classElem = atClass(None, ast.ref, self.value(className), stmt, len(ast.ref.body), self._classTemplate,
                            self.value(parent), self.diagnostic, self._stream)
        ast.ref.types[self.value(className)] = ref(ast)
    ast.ref.body.append(classElem)
    return True


@meta.hook(KoocNorm)
def addMember(self, ast, expr, flag):
    if flag == 1:
        expr = expr.body[0]
    if self._rootref != None:
        member = atMember(self._rootref, expr, len(ast.ref.body), self.diagnostic, self._stream)
    else:
        member = atMember(ast.ref, expr, len(ast.ref.body), self.diagnostic, self._stream)
    ast.ref.body.append(member)
    return True


@meta.hook(KoocNorm)
def addMultipleMembers(self, current_block, stmt):
    for elem in stmt.body:
        addMember(self, current_block, elem, 0)
    return True


@meta.hook(KoocNorm)
def addVirtual(self, ast, expr, flag):
    if flag == 1:
        expr = expr.body[0]
    if self._rootref != None:
        virtual = atVirtual(self._rootref, expr, len(ast.ref.body), self.diagnostic, self._stream)
    else:
        virtual = atVirtual(ast.ref, expr, len(ast.ref.body), self.diagnostic, self._stream)
    ast.ref.body.append(virtual)
    return True


@meta.hook(KoocNorm)
def addMultipleVirtuals(self, current_block, stmt):
    for elem in stmt.body:
        addVirtual(self, current_block, elem, 0)
    return True


@meta.hook(KoocNorm)
def addImplementation(self, ast, name, stmt):
    implementation = atImplementation(ast.ref, self.value(name), stmt, self._implemTemplate, len(ast.ref.body),
                                      self.diagnostic, self._stream)
    ast.ref.body.append(implementation)
    return True


@meta.hook(Expression)
def new_binary(self, ast, op, param):
    left = Node()
    if hasattr(param, 'brack'):
        param = param.brack
    if hasattr(ast, "brack"):
        left = ast.brack
    else:
        left.set(ast)
    if isinstance(param, nodes.Binary) and param.params and isinstance(param.params[0], nodes.Array) and hasattr(
            param.params[0].call_expr, 'brack'):
        param = param.params[0].call_expr.brack
    ast.set(nodes.Binary(op, [left, param]))
    return True

def sameSignature(func1, func2):
    if (len(func1._ctype._params) != len(func2._ctype._params)) or (
        func1._ctype._identifier != func2._ctype._identifier):
        return False
    elif get_pointers(func1._ctype) != get_pointers(func2._ctype):
        return False
    for (elem1, elem2) in zip(func1._ctype._params[1:], func2._ctype._params[1:]):
        if elem1._ctype._identifier != elem2._ctype._identifier:
            return False
    return True


def update_index(ast):
    count = 0
    for elem in ast:
        if hasattr(elem, '_idx'):
            elem._idx = count
        count += 1


def clean_list(root):
    """
    delete all occurences of custom classes
    """

    count = 0
    for elem in root:
        if isinstance(elem, atImport) or isinstance(elem, atModule) or isinstance(elem, atImplementation) or isinstance(
                elem, atClass):
            root.pop(count)
            clean_list(root)
            return
        count += 1


def body_transfo(body):
    """
    call doTrans for each custom node
    each transformation can insert several nodes at a time, therefore we need to update indexes
    """

    for elem in body:
        if isinstance(elem, atImplementation) or isinstance(elem, atModule) or isinstance(elem, atClass):
            try:
                elem.doTrans()
            except error.Diagnostic as e:
                print (e)
                return False
            update_index(body)
    return True


def transfo_type(ast, templateVtable):
    tp = TypeSystem(ast, templateVtable)
    tp.solveExpr()


def transfo(ast, templateVtable):
    
    """
    transform custom nodes in nodes understandable by Cnorm
    delete those which are not
    """

    if not body_transfo(ast.body):
        return False
    clean_list(ast.body)
    transfo_type(ast, templateVtable)
    return True
