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
        if len(bits) <= len(pVal):
            csum += int(cbit) * (pVal[len(bits)])
        else:
            csum = 0
            break
    return csum


pVal = [1, 2, 4, 8, 0, 10, 20, 40, 80, 0, 100, 200]
tSeconds = 0
tMinutes = 0
tHours = 0
tDays = 0
tYears = 0

blocksize = 8  # 8 = 1ms
overlap = 0

# filename = 'irig_frame_sample.wav'
# filename = 'irig_multiframe_sample.wav'
# filename = 'irig_sample_10m.wav'
# filename = 'E:/Apollo_11_Data_Delivery/concatenated_wav_files/T870/defluttered_linear_A11_T870_HR2L_CH31.wav'
# filename = 'E:/Apollo_11_Data_Delivery/concatenated_wav_files/T869/A11_T869_HR1U_CH1.wav'
filename = 'E:/Apollo_11_Data_Delivery/concatenated_wav_files/T869/defluttered_linear_A11_T869_HR1U_CH1.wav'

output_file_name_and_path = "T869_defluttered_irig.csv"
outputFile = open(output_file_name_and_path, "w")
outputFile.write('file_seconds|file_seconds_diff|IRIG_time|IRIG_in_seconds|irig_seconds_diff|file_to_irig_seconds_diff\n')
outputFile.close()

rms_threshold = 0.2
signal_ms_duration = 0
block_count = 0
last_bit = ''
bits = ''
frame_segment_started = True
frame_segments = []
frame_start_time_secs = 0
decoded_time_count = 0
first_seconds_decoded = 0
first_seconds_file = 0

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
                    if decoded_time_count % 10 == 0:
                        outputFile = open(output_file_name_and_path, "a")

                        tSeconds = get_int_by_binary(frame_segments[0])
                        tMinutes = get_int_by_binary(frame_segments[1])
                        tHours = get_int_by_binary(frame_segments[2])
                        tDays = get_int_by_binary(frame_segments[3])
                        # Add the additional day bits in segment 4
                        tDays = tDays + int(frame_segments[4][0]) * pVal[10] + int(frame_segments[4][1]) * pVal[11]
                        tYears = get_int_by_binary(frame_segments[5])
                        ctrl_funcs = frame_segments[6] + frame_segments[7] #  unused part of IRIG spec
                        binary_tod = frame_segments[8] + frame_segments[9]
                        irig_in_seconds = tHours * 60 * 60 + tMinutes * 60 + tSeconds
                        if first_seconds_decoded == 0:
                            first_seconds_decoded = irig_in_seconds
                            first_seconds_file = frame_start_time_secs

                        irig_seconds_differential = irig_in_seconds - first_seconds_decoded
                        file_seconds_differential = frame_start_time_secs - first_seconds_file
                        file_to_irig_seconds_diff = file_seconds_differential - irig_seconds_differential
                        output_string = 'Seconds since file start: %.3f' % frame_start_time_secs
                        output_string = output_string + ' | {0:.3f}'.format(file_seconds_differential)
                        output_string = output_string + ' | IRIG time: {0}:{1}:{2}:{3} | in seconds: {4} | {5} | {6}'.format(str(tDays).zfill(3), str(tHours).zfill(2), str(tMinutes).zfill(2), str(tSeconds).zfill(2), irig_in_seconds, irig_seconds_differential, file_to_irig_seconds_diff)
                        print(output_string)

                        outputLine = '{0}|{1:.3f}|{2}|{3}|{4}|{5}\n'.format(frame_start_time_secs, file_seconds_differential, str(tDays).zfill(3) + ':' + str(tHours).zfill(2) + ':' + str(tMinutes).zfill(2) + ':' + str(tSeconds).zfill(2), irig_in_seconds, irig_seconds_differential, file_to_irig_seconds_diff)
                        outputFile.write(outputLine)
                        outputFile.close()
                    decoded_time_count += 1
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

    # if block_count >= 100000:
    #     break

