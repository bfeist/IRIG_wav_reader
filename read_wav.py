import numpy as np
import soundfile as sf

blocksize = 8  # 8 = 1ms

filename = 'irig_frame_sample.wav'

# Converts length of a pulse to binary 0/1 or a 'R' for a reference/position frame


def ptype(len):
    if len >= 9:
        return 'R'
    elif len <= 3 and len > 1:
        return 0
    elif len < 9 and len > 3:
        return 1
    else:
        return ''

rms_threshold = 0.2
signal_ms_duration = 0
block_count = 0
for block in sf.blocks(filename, blocksize=blocksize, overlap=1):
    block_count += 1
    rms = np.sqrt(np.mean(block**2))
    # print(rms)
    if rms > rms_threshold:
        signal_ms_duration += 1
    else:
        # if signal_ms_duration > 0:
        #     print("signal length: " + str(signal_ms_duration) + " ms")
        # if signal_ms_duration > 9:
        #     print("M")
        #     # print(str(block_count) + " ms")
        # elif signal_ms_duration > 4:
        #     print("1", end='')
        # elif signal_ms_duration > 2:
        #     print("0", end='')
        type = ptype(signal_ms_duration)

        if type == "R":
            print(type)
        else:
            print(type, end='')

        if signal_ms_duration > 0:
            signal_ms_duration = 0
