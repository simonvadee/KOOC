#!/usr/bin/env python3

import os.path
from weakref import ref

from cnorm import nodes
from pyrser.error import Severity, LocationInfo


class atImport:
    def __init__(self, here, filename, path, idx, importFiles, diagnostic, stream):
        self.here = ref(here)
        self.filename = filename
        self.path = path
        self.idx = idx
        self.importFiles = importFiles
        self.diagnostic = diagnostic
        self.stream = stream

    def createOutputName(self, name, from_ext, to_ext):
        if name.find(from_ext) == -1:
            self.diagnostic.notify(Severity.ERROR, "you shall use \".kh\" extensions",
                                   LocationInfo.from_stream(self.stream))
            raise self.diagnostic
        output = name.replace(from_ext, to_ext)
        return output

    def doTrans(self):

        """"
        check if file already imported
        create a new instance of KoocNorm and parse the file to be imported
        transform it (if there is other instances of atImport in the ast, go recursive)
        load types defined in 'self.filename' in self.here()
        put the body that resulted from the transformation as a value in a dict with the filename as key
        replace "@module" by "#include"
        """

        if self.is_inImportedFiles():
            return

        from koocNorm import KoocNorm, transfo
        kn = KoocNorm(self.filename, self.path, self.importFiles, self.here())
        ast = kn.parse_file(self.path + self.filename)

        if not transfo(ast, kn._implemTemplate[4].body.body[0]):
            return False

        self.importFiles = kn.importFiles
        if hasattr(self.here(), 'types'):
            add_chainmaps(self.here().types, ast.types)

        name = self.createOutputName(self.filename, '.kh', '.h')
        self.here().units[name] = ast
        self.here().body[self.idx] = nodes.Raw("#include \"" + name + "\"\n")

    def checkExists(self):
        return os.path.isfile(self.path + self.filename)

    def is_inImportedFiles(self):
        for elem in self.importFiles:
            if (elem == self.filename):
                return True
        self.importFiles.append(self.filename)

def add_chainmaps(a, b):
    for key, value in vars(b).items():
        setattr(a, key, value)
    return True
