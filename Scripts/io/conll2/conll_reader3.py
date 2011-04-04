"""Defines classes for reading conll files."""

class ConllCallback(object):
    """An abstract base class for callbacks."""
    def fileStart(self, file_name):
        """Called when a new file is opened by the reader."""
        pass
    
    def documentStart(self, title):
        """Called when the document header C{##%PAGE} is met.
        @param title: the title of the document."""
        pass
    
    def templates(self, templates):
        """Notifies the callback of the templates present in the document.
        @param templates: a list of the templates defined."""
        pass

    def redirect(self):
        """Notifies the callback that this page is a redirect."""
        pass
    
    def fieldStart(self, field):
        """Signals that start of a field.
        @param field: the name of the field."""
        pass
    
    def sentenceStart(self):
        """Signals that start of a new sentence."""
        pass
    
    def word(self, attributes):
        """Called for each word (self, and punctuation mark as well).
        @param attributes: the attributes that belong to the current word."""
        pass
    
    def sentenceEnd(self):
        """Signals the end of the current sentence."""
        pass
    
    def fieldEnd(self):
        """Signals the end of the current field."""
        pass
    
    def documentEnd(self):
        """Signals that the current document has been fully read."""
        pass
    
    def fileEnd(self):
        """Called when the current file has been completely read by the reader."""
        pass

class TestCallback(ConllCallback):
    """An abstract base class for callbacks."""
    def fileStart(self, file_name):
        """Called when a new file is opened by the reader."""
        print("fileStart({0})".format(file_name))
    
    def documentStart(self, title):
        """Called when the document header C{##%PAGE} is met.
        @param title: the title of the document."""
        print("documentStart({0})".format(title))
    
    def templates(self, templates):
        """Notifies the callback of the templates present in the document.
        @param templates: a list of the templates defined."""
        print("templates({0})".format(templates))

    def redirect(self):
        """Notifies the callback that this page is a redirect."""
        print("redirect()")
    
    def fieldStart(self, field):
        """Signals that start of a field.
        @param field: the name of the field."""
        print("fieldStart({0})".format(field))
    
    def sentenceStart(self):
        """Signals that start of a new sentence."""
        print("sentenceStart()")
    
    def word(self, attributes):
        """Called for each word (self, and punctuation mark as well).
        @param attributes: the attributes that belong to the current word."""
        print("word({0})".format(attributes))
    
    def sentenceEnd(self):
        """Signals the end of the current sentence."""
        print("sentenceEnd()")
    
    def fieldEnd(self):
        """Signals the end of the current field."""
        print("fieldEnd()")
    
    def documentEnd(self):
        """Signals that the current document has been fully read."""
        print("documentEnd()")
    
    def fileEnd(self):
        """Called when the current file has been completely read by the reader."""
        print("fileEnd()")

class DefaultConllCallback(ConllCallback):
    """Saves the file name, title and field parameters to member fields, so that
    subclass won't have to implement it by themselves."""
    def __init__(self):
        self.cc_file  = None
        self.cc_title = None
        self.cc_field = None
        self.cc_redirect = False
    
    def fileStart(self, file_name):
        """Saves the file name."""
        self.cc_file = file_name
    
    def documentStart(self, title):
        """Saves the page title."""
        self.cc_title = title
    
    def redirect(self):
        """Redirects are saved as well."""
        self.cc_redirect = True
    
    def fieldStart(self, field):
        """Saves the field name."""
        self.cc_field = field
        
    def fieldEnd(self):
        """Forgets the field name. Subclasses should call this method
        only when they do not need the field name anymore."""
        self.cc_field = None
    
    def documentEnd(self):
        """Forgets the document title. Subclasses should call this method
        only when they do not need the title anymore."""
        self.cc_title = None
        self.cc_redirect = False
    
    def fileEnd(self):
        """Forgets the file name. Subclasses should call this method at the
        only when they do not need the file name anymore."""
        self.cc_file = None
    
