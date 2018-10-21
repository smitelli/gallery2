from fixlib import find_class_definitions, lookup_class, read_code, walk_src


def main():
    class_defs = set()

    for fname in walk_src():
        php = read_code(fname)
        class_defs |= find_class_definitions(php, fname)

    for c1 in class_defs:
        for m in c1.methods:
            if m.static and m.uses_this:
                print 'WHOA - ' + c1.file + ': ' + c1.name + '::' + str(m)
                print ''

        c2name = c1.extends
        while c2name is not None:
            c2 = None
            try:
                c2 = lookup_class(class_defs, c2name)
                c2name = c2.extends
            except Exception as exc:
                print 'ERROR WALKING ' + c2name
                print exc.message
                print ''
                c2name = None

            if c2:
                compare(c1, c2)


def compare(c1, c2):
    for m1 in c1.methods:
        for m2 in c2.methods:
            if m1.name == m2.name:
                if not m1.is_compat(m2):
                    print c1.file + ': ' + c1.name + '::' + str(m1)
                    print c2.file + ': ' + c2.name + '::' + str(m2)
                    print ''


if __name__ == '__main__':
    main()
