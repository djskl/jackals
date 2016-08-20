#encoding:utf-8

from __future__ import unicode_literals

import base64
import cgi
import sys
import re

__all__ = ('MultiPartParser', 'MultiPartParserError', 'InputStreamExhausted')

class SuspiciousOperation(Exception):
    """The user did something suspicious"""


class SuspiciousMultipartForm(SuspiciousOperation):
    """Suspect MIME request in multipart form data"""
    pass

class MultiPartParserError(Exception):
    pass


class InputStreamExhausted(Exception):
    """
    No more reads are allowed from this device.
    """
    pass

RAW = "raw"
FILE = "file"
FIELD = "field"

_BASE64_DECODE_ERROR = TypeError

class Iterator(object):

    def next(self):
        return type(self).__next__(self)

class MultiPartParser(object):
    """
    解析multipart/form-data类型的表单
    
    HTML中的表单按照enctype(编码类型)的不同可以分为3种：
    ① application/x-www-form-urlencoded；② multipart/form-data；③text/plain
    ①为默认编码，②为RFC2388为上传文件新加的数据类型
    
    解析结果为上传文件列表files,文本键值对post
    
    """
    def __init__(self, META, upload_handlers, encoding=None):
        """
        初始化MultiPartParser对象
        
        :META:
            uWSGI中的env对象，包含HTTP请求的元信息，头部信息以及body等
        :upload_handlers:
            上传文件处理器。文件上传的时候，文件内容是在http的body中的，服务器接收到之后
            需要先放在某个地方(内存或硬盘)，等用户来接收处理
        :encoding:
            接收数据的编码方式
        """
        
        content_type = META.get('HTTP_CONTENT_TYPE', META.get('CONTENT_TYPE', ''))
        # Content-Type应当包含entype信息以及boundary信息
        # 
        # 其中boundary一段随机串，用于分割form中的各个字段
        #
        # 比如：
        # 'CONTENT_TYPE': 'multipart/form-data; boundary=----WebKitFormBoundaryB9iAfLg1SnfmaPh5'
        
        if not content_type.startswith('multipart/'):
            raise MultiPartParserError('Invalid Content-Type: %s' % content_type)
        
        ctypes, opts = parse_header(content_type.encode('ascii'))   # 获取boundary值 
        # ctypes:multipart/form-data
        # opts: {boundary: ----WebKitFormBoundaryB9iAfLg1SnfmaPh5}
        
        boundary = opts.get('boundary')
        if not boundary or not cgi.valid_boundary(boundary):
            raise MultiPartParserError('Invalid boundary in multipart: %s' % boundary)

        # Content-Length should contain the length of the body we are about
        # to receive.
        try:
            content_length = int(META.get('HTTP_CONTENT_LENGTH', META.get('CONTENT_LENGTH', 0)))
        except (ValueError, TypeError):
            content_length = 0

        if content_length < 0:
            # This means we shouldn't continue...raise an error.
            raise MultiPartParserError("Invalid content length: %r" % content_length)

        if isinstance(boundary, unicode):
            boundary = boundary.encode('ascii')
            
        self._boundary = boundary
        self._input_data = META["wsgi.input"]

        # For compatibility with low-level network APIs (with 32-bit integers),
        # the chunk size should be < 2^31, but still divisible by 4.
        possible_sizes = [x.chunk_size for x in upload_handlers if x.chunk_size]
        self._chunk_size = min([2 ** 31 - 4] + possible_sizes)

        self._meta = META
        self._content_length = content_length
        self._upload_handlers = upload_handlers

    def parse(self):
        """
        解析表单数据，将普通字段以及FILE字段分别返回
        """

        encoding = self._encoding
        handlers = self._upload_handlers

        # HTTP spec says that Content-Length >= 0 is valid
        # handling content-length == 0 before continuing
        if self._content_length == 0:
            return {}, {}

        # See if any of the handlers take care of the parsing.
        # This allows overriding everything if need be.
        for handler in handlers:
            result = handler.handle_raw_input(self._input_data,
                                              self._meta,
                                              self._content_length,
                                              self._boundary,
                                              encoding)
            # Check to see if it was handled
            if result is not None:
                return result[0], result[1]

        # Create the data structures to be used later.
        self._post = {}
        self._files = {}

        # 按照chunk-size读取_input_data中的数据
        # Lazy的意思可能是打开的不是文件而是迭代器
        stream = LazyStream(ChunkIter(self._input_data, self._chunk_size))
        
        old_field_name = None   #上一次处理的字段
        counters = [0] * len(handlers)  #每一个upload handler处理的字节数

        try:
            for item_type, meta_data, field_stream in Parser(stream, self._boundary):
                if old_field_name:
                    # We run this at the beginning of the next loop
                    # since we cannot be sure a file is complete until
                    # we hit the next boundary/part of the multipart content.
                    self.handle_file_complete(old_field_name, counters)
                    old_field_name = None

                try:
                    disposition = meta_data['content-disposition'][1]
                    field_name = disposition['name'].strip()
                except (KeyError, IndexError, AttributeError):
                    continue

                transfer_encoding = meta_data.get('content-transfer-encoding')
                if transfer_encoding is not None:
                    transfer_encoding = transfer_encoding[0].strip()
                field_name = force_text(field_name, encoding, errors='replace')

                if item_type == FIELD:
                    # This is a post field, we can just set it in the post
                    if transfer_encoding == 'base64':
                        raw_data = field_stream.read()
                        try:
                            data = base64.b64decode(raw_data)
                        except _BASE64_DECODE_ERROR:
                            data = raw_data
                    else:
                        data = field_stream.read()

                    self._post.appendlist(field_name,
                                          force_text(data, encoding, errors='replace'))
                elif item_type == FILE:
                    # This is a file, use the handler...
                    file_name = disposition.get('filename')
                    if not file_name:
                        continue
                    file_name = force_text(file_name, encoding, errors='replace')
                    file_name = self.IE_sanitize(unescape_entities(file_name))

                    content_type, content_type_extra = meta_data.get('content-type', ('', {}))
                    content_type = content_type.strip()
                    charset = content_type_extra.get('charset')

                    try:
                        content_length = int(meta_data.get('content-length')[0])
                    except (IndexError, TypeError, ValueError):
                        content_length = None

                    counters = [0] * len(handlers)
                    try:
                        for handler in handlers:
                            try:
                                handler.new_file(field_name, file_name,
                                                 content_type, content_length,
                                                 charset, content_type_extra)
                            except StopFutureHandlers:
                                break

                        for chunk in field_stream:
                            if transfer_encoding == 'base64':
                                # We only special-case base64 transfer encoding
                                # We should always decode base64 chunks by multiple of 4,
                                # ignoring whitespace.

                                stripped_chunk = b"".join(chunk.split())

                                remaining = len(stripped_chunk) % 4
                                while remaining != 0:
                                    over_chunk = field_stream.read(4 - remaining)
                                    stripped_chunk += b"".join(over_chunk.split())
                                    remaining = len(stripped_chunk) % 4

                                try:
                                    chunk = base64.b64decode(stripped_chunk)
                                except Exception as e:
                                    # Since this is only a chunk, any error is an unfixable error.
                                    msg = "Could not decode base64 data: %r" % e
                                    six.reraise(MultiPartParserError, MultiPartParserError(msg), sys.exc_info()[2])

                            for i, handler in enumerate(handlers):
                                chunk_length = len(chunk)
                                chunk = handler.receive_data_chunk(chunk,
                                                                   counters[i])
                                counters[i] += chunk_length
                                if chunk is None:
                                    # If the chunk received by the handler is None, then don't continue.
                                    break

                    except SkipFile:
                        self._close_files()
                        # Just use up the rest of this file...
                        exhaust(field_stream)
                    else:
                        # Handle file upload completions on next iteration.
                        old_field_name = field_name
                else:
                    # If this is neither a FIELD or a FILE, just exhaust the stream.
                    exhaust(stream)
        except StopUpload as e:
            self._close_files()
            if not e.connection_reset:
                exhaust(self._input_data)
        else:
            # Make sure that the request data is all fed
            exhaust(self._input_data)

        # Signal that the upload has completed.
        for handler in handlers:
            retval = handler.upload_complete()
            if retval:
                break

        return self._post, self._files

    def handle_file_complete(self, old_field_name, counters):
        """
        Handle all the signaling that takes place when a file is complete.
        """
        for i, handler in enumerate(self._upload_handlers):
            file_obj = handler.file_complete(counters[i])
            if file_obj:
                # If it returns a file object, then set the files dict.
                self._files.appendlist(
                    force_text(old_field_name, self._encoding, errors='replace'),
                    file_obj)
                break

    def IE_sanitize(self, filename):
        """Cleanup filename from Internet Explorer full paths."""
        return filename and filename[filename.rfind("\\") + 1:].strip()

    def _close_files(self):
        # Free up all file handles.
        # FIXME: this currently assumes that upload handlers store the file as 'file'
        # We should document that... (Maybe add handler.free_file to complement new_file)
        for handler in self._upload_handlers:
            if hasattr(handler, 'file'):
                handler.file.close()


