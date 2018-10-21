import fnmatch
import re
from os import path, walk

BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', flags=re.S)
LINE_COMMENT_RE = re.compile(r'//.*?$', flags=re.M)
SQ_STRING_RE = re.compile(r"'.*?'")
DQ_STRING_RE = re.compile(r'".*?"')
STATIC_CALL_RE = re.compile(r'([A-Za-z0-9_]+)::([A-Za-z0-9_]+)[ \t\r\n]*\(', flags=re.M)
CLASS_RE = re.compile(r'^[ \t]*class[ \t\r\n]+([A-Za-z0-9_]+)[ \t\r\n{]+$', flags=re.M)
CLASS_EXTENDS_RE = re.compile(
    r'^[ \t]*class[ \t\r\n]+([A-Za-z0-9_]+)[ \t\r\n]+extends[ \t\r\n]+([A-Za-z0-9_]+)',
    flags=re.M)
METHOD_RE = re.compile(
    r'^[ \t]*(static[ \t\r\n]+)?function[ \t\r\n]+([A-Za-z0-9_]+)[ \t\r\n]*\([ \t\r\n]*(.*?)[ \t\r\n]*\)',
    flags=re.M)
STATIC_ERROR_RE = re.compile(
    r'Non-static method ([A-Za-z0-9_]+)::([A-Za-z0-9_]+)\(\) should not be called statically')
CONSTRUCTOR_ERROR_RE = re.compile(
    r'Methods with the same name as their class will not be constructors in a future version of PHP'
    r'; ([A-Za-z0-9_]+) has a deprecated constructor in')


class LookupError(Exception):
    pass


class StaticCall(object):
    def __init__(self, cname, mname):
        self.class_name = cname
        self.method_name = mname

    def __eq__(self, other):
        if self.class_name != other.class_name:
            return False
        if self.method_name != other.method_name:
            return False
        return True

    def __hash__(self):
        return hash(self.class_name + self.method_name)


class ClassDefinition(object):
    def __init__(self, name, fname, extends=None):
        self.name = name
        self.file = fname
        self.extends = extends
        self.methods = []

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.file != other.file:
            return False
        if self.extends != other.extends:
            return False
        return True

    def __hash__(self):
        return hash(self.name + self.file + str(self.extends))


class MethodDefinition(object):
    def __init__(self, name, static=False, byref=False, uses_this=False):
        self.name = name
        self.static = static
        self.byref = byref
        self.uses_this = uses_this
        self.args = []

    def __str__(self):
        out = ''
        if self.static:
            out += 'static '
        out += 'function '
        if self.byref:
            out += '&'
        out += self.name + '('
        tmpargs = []
        for arg in self.args:
            tmp = arg[0]
            if arg[1]:
                tmp += '=' + arg[1]
            tmpargs.append(tmp)
        out += ', '.join(tmpargs)
        out += ')'
        if self.uses_this:
            out += '  //uses $this'
        return out

    def add_arg(self, name, default=None):
        self.args.append((name, default))

    def is_compat(self, parent):
        if self.static != parent.static:
            return False

        if parent.byref and not self.byref:
            return False

        for i, pa in enumerate(parent.args):
            p_var, p_default = pa

            try:
                c_var, c_default = self.args[i]
            except:
                return False

            if p_default is not None and c_default is None:
                return False

            if p_var.startswith('&') != c_var.startswith('&'):
                return False

        for i, ca in enumerate(self.args):
            c_var, c_default = ca

            try:
                p_var, p_default = parent.args[i]

                if c_var.startswith('&') != p_var.startswith('&'):
                    return False
            except:
                if c_default is None:
                    return False

        return True


def walk_src():
    root_path = path.realpath(path.join(path.dirname(__file__), '..'))

    for root, dirnames, filenames in walk(root_path):
        for pattern in ['*.class', '*.inc', '*.php']:
            for filename in fnmatch.filter(filenames, pattern):
                # TODO: Annoying hack
                if 'upgrade/steps' in root and filename == 'SystemChecksStep.class':
                    continue

                yield path.join(root, filename)


