def includeme(config):
    config.include('pyramid_zodbconn')
    config.include('substanced.catalog')
    config.include('substanced.content')
    config.include('substanced.sdi')
    
    
