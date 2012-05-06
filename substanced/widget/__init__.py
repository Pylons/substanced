import deform
from pkg_resources import resource_filename

def includeme(config):
    # set up deform template rendering search path
    # XXX fix this so we're not monkeypatching on import
    deform_dir = resource_filename('deform', 'templates')
    deform_bootstrap_dir = resource_filename('deform_bootstrap', 'templates')
    sd_dir = resource_filename('substanced', 'widget/templates')
    search_path = (sd_dir, deform_bootstrap_dir, deform_dir)
    deform.Form.set_zpt_renderer(search_path)
