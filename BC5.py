#   //=====================================================================
#   // Copyright (c) 2018    Advanced Micro Devices, Inc. All rights reserved.
#   //
#   // Permission is hereby granted, free of charge, to any person obtaining a copy
#   // of this software and associated documentation files(the "Software"), to deal
#   // in the Software without restriction, including without limitation the rights
#   // to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
#   // copies of the Software, and to permit persons to whom the Software is
#   // furnished to do so, subject to the following conditions :
#   // 
#   // The above copyright notice and this permission notice shall be included in
#   // all copies or substantial portions of the Software.
#   // 
#   // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   // IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   // FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
#   // AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   // LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   // OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#   // THE SOFTWARE.
#   //
#   //=====================================================================


BLOCK_SIZE_4X4 = 16

#
#   compressedBlock: list of 2 uint32
#   returns: alphaBlock (list of 8 uint_8)
#

def DecompressAlphaBlock(compressedBlock):  # returns alphaBlock

    alphaBlock = [0,]*BLOCK_SIZE_4X4
    alpha = GetCompressedAlphaRamp(compressedBlock)

    for i in range(BLOCK_SIZE_4X4):
        if i < 5:
            index = (compressedBlock[0] & (0x7 << (16 + (i * 3)))) >> (16 + (i * 3))
        elif i > 5:
            index = (compressedBlock[1] & (0x7 << (2 + (i - 6) * 3))) >> (2 + (i - 6) * 3)
        else:
            index = (compressedBlock[0] & 0x80000000) >> 31
            index |= (compressedBlock[1] & 0x3) << 1

        alphaBlock[i] = alpha[index]
    return alphaBlock


#
#   compressedBlock: list of 4 uint32
#   returns: list of tuples of srcR and srcG (list of 16 tuples of 2 uint_8)
#

def DecompressBC5_DualChannel_Internal(compressedBlock):
    srcBlockR = DecompressAlphaBlock(compressedBlock[0:2])
    srcBlockG = DecompressAlphaBlock(compressedBlock[2:4])
    result = [(srcBlockR[x],srcBlockG[x]) for x in range(BLOCK_SIZE_4X4)]
    return result


def snorm(val):
    if val & 0x80:
        return (-128 + (val & 0x7f)) / 128
    else:
        return (val & 0x7f) / 127

#
#   compressedBlock: list of 2 uint32
#   returns: alpha (list of 8 uint_8)
#

def GetCompressedAlphaRamp(compressedBlock):    # returns alpha
    alpha = [0,]*8

    alpha[0] = snorm((compressedBlock[0] & 0xff))
    alpha[1] = snorm(((compressedBlock[0] >> 8) & 0xff))

    #print(f"alpha 1: {alpha[0]} alpha 2: {alpha[1]}")
    if alpha[0] > alpha[1]:
        # 8-alpha block:  derive the other six alphas.
        # Bit code 000 = alpha_0, 001 = alpha_1, others are interpolated.

        alpha[2] = ((6 * alpha[0] + 1 * alpha[1]) / 7)    # bit code 010
        alpha[3] = ((5 * alpha[0] + 2 * alpha[1]) / 7)    # bit code 011
        alpha[4] = ((4 * alpha[0] + 3 * alpha[1]) / 7)    # bit code 100
        alpha[5] = ((3 * alpha[0] + 4 * alpha[1]) / 7)    # bit code 101
        alpha[6] = ((2 * alpha[0] + 5 * alpha[1]) / 7)    # bit code 110
        alpha[7] = ((1 * alpha[0] + 6 * alpha[1]) / 7)    # bit code 111

    else:
        alpha[2] = ((4 * alpha[0] + 1 * alpha[1]) / 5)    # Bit code 010
        alpha[3] = ((3 * alpha[0] + 2 * alpha[1]) / 5)    # Bit code 011
        alpha[4] = ((2 * alpha[0] + 3 * alpha[1]) / 5)    # Bit code 100
        alpha[5] = ((1 * alpha[0] + 4 * alpha[1]) / 5)    # Bit code 101
        alpha[6] = -1.0                                           # Bit code 110
        alpha[7] = 0                                         # Bit code 111
    return alpha