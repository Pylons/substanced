from pyramid.scaffolds import PyramidTemplate
import string, random

class SubstanceDProjectTemplate(PyramidTemplate):
    def pre(self, command, output_dir, vars): #pragma: no cover
        size = 10
        chars = string.ascii_letters + string.digits
        vars['random_password'] = ''.join(
            random.choice(chars) for x in range(size)
            )
        return PyramidTemplate.pre(self, command, output_dir, vars)
    _template_dir = 'substanced'
    summary = 'SubstanceD starter project'
