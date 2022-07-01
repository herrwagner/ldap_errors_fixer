
import re
from abc import abstractmethod


class PatternHandler:
    def __init__(self, pattern_dict: dict):
        self.pattern_dict = pattern_dict

    @abstractmethod
    def execute(self, value):
        pass

    def is_all_not_excluded(self, field):
        if self.pattern_dict['field'] == 'All':
            try:
                exclude = self.pattern_dict['exclude']['field']
            except KeyError:
                return True
            else:
                return exclude != field
        else:
            return False

    def check_field(self, field):
        if self.is_all_not_excluded(field) or self.pattern_dict['field'] == field:
            return True
        else:
            return False


class PatternHandlerRegEx(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.reg_ex = re.compile(pattern_dict['value'])

    def execute(self, value):
        return self.reg_ex.findall(value)[0]


class PatternHandlerString(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.pattern = pattern_dict['value']

    def execute(self, value):
        return self.pattern == value


class PatternHandlerList(PatternHandler):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)
        self.pattern = pattern_dict['value']

    def execute(self, value):
        return self.pattern in value


class PatternHandlerFactory:
    def __init__(self, pattern_dict):
        self.pattern_dict = pattern_dict

    @abstractmethod
    def factory(self):
        pass


class PatternHandlerFactoryRegEx(PatternHandlerFactory):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)

    def factory(self) -> PatternHandler:
        return PatternHandlerRegEx(self.pattern_dict)


class PatternHandlerFactoryPattern(PatternHandlerFactory):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)

    def factory(self) -> PatternHandler:
        return PatternHandlerString(self.pattern_dict)


class PatternHandlerFactoryList(PatternHandlerFactory):
    def __init__(self, pattern_dict):
        super().__init__(pattern_dict)

    def factory(self) -> PatternHandler:
        return PatternHandlerList(self.pattern_dict)
