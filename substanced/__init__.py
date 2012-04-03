def includeme(config):
    config.include('pyramid_zodbconn')
    config.include('substanced.content')
    config.include('substanced.catalog')
    config.include('substanced.models')
    config.include('substanced.subscribers')
    config.include('substanced.sdi')
    
    
