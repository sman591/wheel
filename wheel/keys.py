"""Store and retrieve wheel signing / verifying keys.

Given a scope (a package name, + meaning "all packages", or - meaning 
"no packages"), return a list of verifying keys that are trusted for that 
scope.

Given a package name, return a list of (scope, key) suggested keys to sign
that package (only the verifying keys; the private signing key is stored
elsewhere).

Keys here are represented as urlsafe_b64encoded strings with no padding.

Tentative command line interface:

# list trusts
wheel trust
# trust a particular key for all
wheel trust + key
# trust key for beaglevote
wheel trust beaglevote key
# stop trusting a key for all
wheel untrust + key

# generate a key pair
wheel keygen

# import a signing key from a file
wheel import keyfile

# export a signing key
wheel export key
"""

import json
import dirspec.basedir
import os.path
from wheel.util import urlsafe_b64encode, urlsafe_b64decode, native, binary

class WheelKeys(object):
    def __init__(self):
        self.data = {'signers':[], 'verifiers':[]}
        
    def load(self):
        # XXX JSON is not a great database
        for path in dirspec.basedir.load_config_paths('wheel'):
            conf = os.path.join(native(path), 'wheel.json')
            if os.path.exists(conf):
                with open(conf, 'r') as infile:
                    self.data = json.load(infile)
                    for x in ('signers', 'verifiers'):
                        if not x in self.data:
                            self.data[x] = []
                break
        return self

    def save(self):
        # Try not to call this a very long time after load() 
        path = dirspec.basedir.save_config_path('wheel')
        conf = os.path.join(path, 'wheel.json')
        with open(conf, 'w+') as out:
            json.dump(self.data, out, indent=2)
        return self
    
    def trust(self, scope, vk):
        """Start trusting a particular key for given scope."""
        self.data['verifiers'].append({'scope':scope, 'vk':vk})
        return self
    
    def untrust(self, scope, vk):
        """Stop trusting a particular key for given scope."""
        self.data['verifiers'].remove({'scope':scope, 'vk':vk})
        return self
        
    def trusted(self, scope=None):
        """Return list of [(scope, trusted key), ...] for given scope."""
        trust = [(x['scope'], x['vk']) for x in self.data['verifiers'] if x['scope'] in (scope, '+')]
        trust.sort() # hack '+' will usually sort before all valid package names
        trust.reverse()
        return trust
    
    def signers(self, scope):
        """Return list of signing key(s)."""
        sign = [(x['scope'], x['vk']) for x in self.data['verifiers'] if x['scope'] in (scope, '+')]
        sign.sort() # XXX ONLY SORT BY SCOPE (most recently added signer should win)
        sign.reverse()
        return sign
    
    def add_signer(self, scope, vk):
        """Remember verifying key vk as being valid for signing in scope."""
        self.data['signers'].append({'scope':scope, 'vk':vk})
    