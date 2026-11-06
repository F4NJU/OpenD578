"""Physical Flash/vector placement without OEM signatures or SRAM structures."""
import hashlib,struct
from pathlib import Path
from audit_ram_v121 import RAM,RAM_SIZE,APP

FLASH=0x08000000
FLASH_SIZE=0x300000


def inspect_board_image(path,load_address=None,vector_address=None):
    data=Path(path).read_bytes()
    if not 8<=len(data)<=FLASH_SIZE:raise ValueError('Firmware must contain vectors and fit 3 MiB of Flash')
    if load_address is None:load_address=FLASH if len(data)==FLASH_SIZE else APP
    if load_address%128 or not FLASH<=load_address<load_address+len(data)<=FLASH+FLASH_SIZE:
        raise ValueError('Firmware placement outside physical Flash or not vector aligned')
    if vector_address is None:vector_address=APP if len(data)==FLASH_SIZE else load_address
    offset=vector_address-load_address
    if vector_address%128 or not 0<=offset<=len(data)-8:raise ValueError('Vector table is outside the selected image')
    stack,entry=struct.unpack_from('<II',data,offset)
    if not RAM<stack<=RAM+RAM_SIZE or stack%8:raise ValueError('Invalid initial physical SRAM stack')
    if not entry&1 or not load_address<=entry&~1<load_address+len(data):raise ValueError('Reset vector is not Thumb code inside the image')
    return data,dict(load_address=load_address,vector_address=vector_address,bytes=len(data),
        sha256=hashlib.sha256(data).hexdigest(),initial_stack=stack,reset_vector=entry,
        format='physical_flash' if len(data)==FLASH_SIZE else 'raw_flash_image',OEM_reference_required=False)


def inspect_upload(path):
    errors=[]
    for load,vector in [(None,None),(FLASH,FLASH)]:
        try:return inspect_board_image(path,load,vector)[1]
        except ValueError as error:errors.append(str(error))
    raise ValueError('No valid Flash/vector placement: '+'; '.join(errors))