class LazyStream(Iterator):
    """
    LazyStream支持从迭代器里取元素，同时支持把取回的元素的再放回去
    """
    def __init__(self, producer, length=None):
        """
        producer是一个迭代器，每调用一次就返回一个字符串
        """
        self._producer = producer
        self._empty = False
        self._leftover = b''    #取出后右被放回来的字符串，leftover(剩余物,未用完的)
        self.length = length
        self.position = 0       #目前已读取到的位置
        self._remaining = length
        self._unget_history = []

    def tell(self):
        '''
        返回当前读取的位置
        '''
        return self.position

    def read(self, size=None):
        def parts():
            remaining = self._remaining if size is None else size
            
            # do the whole thing in one shot if no limit was provided.
            if remaining is None:
                yield b''.join(self)
                return

            # otherwise do some bookkeeping to return exactly enough
            # of the stream and stashing any extra content we get from
            # the producer
            while remaining != 0:
                assert remaining > 0, 'remaining bytes to read should never go negative'

                try:
                    chunk = next(self)
                except StopIteration:
                    return
                else:
                    emitting = chunk[:remaining]
                    self.unget(chunk[remaining:])
                    remaining -= len(emitting)
                    yield emitting

        out = b''.join(parts())
        return out

    def __next__(self):
        """
        读取一个chunk的数据(字节数不确定，效率较高)
        """
        if self._leftover:
            output = self._leftover
            self._leftover = b''
        else:
            output = next(self._producer)
            self._unget_history = []
        self.position += len(output)
        return output

    def close(self):
        """
        用来invalidate/disable这个lazy stream
        """
        self._producer = []

    def __iter__(self):
        return self

    def unget(self, bytes):
        """
        把取出来的元素再放回去
        """
        if not bytes:
            return
        self._update_unget_history(len(bytes))
        self.position -= len(bytes)
        self._leftover = b''.join([bytes, self._leftover])

    def _update_unget_history(self, num_bytes):
        """
        更新一下unget的历史记录，防止因为恶意攻击导致同一个元素返回取/放，
        如果同一个元素取放50次则抛出异常
        """
        self._unget_history = [num_bytes] + self._unget_history[:49]
        number_equal = len([current_number for current_number in self._unget_history
                            if current_number == num_bytes])

        if number_equal > 40:
            raise SuspiciousMultipartForm(
                "The multipart parser got stuck, which shouldn't happen with"
                " normal uploaded files. Check for malicious upload activity;"
                " if there is none, report this to the Django developers."
            )


