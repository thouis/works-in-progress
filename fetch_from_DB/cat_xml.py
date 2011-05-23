import sys
import xml.parsers.expat

print_all = 0
depth = 0

def start_element(name, attrs):
    print name, attrs

def end_element(name):
    return
    global print_all, depth
    if print_all:
        depth -= 1
    if name == 'Filters':
        raise ValueError('foo')

for f in sys.argv[1:]:
    try:
        print f
        parser = xml.parsers.expat.ParserCreate()
        parser.returns_unicode = False
        parser.StartElementHandler = start_element
        parser.EndElementHandler = end_element
        parser.ParseFile(open(f))
    except Exception, e:
        pass
