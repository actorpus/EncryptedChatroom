import random
from typing import *


class bit128:
    def __init__(self, initialise=None):
        if initialise is None:
            initialise = [[0x00 for _ in range(4)] for _ in range(4)]

        self._grid = initialise

    def fill_bytes(self, data: bytes):
        if len(data) > 16:
            raise ValueError("cannot fill from bytes > 16")

        data = data.ljust(16, b'\x00')

        for i in range(16):
            self[i] = data[i]

    def __bytes__(self):
        return b''.join([bytes(_) for _ in self._grid])

    def get_bytes(self):
        return self.__bytes__()

    def __str__(self):
        out = ""

        for column in self._grid:
            out += "\n"
            for piece in column:
                out += hex(piece)[2:].rjust(2, "0") + " "

        return out[1:]  # remove 1st \n

    def __getitem__(self, item: Union[int, Tuple[int, int], slice]):
        if type(item) == int:
            return self._grid[item // 4][item % 4]
        elif type(item) == tuple:
            return self._grid[item[1]][item[0]]
        elif type(item) == slice:
            return self[item.start, 0], self[item.start, 1], self[item.start, 2], self[item.start, 3]

    def __setitem__(self, key, value):
        if type(key) == int:
            self._grid[key // 4][key % 4] = value
        elif type(key) == tuple:
            self._grid[key[1]][key[0]] = value
        elif type(key) == slice:
            self[key.start, 0] = value[0]
            self[key.start, 1] = value[1]
            self[key.start, 2] = value[2]
            self[key.start, 3] = value[3]

    def shift_row(self, row: int, i: int):
        for _ in range(i):
            a, b, c, d = self._grid[row]

            self._grid[row] = [b, c, d, a]

    def fill_random(self):
        for yi, y in enumerate(self._grid):
            for xi, x in enumerate(y):
                self[xi, yi] = random.randint(0, 255)

    @staticmethod
    def sub_byte(byte):
        s_box = [
            [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76],
            [0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0],
            [0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15],
            [0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75],
            [0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84],
            [0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf],
            [0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8],
            [0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2],
            [0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73],
            [0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb],
            [0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79],
            [0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08],
            [0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a],
            [0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e],
            [0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf],
            [0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]
        ]

        return s_box[byte >> 4][byte & 0x0F]

    @staticmethod
    def un_sub_byte(byte):
        s_box = [
            0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
            0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
            0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
            0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
            0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
            0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
            0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
            0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
            0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
            0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
            0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
            0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
            0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
            0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
            0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
            0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
        ]

        return ((s_box.index(byte) // 16) << 4) + s_box.index(byte) % 16

    def auto_sub(self):
        for x in range(4):
            for y in range(4):
                self[x, y] = self.sub_byte(self[x, y])

    def auto_un_sub(self):
        for x in range(4):
            for y in range(4):
                self[x, y] = self.un_sub_byte(self[x, y])

    def auto_shift(self):
        self.shift_row(1, 1)
        self.shift_row(2, 2)
        self.shift_row(3, 3)

    def auto_un_shift(self):
        self.shift_row(1, 3)
        self.shift_row(2, 2)
        self.shift_row(3, 1)

    def __xor__(self, other):
        out = bit128()

        for x in range(4):
            for y in range(4):
                out[x, y] = self[x, y] ^ other[x, y]

        return out

    def __or__(self, other):
        out = bit128()

        for x in range(4):
            for y in range(4):
                out[x, y] = self[x, y] | other[x, y]

        return out

    def __invert__(self):
        out = bit128()

        for x in range(4):
            for y in range(4):
                out[x, y] = 255 - self[x, y]

        return out

    def ixor(self, other):
        for x in range(4):
            for y in range(4):
                self[x, y] = self[x, y] ^ other[x, y]

    def __ior__(self, other):
        for x in range(4):
            for y in range(4):
                self[x, y] = self[x, y] | other[x, y]

    def invert(self):
        for x in range(4):
            for y in range(4):
                self[x, y] = 255 - self[x, y]

    def expand(self, i=10):
        keys = [self]
        rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

        for _ in range(i):
            keys.append(bit128())

            # 0
            word = rot_word(keys[_][3:])
            word = [self.sub_byte(__) for __ in word]
            word = [word[i] ^ keys[_][0:][i] for i in range(4)]
            word[0] ^= rcon[_]
            keys[_ + 1][0:] = word

            # 1, 2, 3
            for __ in range(3):
                keys[_ + 1][__ + 1:] = [keys[_][__ + 1:][___] ^ keys[_ + 1][__:][___] for ___ in range(4)]

        return keys[1:]

    def auto_mix_columns(self):
        for c in range(4):
            self[c:] = [
                special_multiply(self[c:][0], 2) ^ special_multiply(self[c:][1], 3) ^ special_multiply(self[c:][2], 1) ^ special_multiply(self[c:][3], 1),
                special_multiply(self[c:][0], 1) ^ special_multiply(self[c:][1], 2) ^ special_multiply(self[c:][2], 3) ^ special_multiply(self[c:][3], 1),
                special_multiply(self[c:][0], 1) ^ special_multiply(self[c:][1], 1) ^ special_multiply(self[c:][2], 2) ^ special_multiply(self[c:][3], 3),
                special_multiply(self[c:][0], 3) ^ special_multiply(self[c:][1], 1) ^ special_multiply(self[c:][2], 1) ^ special_multiply(self[c:][3], 2)
            ]


def rot_word(word):
    return list(word[1:]) + [word[0]]


def special_multiply(a, b):
    if b == 1:
        return a

    tmp = (a << 1) & 0xff

    if b == 2:
        return tmp if a < 127 else tmp ^ 0x1b

    if b == 3:
        return tmp ^ a if a < 127 else (tmp ^ 0x1b) ^ a


def print_mul(bits):
    out = [[], [], [], []]

    for b in bits:
        b = b.__str__().split("\n")

        for _ in range(4):
            out[_].append(b[_])

    out = "\n".join([" ".join(_) for _ in out])

    print(out)


def encrypt(data: bytes, key: bit128):
    data += b'\x00' * (16 - len(data) % 16)
    plain_data = [data[_*16:_*16+16] for _ in range(len(data) // 16)]
    encrypted_data = []

    round_keys = key.expand()

    for data in plain_data:
        plain = bit128()
        plain.fill_bytes(data)

        # print("main key:")
        # print(main_key)
        # print()
        #
        # print("round keys:")
        # print_mul(round_keys)
        # print()
        #
        # print("raw data:")
        # print(plain)
        # print()

        # INITIAL ROUND
        cypher = plain ^ key  # add initial round key

        # 9 MAIN ROUNDS
        for round_i in range(9):
            cypher.auto_sub()  # substitute bytes

            cypher.auto_shift()  # shift rows

            cypher.auto_mix_columns()  # mix columns

            cypher.ixor(round_keys[round_i])  # add round key

        # FINAL ROUND
        cypher.auto_sub()
        cypher.auto_shift()
        cypher.ixor(round_keys[9])

        # print("encrypted data")
        # print(cypher)
        # print()

        encrypted_data.append(cypher.get_bytes())

    return b''.join(encrypted_data)


def decrypt(data: bytes, key: bit128):
    encrypted_data = [data[_ * 16:_ * 16 + 16] for _ in range(len(data) // 16)]

    round_keys = key.expand()

    for data in encrypted_data:
        data = bit128.fill_bytes(bit128(), data)

        # FINAL ROUND
        cypher = round_keys[9] ^ data
        cypher.auto_un_shift()
        cypher.auto_un_sub()

        for round_i in range(9):
            cypher.ixor(round_keys[8 - round_i])

            cypher.auto_mix_columns()

            cypher.auto_un_shift()

            cypher.auto_un_sub()


encryption_key = bit128()
encryption_key.fill_bytes(b'\x8f45r|\xab*\x953K\xf7\x90\x9b\x9f\xcc\x83')  # random data

print(encrypt(b'hello world! how are we doin?', encryption_key))

