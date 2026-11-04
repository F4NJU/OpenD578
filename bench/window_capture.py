"""Capture this Tk window via WM_PRINT, never the desktop or foreground app."""
def capture_window(root,path):
    import ctypes as C
    from ctypes import wintypes as W
    from PIL import Image
    user=C.WinDLL('user32',use_last_error=True);gdi=C.WinDLL('gdi32',use_last_error=True)
    user.GetAncestor.argtypes=[W.HWND,W.UINT];user.GetAncestor.restype=W.HWND
    user.GetDC.argtypes=[W.HWND];user.GetDC.restype=W.HDC
    user.GetClientRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
    user.PrintWindow.argtypes=[W.HWND,W.HDC,W.UINT];user.PrintWindow.restype=W.BOOL
    user.ReleaseDC.argtypes=[W.HWND,W.HDC]
    gdi.CreateCompatibleDC.argtypes=[W.HDC];gdi.CreateCompatibleDC.restype=W.HDC
    gdi.CreateCompatibleBitmap.argtypes=[W.HDC,C.c_int,C.c_int];gdi.CreateCompatibleBitmap.restype=W.HBITMAP
    gdi.SelectObject.argtypes=[W.HDC,W.HGDIOBJ];gdi.SelectObject.restype=W.HGDIOBJ
    gdi.DeleteObject.argtypes=[W.HGDIOBJ];gdi.DeleteDC.argtypes=[W.HDC]
    class Header(C.Structure):
        _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),
                  ('compression',W.DWORD),('image_size',W.DWORD),('xppm',W.LONG),('yppm',W.LONG),('used',W.DWORD),('important',W.DWORD)]
    gdi.GetDIBits.argtypes=[W.HDC,W.HBITMAP,W.UINT,W.UINT,C.c_void_p,C.POINTER(Header),W.UINT]
    hwnd=user.GetAncestor(root.winfo_id(),2)
    rect=W.RECT();user.GetClientRect(hwnd,C.byref(rect));width=rect.right;height=rect.bottom
    dc=user.GetDC(hwnd);memory=gdi.CreateCompatibleDC(dc);bitmap=gdi.CreateCompatibleBitmap(dc,width,height)
    previous=gdi.SelectObject(memory,bitmap)
    try:
        if not user.PrintWindow(hwnd,memory,3):raise OSError('Window-only capture failed')
        header=Header(C.sizeof(Header),width,-height,1,32,0,width*height*4,0,0,0,0)
        data=C.create_string_buffer(width*height*4)
        if not gdi.GetDIBits(memory,bitmap,0,height,data,C.byref(header),0):raise OSError('Window bitmap unavailable')
        Image.frombuffer('RGB',(width,height),data.raw,'raw','BGRX',0,1).save(path)
    finally:
        gdi.SelectObject(memory,previous);gdi.DeleteObject(bitmap);gdi.DeleteDC(memory);user.ReleaseDC(hwnd,dc)