class ChunkIter(Iterator):
    """
    file-like类型的迭代器，每次返回一个chunk-size的chunk
    """
    def __init__(self, flo, chunk_size=64 * 1024):
        self.flo = flo
        self.chunk_size = chunk_size

    def __next__(self):
        try:
            data = self.flo.read(self.chunk_size)
        except InputStreamExhausted:
            raise StopIteration()
        if data:
            return data
        else:
            raise StopIteration()

    def __iter__(self):
        return self


def exhaust(stream_or_iterable):
    """
    穷尽一个迭代器或文件
    """
    iterator = None
    try:
        iterator = iter(stream_or_iterable)
    except TypeError:
        iterator = ChunkIter(stream_or_iterable, 16384)

    if iterator is None:
        raise MultiPartParserError('multipartparser.exhaust() was passed a non-iterable or stream parameter')

    for __ in iterator:
        pass
        
class BoundaryIter(Iterator):
    """
    按照http body中的boundary，遍历各个字段
    """

    def __init__(self, stream, boundary):
        self._stream = stream
        self._boundary = boundary
        self._done = False
        # rollback an additional six bytes because the format is like
        # this: CRLF<boundary>[--CRLF]
        self._rollback = len(boundary) + 6

        # Try to use mx fast string search if available. Otherwise
        # use Python find. Wrap the latter for consistency.
        unused_char = self._stream.read(1)
        if not unused_char:
            raise InputStreamExhausted()
        self._stream.unget(unused_char)

    def __iter__(self):
        return self

    def __next__(self):
        if self._done:
            raise StopIteration()

        stream = self._stream
        rollback = self._rollback

        bytes_read = 0
        chunks = []
        for bytes in stream:
            bytes_read += len(bytes)
            chunks.append(bytes)
            if bytes_read > rollback:
                break
            if not bytes:
                break
        else:
            self._done = True

        if not chunks:
            raise StopIteration()

        chunk = b''.join(chunks)
        boundary = self._find_boundary(chunk, len(chunk) < self._rollback)

        if boundary:
            end, next = boundary
            stream.unget(chunk[next:])
            self._done = True
            return chunk[:end]
        else:
            # make sure we don't treat a partial boundary (and
            # its separators) as data
            if not chunk[:-rollback]:  # and len(chunk) >= (len(self._boundary) + 6):
                # There's nothing left, we should just return and mark as done.
                self._done = True
                return chunk
            else:
                stream.unget(chunk[-rollback:])
                return chunk[:-rollback]

    def _find_boundary(self, data, eof=False):
        """
        Finds a multipart boundary in data.

        Should no boundary exist in the data None is returned instead. Otherwise
        a tuple containing the indices of the following are returned:

         * the end of current encapsulation
         * the start of the next encapsulation
        """
        index = data.find(self._boundary)
        if index < 0:
            return None
        else:
            end = index
            next = index + len(self._boundary)
            # backup over CRLF
            last = max(0, end - 1)
            if data[last:last + 1] == b'\n':
                end -= 1
            last = max(0, end - 1)
            if data[last:last + 1] == b'\r':
                end -= 1
            return end, next

