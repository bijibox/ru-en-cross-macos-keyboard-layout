"""Small ctypes wrapper around Apple's public Text Input Sources APIs."""
import ctypes as C
import sys


class MacLayouts:
    def __init__(self):
        if sys.platform != 'darwin':
            raise RuntimeError('This check requires macOS')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.carbon = C.CDLL('/System/Library/Frameworks/Carbon.framework/Carbon')
        ptr = C.c_void_p
        signatures = [
            (self.cf, 'CFArrayGetCount', C.c_long, [ptr]),
            (self.cf, 'CFArrayGetValueAtIndex', ptr, [ptr, C.c_long]),
            (self.cf, 'CFStringGetCString', C.c_bool, [ptr, ptr, C.c_long, C.c_uint32]),
            (self.cf, 'CFDataGetBytePtr', ptr, [ptr]),
            (self.cf, 'CFURLCreateFromFileSystemRepresentation', ptr,
             [ptr, C.c_char_p, C.c_long, C.c_bool]),
            (self.cf, 'CFRelease', None, [ptr]),
            (self.carbon, 'TISCreateInputSourceList', ptr, [ptr, C.c_bool]),
            (self.carbon, 'TISGetInputSourceProperty', ptr, [ptr, ptr]),
            (self.carbon, 'TISRegisterInputSource', C.c_int32, [ptr]),
            (self.carbon, 'UCKeyTranslate', C.c_int32,
             [ptr, C.c_uint16, C.c_uint16, C.c_uint32, C.c_uint32, C.c_uint32,
              C.POINTER(C.c_uint32), C.c_uint32, C.POINTER(C.c_uint32), C.POINTER(C.c_uint16)]),
        ]
        for library, name, result, args in signatures:
            function = getattr(library, name)
            function.restype, function.argtypes = result, args
        self.sources = None
        self.refresh()

    def refresh(self):
        self.close()
        self.sources = self.carbon.TISCreateInputSourceList(None, True)
        if not self.sources:
            raise RuntimeError('macOS did not return any input sources')

    def close(self):
        if self.sources:
            self.cf.CFRelease(self.sources)
            self.sources = None

    def property(self, source, name):
        key = C.c_void_p.in_dll(self.carbon, name)
        return self.carbon.TISGetInputSourceProperty(source, key)

    def string(self, value):
        buffer = C.create_string_buffer(4096)
        if not value or not self.cf.CFStringGetCString(value, buffer, len(buffer), 0x08000100):
            raise RuntimeError('Cannot read input source string')
        return buffer.value.decode('utf-8')

    def find(self, identifier):
        available = []
        for index in range(self.cf.CFArrayGetCount(self.sources)):
            source = self.cf.CFArrayGetValueAtIndex(self.sources, index)
            found = self.string(self.property(source, 'kTISPropertyInputSourceID'))
            if 'check' in found:
                available.append(found)
            if found == identifier:
                return source
        raise RuntimeError(f'Input source not found: {identifier}; test sources: {available}')

    def data(self, source):
        data = self.property(source, 'kTISPropertyUnicodeKeyLayoutData')
        if not data:
            raise RuntimeError('macOS could not compile the keyboard layout')
        return self.cf.CFDataGetBytePtr(data)

    def register(self, bundle):
        path = bytes(bundle)
        url = self.cf.CFURLCreateFromFileSystemRepresentation(None, path, len(path), True)
        try:
            status = self.carbon.TISRegisterInputSource(url)
            if status:
                raise RuntimeError(f'TISRegisterInputSource failed: {status}')
        finally:
            self.cf.CFRelease(url)
        self.refresh()

    def translate(self, data, key, modifiers, keyboard_type):
        state, length = C.c_uint32(), C.c_uint32()
        output = (C.c_uint16 * 16)()
        status = self.carbon.UCKeyTranslate(data, key, 0, modifiers, keyboard_type, 1,
                                          C.byref(state), 16, C.byref(length), output)
        if status or state.value:
            raise RuntimeError(f'UCKeyTranslate failed: status={status}, dead state={state.value}')
        return bytes(output)[:length.value * 2].decode('utf-16-le')
