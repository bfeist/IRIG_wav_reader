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


pVal = [1, 2, 4, 8, 0, 10, 20, 40, 80, 0, 100, 200]
tSeconds = 0
tMinutes = 0
tHours = 0
tDays = 0
tYears = 0

blocksize = 8  # 8 = 1ms
overlap = 0

#filename = 'irig_frame_sample.wav'
#filename = 'irig_multiframe_sample.wav'
filename = 'irig_sample_10m.wav'
rms_threshold = 0.2
signal_ms_duration = 0
block_count = 0
last_bit = ''
bits = ''
frame_segment_started = True
frame_segments = []
frame_start_time_secs = 0

# print(get_int_by_binary('11100101'))

for block in sf.blocks(filename, blocksize=blocksize, overlap=overlap):
    block_count += 1
    rms = np.sqrt(np.mean(block**2))
    # print(rms)
    if rms > rms_threshold:
        signal_ms_duration += 1
    elif signal_ms_duration > 1: #  signal has dropped down - figure out what kind it is and add the appropriate bit
        bit = ptype(signal_ms_duration)

        if bit == "R":
            if last_bit == "R":  # double R - start new frame
                if len(frame_segments) == 10:  # If previous frame is not malformed, decode it
                    tSeconds = get_int_by_binary(frame_segments[0])
                    tMinutes = get_int_by_binary(frame_segments[1])
                    tHours = get_int_by_binary(frame_segments[2])
                    tDays = get_int_by_binary(frame_segments[3])
                    # Add the additional day bits in segment 4
                    tDays = tDays + int(frame_segments[4][0]) * pVal[10] + int(frame_segments[4][1]) * pVal[11]
                    tYears = get_int_by_binary(frame_segments[5])
                    ctrl_funcs = frame_segments[6] + frame_segments[7] #  unused part of IRIG spec
                    binary_tod = frame_segments[8] + frame_segments[9]
                    print('Seconds since file start: ' + "%.2f" % frame_start_time_secs, end='')
                    print(' | IRIG time: ' + str(tDays).zfill(3) + ':' + str(tHours).zfill(2) + ':' + str(tMinutes).zfill(2) + ':' + str(tSeconds).zfill(2) + ' | in seconds: ' + str(tHours*60*60 + tMinutes*60 + tSeconds))
                # else:
                #     print(' | IRIG time: malformed')

                # print("New Frame")
                frame_start_time_secs = (block_count - overlap) / 1000
                frame_segments = []
                frame_segment_started = True

            else:  # frame segment over. push bits into frame_segments list
                frame_segment_started = False
                frame_segments.append(bits)
                bits = ''
        else:
            bits = bits + bit  # add the current bit to the current segment bit queue

        last_bit = bit

        # #print frame bits
        # if bit == "R":
        #     print(bit)
        # elif bit != '':
        #     print(bit, end='')

        if signal_ms_duration > 0:
            signal_ms_duration = 0

    # if block_count >= 500000:
    #     break