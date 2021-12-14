
from ldif import LDIFParser


class ParseLDIF(LDIFParser):
    def __init__(self, input_file, processing_object):
        LDIFParser.__init__(self, input_file)
        self.processing_object = processing_object

    def handle(self,dn, entry):
        self.processing_object.process_entry(dn, entry)
