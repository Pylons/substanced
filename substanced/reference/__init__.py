from persistent import Persistent
import BTrees

from ..util import oid_of
from ..service import find_service
from ..content import content
from ..interfaces import IReferences

class ReferenceSet(Persistent):
    
    family = BTrees.family32

    def __init__(self):
        self.referents = self.family.IO.BTree()
        self.referrers = self.family.IO.BTree()

    def connect(self, src, target):
        referents = self.referents.setdefault(src, self.family.IF.TreeSet())
        referents.insert(target)
        referrers = self.referrers.setdefault(target, self.family.IF.TreeSet())
        referrers.insert(src)

    def disconnect(self, src, target):
        referents = self.referents.get(src)
        if referents is not None:
            try:
                referents.remove(target)
            except KeyError:
                pass
            
        referrers = self.referrers.get(target)
        if referrers is not None:
            try:
                referrers.remove(src)
            except KeyError:
                pass

    def refers_to(self, src, target):
        referents = self.referents.get(src)
        if referents is not None:
            return target in referents
        return False

    def referred_to(self, src, target):
        referrers = self.referrers.get(src)
        if referrers is not None:
            return target in referrers
        return False

    def get_referents(self, src):
        return self.referents.get(src, [])

    def get_referrers(self, src):
        return self.referrers.get(src, [])

class ReferenceMap(Persistent):
    
    family = BTrees.family32
    
    def __init__(self, refmap=None):
        if refmap is None:
            refmap = self.family.OO.BTree()
        self.refmap = refmap

    def connect(self, src, target, reftype):
        refset = self.refmap.setdefault(reftype, ReferenceSet())
        refset.connect(src, target)

    def disconnect(self, src, target, reftype):
        refset = self.refmap.get(reftype)
        if refset is not None:
            refset.disconnect(src, target)

    def refers_to(self, src, target, reftype):
        refset = self.refmap.get(reftype)
        if refset is not None:
            return refset.refers_to(src, target)
        return False

    def referred_to(self, src, target, reftype):
        refset = self.refmap.get(reftype)
        if refset is not None:
            return refset.referred_to(src, target)
        return False

    def get_referents(self, src, reftype):
        refset = self.refmap.get(reftype)
        if refset is not None:
            return refset.get_referents(src)
        return []

    def get_referrers(self, src, reftype):
        refset = self.refmap.get(reftype)
        if refset is not None:
            return refset.get_referrers(src)
        return []

@content(IReferences, icon='icon-random')
class References(Persistent):
    def __init__(self):
        self.referencemap = ReferenceMap()

    def connect(self, src, target, reftype):
        src_oid, target_oid = oid_of(src), oid_of(target)
        self.references.connect(src_oid, target_oid, reftype)

    def disconnect(self, src, target, reftype):
        src_oid, target_oid = oid_of(src), oid_of(target)
        self.references.disconnect(src_oid, target_oid, reftype)

    def get_referents(self, obj, reftype):
        oid = oid_of(obj)
        return iter_objects(
            self.references.get_referents(oid, reftype),
            find_service(self.__parent__, 'objectmap'),
            )

    def get_referent(self, obj, reftype):
        try:
            return self.get_referents(obj, reftype).next()
        except StopIteration:
            return None

    def get_referrers(self, obj, reftype):
        oid = oid_of(obj)
        return iter_objects(
            self.references.get_referrers(oid, reftype),
            find_service(self.__parent__, 'objectmap'),
            )

    def get_referrer(self, obj, reftype):
        try:
            return self.get_referrers(obj, reftype).next()
        except StopIteration:
            return None

def iter_objects(oids, objectmap):
    for oid in oids:
        yield oid.object_for(oid)

def includeme(config):
    config.scan('substanced.reference')
    