def read_code(fname, mark=True):
    cmark = 'COMMENT' if mark else ''
    lmark = 'STR_LITERAL' if mark else ''

    with open(fname, 'rb') as fh:
        code = fh.read()

    code = BLOCK_COMMENT_RE.sub(cmark, code)
    code = LINE_COMMENT_RE.sub(cmark, code)
    code = SQ_STRING_RE.sub(lmark, code)
    code = DQ_STRING_RE.sub(lmark, code)

    return code


def find_logged_static_calls(fh):
    seen = set()

    for line in fh:
        match = STATIC_ERROR_RE.search(line)
        if match is not None:
            seen.add(StaticCall(match.group(1), match.group(2)))

    return seen


def find_logged_constructors(fh):
    seen = set()

    for line in fh:
        match = CONSTRUCTOR_ERROR_RE.search(line)
        if match is not None:
            seen.add(match.group(1))

    return seen


def find_static_calls(php):
    seen = set()

    matches = STATIC_CALL_RE.findall(php)
    if matches is not None:
        for cname, mname in matches:
            if cname in ('self', 'parent', 'PEAR'):
                continue
            seen.add(StaticCall(cname, mname))

    return seen


def find_class_definitions(php, fname):
    seen = set()

    matches = CLASS_RE.findall(php)
    if matches is not None:
        for name in matches:
            cd = ClassDefinition(name, fname)
            cd.methods = find_method_definitions(php, name)
            seen.add(cd)

    matches = CLASS_EXTENDS_RE.findall(php)
    if matches is not None:
        for name, ext in matches:
            cd = ClassDefinition(name, fname, ext)
            cd.methods = find_method_definitions(php, name)
            seen.add(cd)

    return seen


def find_method_definitions(php, cname):
    splitter = re.compile(r'^([ \t]*class[ \t\r\n]+[A-Za-z0-9_]+[ \t\r\n{]+)', flags=re.M)
    extractor = re.compile(r'^[ \t]*class[ \t\r\n]+([A-Za-z0-9_]+)[ \t\r\n{]+', flags=re.M)

    segments = splitter.split(php)
    for i, segment in enumerate(segments):
        match = extractor.search(segment)
        if match is not None and match.group(1) == cname:
            return _extract_method_definitions(segments[i + 1])

    return []


def _extract_method_definitions(php):
    splitter = re.compile(
        r'^([ \t]*(?:static[ \t\r\n]+)?function[ \t\r\n&]+[A-Za-z0-9_]+[ \t\r\n]*\([ \t\r\n]*.*?[ \t\r\n]*\))',
        flags=re.M)
    extractor = re.compile(
        r'^[ \t]*(static[ \t\r\n]+)?function([ \t\r\n&]+)([A-Za-z0-9_]+)[ \t\r\n]*\([ \t\r\n]*(.*?)[ \t\r\n]*\)',
        flags=re.M)
    thistest = re.compile(r'\$[ \t\r\n]*this[ \t\r\n]*[-:]')

    methods = []

    segments = splitter.split(php)
    for i, segment in enumerate(segments):
        match = extractor.search(segment)
        if match is not None:
            static_flag, byref_flag, name, signature = match.groups()

            static = ('static' in str(static_flag))
            byref = ('&' in str(byref_flag))
            md = MethodDefinition(name=name, static=static, byref=byref)

            for arg in _extract_argument_definitions(signature):
                md.add_arg(*arg)

            if thistest.search(segments[i + 1]) is not None:
                md.uses_this = True

            methods.append(md)

    return methods


def _extract_argument_definitions(signature):
    splitter = re.compile(r'[ \t]*,[ \t]*')
    extractor = re.compile(r'[ \t]*([A-Za-z0-9_$&]+)[ \t]*([ \t]*=[ \t]*([^ \t]+))?')

    args = splitter.split(signature)
    for arg in args:
        if not arg:
            continue

        varname, _, default = extractor.search(arg).groups()
        yield (varname, default)


def lookup_class(defs, name):
    possible = []

    for c in defs:
        if c.name == name:
            possible.append(c)

    lp = len(possible)
    if lp == 0:
        raise LookupError('no match for ' + name)
    elif lp > 1:
        raise LookupError(str(lp) + ' matches for ' + name)

    return possible[0]
