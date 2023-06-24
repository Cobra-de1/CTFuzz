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

class FuzzMutator2():
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

        # Temp saving
        self.tmpData = b''
        self.tmpAction = -1
        self.tmpTry = 0
        self.tmpIndex = 0
        self.tmpSize = 0
        self.tmpByte = b'\x00'

    def Mutate_EraseBytes(self):
        data = self.tmpData
        if len(data) > 0:
            n = Rand(len(data) // 2) + 1
            s = Rand(len(data) - n + 1)
            return data[0:s] + data[s+n:]
        else:
            return data

    def Mutate_InsertByte(self):
        data = self.tmpData
        if len(data) >= self.maxSize:
            return data
        else:
            b = Rand(256)
            s = Rand(len(data) + 1)
            l = list(data)
            l.insert(s, b)
            return bytes(l)

    def Mutate_InsertRepeatedBytes(self):
        data = self.tmpData
        kMinBytesToInsert = 3
        if kMinBytesToInsert + len(data) >= self.maxSize:
            return data
        else:
            MaxBytesToInsert = min(self.maxSize - len(data), 128)
            repeatedTimes = kMinBytesToInsert + Rand(MaxBytesToInsert - kMinBytesToInsert + 1)
            bs = [Rand(256)] * repeatedTimes
            s = Rand(len(data) + 1)
            l = list(data)
            tmpl = l[0 : s] + bs + l[s :]
            return bytes(tmpl)
            
    def Mutate_ChangeByte(self):
        data = self.tmpData
        if len(data) > self.maxSize or len(data) == 0:
            return data
        else:
            b = Rand(256)
            s = Rand(len(data))
            l = list(data)
            l[s] = b
            return bytes(l)

    def Mutate_ChangeBit(self):
        data = self.tmpData
        if len(data) > self.maxSize or len(data) == 0:
            return data
        else:
            s = Rand(len(data))
            l = list(data)
            l[s] ^= 1 << Rand(8)
            return bytes(l)

    def Mutate_ShuffleBytes(self):
        data = self.tmpData
        if len(data) > self.maxSize or len(data) == 0:
            return data
        else:
            ShuffleAmount = Rand(min(8, len(data))) + 1
            ShuffleStart = Rand(len(data) - ShuffleAmount)
            l = list(data)
            tmpl = l[ShuffleStart : ShuffleStart + ShuffleAmount]
            shuffle(tmpl)
            l[ShuffleStart : ShuffleStart + ShuffleAmount] = tmpl
            return bytes(l)

    def Mutate_ChangeASCIIInteger(self):
        data = self.tmpData
        if len(data) > self.maxSize or len(data) == 0:
            return data
        else:
            B = Rand(len(data))
            while (B < len(data) and not isdigit(data[B])): B += 1
            if B == len(data):
                return data
            else:
                E = B + 1
                while (E < len(data) and isdigit(data[E])): E += 1
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
        nd = 2 ** (Rand(4))  # 1 2 4 8
        
        if nd == 1:
            fmt = 'B'
        elif nd == 2:
            fmt = 'H'
        elif nd == 4:
            fmt = 'I'
        else:
            fmt = 'Q'
        
        if len(data) < nd:
            return data
        else:
            val = []
            Off = Rand(len(data) - nd + 1)
            l = list(data)
            if Off < 64 and not Rand(4):
                size = len(data) % (1 << 8 * nd)
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
        if len(data) > self.maxSize or len(data) == 0:
            return data
        else:
            ToBeg = Rand(len(data))
            FromBeg = Rand(len(data))
            CopySize = Rand(min(len(data) - FromBeg, self.maxSize - len(data)))
            l = list(data)
            tmpl = l[FromBeg : FromBeg + CopySize]
            if Rand(1): # 1
                l = l[0:ToBeg] + tmpl + l[ToBeg+CopySize:]
            else: # 0
                l = l[0:ToBeg] + tmpl + l[ToBeg:]
            return bytes(l)
        
    def Setup_EraseBytes(self, data, max_try):
        pass

    def Setup_InsertByte(self, data, max_try):
        pass    

    def Setup_InsertRepeatedBytes(self, data, max_try):
        pass
            
    def Setup_ChangeByte(self, data, max_try):
        pass

    def Setup_ChangeBit(self, data, max_try):
        pass

    def Setup_ShuffleBytes(self, data, max_try):
        pass

    def Setup_ChangeASCIIInteger(self, data, max_try):
        pass

    def Setup_ChangeBinaryInteger(self, data, max_try):
        pass

    def Setup_CopyPart(self, data, max_try):
        pass

    def run_action(self, action, data, max_try):
        assert(max_try > 0)
        # Setup mutator and return max_possible, and percent possible
        assert(0 <= action < self.methodNum)
        # setupFunc = self.setupMap[action]
        # return setupFunc(data, max_try)

        # Test
        self.tmpData = data
        self.tmpTry = max_try
        self.tmpAction = action
        return max_try, 1

    def next(self):
        if 0 <= self.tmpAction < self.methodNum:            
            mutatorFunc = self.funcMap[self.tmpAction]
            return mutatorFunc()[:self.maxSize]
        return b''

    def Get_action_table_size(self):
        return self.methodNum
