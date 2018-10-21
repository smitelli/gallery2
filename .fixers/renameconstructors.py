import re
from fixlib import find_class_definitions, read_code, walk_src


def main():
    class_defs = set()

    for fname in walk_src():
        php = read_code(fname)
        class_defs |= find_class_definitions(php, fname)

    for c in class_defs:
        rewrite(c)


def rewrite(cls):
    print 'Rewriting ' + cls.file

    with open(cls.file, 'rb') as fh:
        php = fh.read()

    php2 = re.sub(
        r'^([ \t]+function[ \t\r\n]+)(' + cls.name + ')([ \t\r\n]*\()', r'\1__construct\3',
        php, flags=re.M)

    if cls.extends:
        php2 = re.sub(
            r'(\$this[ \t\r\n]*->[ \t\r\n]*)(' + cls.extends + ')([ \t\r\n]*\()',
            r'parent::__construct\3', php2)

        php2 = re.sub(
            r'(parent[ \t\r\n]*::[ \t\r\n]*)(' + cls.extends + ')([ \t\r\n]*\()',
            r'\1__construct\3', php2)

    if php2 != php:
        with open(cls.file, 'wb') as fh:
            fh.write(php2)


if __name__ == '__main__':
    main()
