import numpy as np
import soundfile as sf

# Converts length of a pulse to binary 0/1 or a 'R' for a reference/position frame

def ptype(len):
    if len >= 9:
        return 'R'
    elif len <= 4 and len > 1:
        return '0'
    elif len < 9 and len > 4:
        return '1'
    else:
        return ''

# Sums up bits stored within the bits queue


def get_int_by_binary(bits):
    csum = 0
    while len(bits) > 0:
        bits, cbit = bits[:-1], bits[-1]
        csum += int(cbit) * (pVal[len(bits)])
    return csum


def parseBits(bits, position):  #  Parse data received until this position, at this point we should parse...
    if position == 0:                     #  ...seconds
        return get_int_by_binary(bits)

    elif position == 1:                     #  ...minutes
        return get_int_by_binary(bits)

    elif position == 2:                     #  ...hours
        return get_int_by_binary(bits)

    elif position == 3:                     #  ...days
        return get_int_by_binary(bits)

    elif position == 4:                     #  ...days continued - handled elsewhere
        pass

    elif position == 5:                     #  ...years
        return get_int_by_binary(bits)

    # elif position == 6:                     #  At this point, we have all time data recorded. Set variables based on anticipated time.
    #     if tSeconds + 1 == 60:
    #         tSeconds = 0
    #         tMinutes += 1
    #
    #     seconds = tSeconds
    #     secondM = tSecondM
    #
    #     if tMinutes == 60:
    #         tMinutes = 0
    #         tHours += 1
    #
    #     minutes = tMinutes
    #
    #     if tHours == 24:
    #         tHours = 0
    #         tDays += 1
    #
    #     hours = tHours
    #
    #     if tDays == 367:  #  This does not take into account leap years, and has yet to be tested.
    #         tDays = 0
    #         tYears += 1
    #
    #     days = tDays
    #
    #     years = tYears

#  lastUpdatedAt = millis() - 700; #  Time last received at current time, -700 ms for position marker 7


pVal = [1, 2, 4, 8, 0, 10, 20, 40, 80, 0, 100, 200]
tSeconds = 0
tMinutes = 0
tHours = 0
tDays = 0
tYears = 0

blocksize = 8  # 8 = 1ms
#filename = 'irig_frame_sample.wav'
filename = 'irig_multiframe_sample.wav'
rms_threshold = 0.2
signal_ms_duration = 0
block_count = 0
last_bit = ''
bits = ''
frame_segment_started = True
frame_segments = []

# print(get_int_by_binary('11100101'))

for block in sf.blocks(filename, blocksize=blocksize, overlap=1):
    block_count += 1
    rms = np.sqrt(np.mean(block**2))
    # print(rms)
    if rms > rms_threshold:
        signal_ms_duration += 1
    else:
        bit = ptype(signal_ms_duration)

        if bit == "R":
            if last_bit == "R":  # double R - start new frame
                if len(frame_segments) == 10:  # If frame is complete, decode it
                    tSeconds = parseBits(frame_segments[0], 0)
                    tMinutes = parseBits(frame_segments[1], 1)
                    tHours = parseBits(frame_segments[2], 2)
                    tDays = parseBits(frame_segments[3], 3)
                    # Add the additional day bits in segment 4
                    tDays = tDays + int(frame_segments[4][0]) * 100 + int(frame_segments[4][1]) * 200
                    tYears = parseBits(frame_segments[5], 5)
                    ctrl_funcs = frame_segments[6] + frame_segments[7] #  unused part of IRIG spec
                    binary_tod = frame_segments[8] + frame_segments[9]

                    print

                print("New Frame")
                frame_start_time_secs = block_count / 1000
                frame_segments = []
                frame_segment_started = True

            else:  # frame segment over. push bits into frame_segments list
                frame_segment_started = False
                frame_segments.append(bits)
                bits = ''
        else:
            bits = bits + bit  # add the current bit to the current segment bit queue

        last_bit = bit

        if bit == "R":
            print(bit)
        else:
            print(bit, end='')

        if signal_ms_duration > 0:
            signal_ms_duration = 0
