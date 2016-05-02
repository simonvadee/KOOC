#!/usr/bin/env python3

from cnorm.parsing.declaration import Declaration
from pyrser import meta
from pyrser.grammar import Grammar


class SolveLiteral(Grammar):
    def __init__(self, datas):
        Grammar.__init__(self)
        self.datas = datas
        self.dicspec = {
            'spec': {
                'll': 'long long',
                'l': 'long',
                'sh': 'short'
            },
            'float': ['float', 'double']
        }

    def intExists(self):
        for elem in self.datas:
            if elem.find('int') != -1 and elem.find('p') == -1:
                return True
        return False

    def tryIntType(self):
        if not self.intExists():
            return self.tryFloatType()
        decl = Declaration()
        for elem in self.datas:
            for key, corres in self.dicspec['spec'].items():
                if elem.find(key) != -1:
                    return getPrimaryType(corres)
        return getPrimaryType('int')

    def tryFloatType(self):
        decl = Declaration()
        for elem in self.datas:
            for corres in self.dicspec['float']:
                if elem.find(corres) != -1:
                    for key, spec in self.dicspec['spec'].items():
                        if elem.find(key) != -1:
                            return getPrimaryType(spec + ' ' + corres)
                    return getPrimaryType(corres)
        return getPrimaryType('float')

    entry = "translation_literal"
    grammar = """
    translation_literal =
    [
        [
                int:>_
                | float:>_
                | char:>_
                | string:>_
        ]
        Base.eof
    ]

    int = [ num+:integer #handleIntType(_) ]
    float = [ [num|'.']+:f #handleFloatType(_) ]
    char = [
                [ "'" read_char:c "'" #handleCharType(_) ]
                | [ '"' read_char:c '"' #handleCharType(_) ]
           ]
    string = [
                [ "'" [!"'" read_char]+:s "'" #handleStringType(_)]
                | [ '"' [!'"' read_char]+:s '"' #handleStringType(_)]
             ]

    """


@meta.hook(SolveLiteral)
def handleIntType(self, ast):
    ast.typ = self.tryIntType()
    return True


@meta.hook(SolveLiteral)
def handleFloatType(self, ast):
    ast.typ = self.tryFloatType()
    return True


@meta.hook(SolveLiteral)
def handleCharType(self, ast):
    decl = Declaration()
    ast.typ = getPrimaryType('char')
    return True


@meta.hook(SolveLiteral)
def handleStringType(self, ast):
    decl = Declaration()
    ast.typ = getPrimaryType('char *')
    return True


def getPrimaryType(param):
    decl = Declaration()
    typ = decl.parse(param + ';').body[0]._ctype
    return typ
