import re
from fixlib import (
    find_class_definitions, find_static_calls, lookup_class, read_code, walk_src)

CLASS_SPLIT_RE = re.compile(r'^([ \t]*class[ \t\r\n]+[A-Za-z0-9_]+[ \t\r\n{]+)', flags=re.M)
CLASS_EXTRACT_RE = re.compile(r'^[ \t]*class[ \t\r\n]+([A-Za-z0-9_]+)[ \t\r\n{]+', flags=re.M)
FUNCTION_SPLIT_RE = re.compile(r'^([ \t]+function[ \t\r\n]+[A-Za-z0-9_]+)', flags=re.M)
FUNCTION_EXTRACT_RE = re.compile(r'^[ \t]+function[ \t\r\n]+([A-Za-z0-9_]+)', flags=re.M)

static_calls = set()
class_defs = set()


def main():
    global static_calls, class_defs

    for fname in walk_src():
        php = read_code(fname, mark=False)

        static_calls |= find_static_calls(php)
        class_defs |= find_class_definitions(php, fname)

    for sc in static_calls:
        rewrite(sc.class_name, sc.method_name)


def rewrite(class_name, method_name):
    print 'Scanning ' + class_name + '::' + method_name
    c = lookup_class(class_defs, class_name)

    with open(c.file, 'rb') as fh:
        php = fh.read()

    php_classes = CLASS_SPLIT_RE.split(php)
    for i, segment in enumerate(php_classes):
        matches = CLASS_EXTRACT_RE.search(segment)
        if matches and matches.group(1) == class_name:
            php_functions = FUNCTION_SPLIT_RE.split(php_classes[i + 1])
            for j, subsegment in enumerate(php_functions):
                matches = FUNCTION_EXTRACT_RE.search(subsegment)
                if matches and matches.group(1) == method_name:
                    print 'FOUND ' + method_name
                    php_functions[j] = subsegment.replace('function', 'static function')
            php_classes[i + 1] = ''.join(php_functions)
    php2 = ''.join(php_classes)

    if php2 != php:
        with open(c.file, 'wb') as fh:
            fh.write(php2)

    if c.extends:
        print '  --> extends!'
        rewrite(c.extends, method_name)


if __name__ == '__main__':
    main()