class InterBoundaryIter(Iterator):
    """
    遍历boundary的Producer
    """
    def __init__(self, stream, boundary):
        self._stream = stream
        self._boundary = boundary

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return LazyStream(BoundaryIter(self._stream, self._boundary))
        except InputStreamExhausted:
            raise StopIteration()
        

def parse_boundary_stream(stream, max_header_size):
    """
    Parses one and exactly one stream that encapsulates a boundary.
    """
    # Stream at beginning of header, look for end of header
    # and parse it if found. The header must fit within one
    # chunk.
    chunk = stream.read(max_header_size)

    # 'find' returns the top of these four bytes, so we'll
    # need to munch them later to prevent them from polluting
    # the payload.
    header_end = chunk.find(b'\r\n\r\n')

    def _parse_header(line):
        main_value_pair, params = parse_header(line)
        try:
            name, value = main_value_pair.split(':', 1)
        except ValueError:
            raise ValueError("Invalid header: %r" % line)
        return name, (value, params)

    if header_end == -1:
        # we find no header, so we just mark this fact and pass on
        # the stream verbatim
        stream.unget(chunk)
        return (RAW, {}, stream)

    header = chunk[:header_end]

    # here we place any excess chunk back onto the stream, as
    # well as throwing away the CRLFCRLF bytes from above.
    stream.unget(chunk[header_end + 4:])

    TYPE = RAW
    outdict = {}

    # Eliminate blank lines
    for line in header.split(b'\r\n'):
        # This terminology ("main value" and "dictionary of
        # parameters") is from the Python docs.
        try:
            name, (value, params) = _parse_header(line)
        except ValueError:
            continue

        if name == 'content-disposition':
            TYPE = FIELD
            if params.get('filename'):
                TYPE = FILE

        outdict[name] = value, params

    if TYPE == RAW:
        stream.unget(chunk)

    return (TYPE, outdict, stream)


