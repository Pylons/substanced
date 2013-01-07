from substanced.objectmap import (
    find_objectmap,
    )
import logging
from substanced.file import File
from substanced.util import (
    get_dotted_name,
    chunks,
    )
from substanced.file import magic


_marker = object()

logger = logging.getLogger('evolution')

def evolve(root):
    logger.info(
        'Running substanced evolve step 7: reset all blob mimetypes '
        'to nominal USE_MAGIC value'
        )
    if magic:
        objectmap = find_objectmap(root)
        if objectmap is not None:
            oids = objectmap.get_extent(get_dotted_name(File))
            if oids is not None:
                for oid in oids:
                    f = objectmap.object_for(oid)
                    if f.get_size():
                        for chunk in chunks(f.blob.open('r')):
                            m = magic.Magic(mime=True)
                            mimetype = m.from_buffer(chunk)
                            f.mimetype = mimetype
                            break
