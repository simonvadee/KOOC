#!/usr/bin/env python3

class atBrackets:
    def __init__(self, typedef, scope, param, funcName):
        self.typedef = typedef
        self.scope = scope
        self.param = param
        self.funcName = funcName
        self.isMember = False
        self.isVirtual = False
        self.instance = ""
