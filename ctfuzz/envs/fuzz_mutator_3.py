# libFuzzer

from random import randint, shuffle
import struct

def Rand(a):
    if a == 0:
        return 0
    else:
        return randint(0, a-1) # [0, a-1]

def isdigit(a):
    return ord('0') <= a <= ord('9')

class FuzzMutator3():
    def __init__(self, maxSize, userDict=None):
        self.maxSize = maxSize
        self.userDict = userDict
        self.funcMap = {
            0: self.Mutate_EraseBytes,
            1: self.Mutate_InsertByte,
            2: self.Mutate_InsertRepeatedBytes,
            3: self.Mutate_ChangeByte,
            4: self.Mutate_ChangeBit,
            5: self.Mutate_ShuffleBytes,
            6: self.Mutate_ChangeASCIIInteger,
            7: self.Mutate_ChangeBinaryInteger,
            8: self.Mutate_CopyPart,
        }
        self.setupMap = {
            0: self.Setup_EraseBytes,
            1: self.Setup_InsertByte,
            2: self.Setup_InsertRepeatedBytes,
            3: self.Setup_ChangeByte,
            4: self.Setup_ChangeBit,
            5: self.Setup_ShuffleBytes,
            6: self.Setup_ChangeASCIIInteger,
            7: self.Setup_ChangeBinaryInteger,
            8: self.Setup_CopyPart,
        }
        self.methodNum = len(self.funcMap)

        self.kMinBytesToInsert = 3

        # Temp saving
        self.tmpData = b''
        self.tmpAction = -1
        self.tmpIndex = 0
        self.tmpIndex2 = 0
        self.tmpSize = 0
        self.tmpByte = 0
        self.replace = 0

    def Mutate_EraseBytes(self):
        data = self.tmpData
        data_size = len(data)
        # n = Rand(len(data) // 2) + 1
        # s = Rand(len(data) - n + 1)
        n = self.tmpIndex
        s = self.tmpSize
        res = data[0:s] + data[s+n:]

        self.tmpIndex += 1
        if self.tmpIndex + self.tmpSize > data_size:
            self.tmpIndex = 0
            self.tmpSize += 1
            if self.tmpSize > data_size:
                self.tmpSize = 1

        return res

    def Mutate_InsertByte(self):
        data = self.tmpData
        data_size = len(data)

        # b = Rand(256)
        # s = Rand(len(data) + 1)
        b = self.tmpByte
        s = self.tmpIndex
        l = list(data)
        l.insert(s, b)
        
        self.tmpIndex += 1
        if self.tmpIndex > data_size:
            self.tmpIndex = 0
            self.tmpByte = (self.tmpByte + 1) % 256

        return bytes(l)

    def Mutate_InsertRepeatedBytes(self):
        data = self.tmpData
        data_size = len(data)
        # MaxBytesToInsert = min(self.maxSize - len(data), 128)
        # repeatedTimes = kMinBytesToInsert + Rand(MaxBytesToInsert - kMinBytesToInsert + 1)
        # bs = [Rand(256)] * repeatedTimes
        # s = Rand(len(data) + 1)
        bs = [self.tmpByte] * self.tmpSize
        s = self.tmpIndex
        l = list(data)
        tmpl = l[0 : s] + bs + l[s :]

        self.tmpByte += 1
        if self.tmpByte == 256:
            self.tmpByte = 0
            self.tmpIndex += 1
            if self.tmpIndex > data_size:
                self.tmpIndex = 0
                self.tmpSize += 1
                if self.tmpSize > self.MaxBytesToInsert:
                    self.tmpSize = self.kMinBytesToInsert

        return bytes(tmpl)
            
    def Mutate_ChangeByte(self):
        data = self.tmpData
        data_size = len(data)

        # b = Rand(256)
        # s = Rand(len(data))
        b = self.tmpByte
        s = self.tmpIndex
        l = list(data)
        l[s] = b

        self.tmpByte += 1
        if self.tmpByte == 256:
            self.tmpByte = 0
            self.tmpIndex = (self.tmpIndex + 1) % data_size

        return bytes(l)

    def Mutate_ChangeBit(self):
        data = self.tmpData
        data_size = len(data)

        # s = Rand(len(data))
        s = self.tmpIndex
        shift = self.tmpShift
        l = list(data)
        # l[s] ^= 1 << Rand(8)
        l[s] ^= 1 << shift

        self.tmpShift += 1
        if self.tmpShift == 8:
            self.tmpShift = 0
            self.tmpIndex = (self.tmpIndex + 1) % data_size

        return bytes(l)   

    def Mutate_ShuffleBytes(self):
        data = self.tmpData
        data_size = len(data)
        if data_size <= 8:
            l = list(data)
            shuffle(l)
            return bytes(l)
        else:
            ShuffleAmount = Rand(min(8, len(data))) + 1
            ShuffleStart = Rand(len(data) - ShuffleAmount)
            # ShuffleAmount = self.tmpSize
            # ShuffleStart = self.tmpIndex
            l = list(data)
            tmpl = l[ShuffleStart : ShuffleStart + ShuffleAmount]
            shuffle(tmpl)
            l[ShuffleStart : ShuffleStart + ShuffleAmount] = tmpl
            return bytes(l)

    def Mutate_ChangeASCIIInteger(self):
        data = self.tmpData
        data_size = len(data)

        B = Rand(data_size)
        while (B < data_size and not isdigit(data[B])): B += 1
        if B == data_size:
            return data
        else:
            E = B + 1
            while (E < data_size and isdigit(data_size)): E += 1
            l = list(data)
            digitl = l[B:E]
            val = int(bytes(digitl))

            sw = Rand(5)
            if sw == 0:  val += 1
            elif sw == 1: val -= 1
            elif sw == 2:  val //= 2
            elif sw == 3: val *= 2
            else: val = Rand(val*val)

            digitl = [0] * len(digitl)
            de = len(digitl) - 1
            for v in str(val)[::-1]:
                if de < 0:
                    break
                digitl[de] = ord(v)
                de -= 1

            l[B:E] = digitl
            return bytes(l)

    def Mutate_ChangeBinaryInteger(self):
        data = self.tmpData
        data_size = len(data)
        nd = 2 ** (Rand(4))  # 1 2 4 8
        
        if nd == 1:
            fmt = 'B'
        elif nd == 2:
            fmt = 'H'
        elif nd == 4:
            fmt = 'I'
        else:
            fmt = 'Q'
        
        if data_size < nd:
            return data
        else:
            val = []
            Off = Rand(data_size - nd + 1)
            l = list(data)
            if Off < 64 and not Rand(4):
                size = data_size % (1 << 8 * nd)
                val = list(struct.pack('<' + fmt, size)) # x86小端序
                if Rand(1):
                    val = list(struct.pack('>' + fmt, size))  # 转为大端序
            else:
                val = struct.unpack('<' + fmt, bytes(l[Off:Off + nd]))[0]
                Add = Rand(21) - 10
                if Rand(1):
                    bval = struct.pack('>' + fmt, val) # 大端序pack，小端序unpack来实现__builtin_bswap
                    val += struct.unpack('<' + fmt, bval)[0]
                    val += Add
                    val = val % (1 << 8 * nd)
                    bval = struct.pack('>' + fmt, val)
                    val += struct.unpack('<' + fmt, bval)[0]
                else:
                    val += Add
                if Add == 0 or Rand(0):
                    val = -val
                val = val % (1 << 8 * nd)
                val = list(struct.pack('<' + fmt, val))

            l[Off:Off + nd] = val

            return bytes(l)

    def Mutate_CopyPart(self):
        data = self.tmpData
        data_size = len(data)

        # ToBeg = Rand(len(data))
        # FromBeg = Rand(len(data))
        # CopySize = Rand(min(len(data) - FromBeg, self.maxSize - len(data)))
        ToBeg = self.tmpIndex2
        FromBeg = self.tmpIndex
        CopySize = self.tmpSize
        l = list(data)
        tmpl = l[FromBeg : FromBeg + CopySize]
        if self.replace: # 1
            l = l[0:ToBeg] + tmpl + l[ToBeg+CopySize:]
        else: # 0
            l = l[0:ToBeg] + tmpl + l[ToBeg:]

        self.replace = (self.replace + 1) % 2
        if self.replace == 0:
            self.tmpIndex2 += 1
            if self.tmpIndex2 > data_size:
                self.tmpIndex2 = 0
                self.tmpIndex += 1
                if self.tmpIndex + self.tmpSize > data_size:
                    self.tmpIndex = 0
                    self.tmpSize = (self.tmpSize + 1) % min(data_size, self.maxSize - data_size)

        return bytes(l)
        
    def Setup_EraseBytes(self, data, max_try):
        data_size = len(data)
        if data_size == 0:
            return 0, 0
        
        max_possible = (data_size * (data_size + 1) // 2)
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpSize = 0
        else:
            self.tmpSize = Rand(data_size // 2) + 1
            self.tmpIndex = Rand(data_size - self.tmpSize + 1)

        return max_try, max_try / max_possible

    def Setup_InsertByte(self, data, max_try):
        data_size = len(data)
        if data_size >= self.maxSize:
            return 0, 0
        
        max_possible = (data_size + 1) * 256
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpByte = 0
        else:
            self.tmpIndex = Rand(data_size + 1)
            self.tmpByte = Rand(256)

        return max_try, max_try / max_possible

    def Setup_InsertRepeatedBytes(self, data, max_try):
        data_size = len(data)
        if data_size + self.kMinBytesToInsert > self.maxSize:
            return 0, 0
        
        self.MaxBytesToInsert = min(self.maxSize - data_size, 128)
        max_possible = (data_size + 1) * self.MaxBytesToInsert * (self.MaxBytesToInsert + 1) // 2 * 256
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpByte = 0
            self.tmpSize = 1
        else:
            self.tmpIndex = Rand(data_size + 1)
            self.tmpByte = Rand(256)
            self.tmpSize = self.kMinBytesToInsert + Rand(self.MaxBytesToInsert - self.kMinBytesToInsert + 1)

        return max_try, max_try / max_possible
            
    def Setup_ChangeByte(self, data, max_try):
        data_size = len(data)
        if data_size > self.maxSize or data_size == 0:
            return 0, 0
        
        max_possible = (data_size) * 256
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpByte = 0
        else:
            self.tmpIndex = Rand(data_size)
            self.tmpByte = Rand(256)

        return max_try, max_try / max_possible

    def Setup_ChangeBit(self, data, max_try):
        data_size = len(data)
        if data_size > self.maxSize or data_size == 0:
            return 0, 0
        
        max_possible = (data_size) * 8
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpShift = 0
        else:
            self.tmpIndex = Rand(data_size)
            self.tmpShift = Rand(8)

        return max_try, max_try / max_possible

    def Setup_ShuffleBytes(self, data, max_try):
        data_size = len(data)
        if data_size > self.maxSize or data_size == 0:
            return 0, 0
        
        if data_size <= 8:
            return 2000, 1

        return max_try, 1

    def Setup_ChangeASCIIInteger(self, data, max_try):
        data_size = len(data)
        if data_size > self.maxSize or data_size == 0:
            return 0, 0
        
        if data_size <= 8:
            return 2000, 1

        return max_try, 1

    def Setup_ChangeBinaryInteger(self, data, max_try):
        return max_try, 1

    def Setup_CopyPart(self, data, max_try):
        data_size = len(data)
        if data_size > self.maxSize or data_size == 0:
            return 0, 0
        
        max_possible = data_size * data_size * (min(data_size, self.maxSize - data_size))
        max_try = min(max_try, max_possible)
        if max_try == max_possible:
            self.tmpIndex = 0
            self.tmpIndex2 = 0
            self.tmpSize = 1
        else:
            self.tmpIndex = Rand(data_size)
            self.tmpIndex2 = Rand(data_size)
            self.tmpSize = Rand(min(data_size - self.tmpIndex, self.maxSize - data_size))

        return max_try, max_try / max_possible

    def run_action(self, action, data, max_try):
        max_try = max(int(max_try), 1)
        assert(0 <= action < self.methodNum)

        # Setup mutator and return max_possible, and percent possible
        self.tmpAction = action
        self.tmpData = data        
        setupFunc = self.setupMap[action]
        return setupFunc(data, max_try)

        # Test
        # self.tmpData = data
        # self.tmpTry = max_try
        # self.tmpAction = action
        # return max_try, 1

    def next(self):
        if 0 <= self.tmpAction < self.methodNum:            
            mutatorFunc = self.funcMap[self.tmpAction]
            return mutatorFunc()[:self.maxSize]
        return b''

    def Get_action_table_size(self):
        return self.methodNum
