"""Private worker-to-server CDC state frames over the existing stdout pipe."""
import json

PREFIX='@D578_CDC_STATE '
STATES={'disconnected','enumerating','ready','error'}


def encode(value):
    compact={key:item for key,item in value.items() if key!='recent_events'}
    return PREFIX+json.dumps(compact,separators=(',',':'))+'\n'


def decode(line):
    if not line.startswith(PREFIX):return None
    value=json.loads(line[len(PREFIX):])
    if not isinstance(value,dict) or value.get('state') not in STATES or not isinstance(value.get('session'),str):
        raise ValueError('Invalid CDC worker state frame')
    total=value.get('received_total');base=value.get('received_base')
    if type(total) is not int or type(base) is not int or not 0<=base<=total:raise ValueError('Invalid CDC receive counters')
    data=bytes.fromhex(value.get('received_hex',''))
    if len(data)!=total-base or len(data)>65536:raise ValueError('CDC receive history length mismatch')
    return value


class Publisher:
    def __init__(self,stream):self.stream=stream
    def __call__(self,value):self.stream.write(encode(value));self.stream.flush()