class ConllReader(object):
    """Reads conll files and notifies all callback objects."""
    
    META_HEAD = "%%#"
    """The head of a meta sequence."""
    PAGE_LABEL = "PAGE"
    """The page label."""
    FIELD_LABEL = "Field"
    """The field label."""
    TEMPLATE_LABEL = "Templates"
    """Template enumeration label."""
    REDIRECT_LABEL = "Redirect"
    """Redirect label."""
    
    NONE, PAGE, FIELD, SENTENCE = 0, 1, 2, 3
    
    META_LEN = len(META_HEAD)
    """Length of the meta header precomputed for efficiency."""
    
    def __init__(self, callbacks = []):
        """Registers the specified callbacks. Callbacks will be notified in the
        same order as they are registered."""
        self.callbacks = list(callbacks)
        self.state = ConllReader.NONE
    
    def read(self, fileName, charset='utf-8'):
        """Reads the specified file and notifies all registered callbacks.
        @throws IOError if the file denoted by C{fileName} does not exist or it
                cannot be read.
        @throws LookupError if C{charset} is not supported."""
        with open(fileName, 'r', encoding = charset) as in_file:
            self.__fileStart(fileName)
            for line in in_file:
                line = line.strip()
                if line.startswith(ConllReader.META_HEAD):
                    if line.startswith(ConllReader.PAGE_LABEL, ConllReader.META_LEN):
                        self.__endState(ConllReader.PAGE)
                        self.__documentStart(line.split("\t")[1])
                        self.__startState(ConllReader.PAGE)
                    elif line.startswith(ConllReader.FIELD_LABEL, ConllReader.META_LEN):
                        self.__endState(ConllReader.FIELD)
                        self.__fieldStart(line.split("\t")[1])
                        self.__startState(ConllReader.FIELD)
                    elif line.startswith(ConllReader.TEMPLATE_LABEL, ConllReader.META_LEN):
                        self.__templates(line.split("\t")[1].split(","))
                    elif line.startswith(ConllReader.REDIRECT_LABEL, ConllReader.META_LEN):
                        self.__redirect()
                elif len(line) == 0:
                    self.__endState(ConllReader.SENTENCE)
                else:
                    if self.state == ConllReader.FIELD:
                        self.__sentenceStart()
                        self.__startState(ConllReader.SENTENCE)
                    if self.state == ConllReader.SENTENCE:
                        self.__word(line.split("\t"))
            self.__endState(ConllReader.PAGE)
        self.__fileEnd()
    
    def __startState(self, what):
        """"Starts" the specific state."""
        self.state = what
    
    def __endState(self, what):
        """Removes the specific state, as well as all states above it."""
        while self.state >= what:
            if self.state == ConllReader.SENTENCE:
                self.__sentenceEnd()
            elif self.state == ConllReader.FIELD:
                self.__fieldEnd()
            elif self.state == ConllReader.PAGE:
                self.__documentEnd()
            self.state -= 1
    
    # Callback registration
    
    def addCallback(self, callback):
        """ Adds C{callback} to the list of callbacks, if it is not already
	registered."""
        if callback and not callback in self.callbacks:
            self.callbacks.append(callback)
    
    def removeCallback(self, callback):
        """Unregisters C{callback}."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def get_callbacks(self):
        """Returns the set of registered callbacks."""
        return list(self.callbacks)
    
    # Convenience methods for notifying all callbacks. Please let me know if you
    # have a better solution.
    def __fileStart(self, file_name):
        """Called when a new file is opened by the reader."""
        for callback in self.callbacks:
            callback.fileStart(file_name)
    
    def __documentStart(self, title):
        """Called when the document header C{##%PAGE} is met.
        @param title: the title of the document."""
        for callback in self.callbacks:
            callback.documentStart(title)
    
    def __templates(self, templates):
        """Notifies the callback of the templates present in the document.
        @param templates: a list of the templates defined."""
        for callback in self.callbacks:
            callback.templates(templates)

    def __redirect(self):
        """Notifies the callback that this page is a redirect."""
        for callback in self.callbacks:
            callback.redirect()
    
    def __fieldStart(self, field):
        """Signals that start of a field.
        @param field: the name of the field."""
        for callback in self.callbacks:
            callback.fieldStart(field)
        
    def __sentenceStart(self):
        """Signals that start of a new sentence."""
        for callback in self.callbacks:
            callback.sentenceStart()
        
    def __word(self, attributes):
        """Called for each word (self, and punctuation mark as well).
        @param attributes: the attributes that belong to the current word."""
        for callback in self.callbacks:
            callback.word(attributes)
        
    def __sentenceEnd(self):
        """Signals the end of the current sentence."""
        for callback in self.callbacks:
            callback.sentenceEnd()
        
    def __fieldEnd(self):
        """Signals the end of the current field."""
        for callback in self.callbacks:
            callback.fieldEnd()
        
    def __documentEnd(self):
        """Signals that the current document has been fully read."""
        for callback in self.callbacks:
            callback.documentEnd()
        
    def __fileEnd(self):
        """Called when the current file has been completely read by the reader."""
        for callback in self.callbacks:
            callback.fileEnd()

if __name__ == '__main__':
    import sys
    ConllReader([TestCallback()]).read(sys.argv[1], "utf-8")
