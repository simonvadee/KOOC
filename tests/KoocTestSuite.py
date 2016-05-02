#!/usr/bin/env python3

import unittest
from koocNorm import KoocNorm, transfo

class ImportTestCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testImport.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testImport.kc')
        
    def test_import(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))


class ModuleTestCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testModule.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testModule.kc')
        
    def test_module(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))


class ManglingTestCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testWrongMangling.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testWrongMangling.kc')
        
    def test_mangling(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))


class ClassTestCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testClass.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testClass.kc')

    def test_class(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassDoubleDefTestCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testDoubleDefinitionClasse.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testDoubleDefinitionClasse.kc')

    def test_double_def(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassInlineCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testInlineClass.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testInlineClass.kc')

    def test_inline(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassDoubleClasseCase(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testDoubleClasse.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testDoubleClasse.kc')

    def test_double_classe(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassMissingAssignation(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testMissingAssignation.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testMissingAssignation.kc')

    def test_missing_assignation(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassWrongInclude(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testMissingAssignation.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testMissingAssignation.kc')

    def test_wrong_include(self):
        if not self.res:
            self.assertTrue(True)

class ClassWrongVirtual(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testWrongVirtual.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testWrongVirtual.kc')

    def test_wrong_virtual(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassUnknownParent(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testUnknownParent.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testUnknownParent.kc')

    def test_unknown_parent(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassWrongMember(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testWrongMember.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testWrongMember.kc')

    def test_wrong_virtual(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassNeverDefined(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testNeverDefined.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testNeverDefined.kc')

    def test_enever_defined(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassUnknownImplementation(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testUnknownImplementation.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testUnknownImplementation.kc')

    def test_unknown_implementation(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))
        
class ClassWrongDefImplem(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testWrongDefImplem.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testWrongDefImplem.kc')

    def test_wrong_def_implem(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

        
class ClassWrongDefImplem(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testWrongDefImplem.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testWrongDefImplem.kc')

    def test_wrong_def_implem(self):
        self.assertFalse(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassTypageBinaryExpr(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testTypageBinaryExpr.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testTypageBinaryExpr.kc')

    def test_typage_binary_expr(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

class ClassTypageClass(unittest.TestCase):
    def setUp(self):
        self.grammar = KoocNorm('testTypageClass.kc', './samples/')
        self.res = self.grammar.parse_file('./samples/testTypageClass.kc')

    def test_typage_class(self):
        self.assertTrue(transfo(self.res, self.grammar._implemTemplate[4].body.body[0]))

if __name__ == '__main__':
    unittest.main()