class Parser(object):
    def __init__(self, stream, boundary):
        self._stream = stream
        self._separator = b'--' + boundary

    def __iter__(self):
        boundarystream = InterBoundaryIter(self._stream, self._separator)
        for sub_stream in boundarystream:
            # Iterate over each part
            yield parse_boundary_stream(sub_stream, 1024)


def parse_header(line):
    """
    将http请求行中的key=value解析为字典
    """
    plist = _parse_header_params(b';' + line)   #按分号把一行分割成多个字段，为什么不是split(;)?请看_parse_header_params的注释
    key = plist.pop(0).lower().decode('ascii')
    pdict = {}
    for p in plist:
        i = p.find(b'=')
        if i >= 0:
            has_encoding = False
            name = p[:i].strip().lower().decode('ascii')
            if name.endswith('*'):
                # Lang/encoding embedded in the value (like "filename*=UTF-8''file.ext")
                # http://tools.ietf.org/html/rfc2231#section-4
                name = name[:-1]
                if p.count(b"'") == 2:  #根据单引号数量判断是否指定了value的编码
                    has_encoding = True
                    
            value = p[i + 1:].strip()
            if has_encoding:    #如果指定了encoding,此进行解码
                encoding, lang, value = value.split(b"'")
                value = unquote(value).decode(encoding)
            
            #正则表达式相关，处理转义字符
            if len(value) >= 2 and value[:1] == value[-1:] == b'"':
                value = value[1:-1]
                value = value.replace(b'\\\\', b'\\').replace(b'\\"', b'"')
                
            pdict[name] = value
            
    return key, pdict


def _parse_header_params(s):
    '''
    按分号把http的一个请求行分割成数组
    '''
    plist = []
    while s[:1] == b';': #为什么不是s[0]？估计是因为s[0]会在s为空的报错，s[:1]不会
        s = s[1:]
        end = s.find(b';')
        #防止把一对双引号中通过分号分开，比如afafa;"dafafaf;dfafaf";dfafa中的第二个分号就不能当作分割符号
        while end > 0 and s.count(b'"', 0, end) % 2:
            end = s.find(b';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        plist.append(f.strip())
        s = s[end:]
    return plist


_hexdig = '0123456789ABCDEFabcdef'
_hextochr = dict((a + b, chr(int(a + b, 16)))
                 for a in _hexdig for b in _hexdig)
_asciire = re.compile('([\x00-\x7f]+)')
def unquote(s):
    """unquote('abc%20def') -> 'abc def'."""
    if isinstance(s, unicode):
        if '%' not in s:
            return s
        bits = _asciire.split(s)
        res = [bits[0]]
        append = res.append
        for i in range(1, len(bits), 2):
            append(unquote(str(bits[i])).decode('latin1'))
            append(bits[i + 1])
        return ''.join(res)

    bits = s.split('%')
    # fastpath
    if len(bits) == 1:
        return s
    res = [bits[0]]
    append = res.append
    for item in bits[1:]:
        try:
            append(_hextochr[item[:2]])
            append(item[2:])
        except KeyError:
            append('%')
            append(item)
    return ''.join(res)
