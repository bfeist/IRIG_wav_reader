import numpy as np
import soundfile as sf
import os
import sys
# import psutil
import math

# p = psutil.Process(os.getpid())
# p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)


def get_arg(index):
    try:
        sys.argv[index]
    except IndexError:
        return ''
    else:
        return sys.argv[index]


def ptype(len):
    # Converts length of a pulse to binary 0/1 or a 'R' for a reference/position frame
    # ~8ms is an R frame
    # ~5ms is a 1
    # ~3ms is a 0
    if len >= 9:
        return 'R'
    elif len <= 4 and len > 1:
        return '0'
    elif len < 9 and len > 4:
        return '1'
    else:
        return ''


def get_int_by_binary(bits): # Sums up bits stored within the bits queue
    csum = 0
    while len(bits) > 0:
        bits, cbit = bits[:-1], bits[-1]
        try:
            csum += int(cbit) * (pVal[len(bits)])
        except Exception as e:
            # print("type error: " + str(e))
            csum = 0
            break
    return csum

def GET_by_UTC(irig_time):
    apollo11_launch_time = "197:13:32:01"
    launch_seconds = seconds_by_UTC(apollo11_launch_time)
    irig_seconds = seconds_by_UTC(irig_time)
    seconds_since_launch = irig_seconds - launch_seconds
    return HMS_by_seconds(seconds_since_launch)

def HMS_by_seconds(input_seconds):
    hours = abs(int(input_seconds / 3600))
    minutes = abs(int(input_seconds / 60)) % 60 % 60
    seconds = abs(int(input_seconds)) % 60
    seconds = math.floor(seconds)
    hms_string = str(hours).zfill(3) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)
    if input_seconds < 0:
        hms_string = "-" + hms_string
    return hms_string

def seconds_by_UTC(UTC_time):
    UTCList = UTC_time.split(':')
    if len(UTCList) == 4:
        seconds = int(UTCList[0]) * 24 * 60 * 60
        seconds += int(UTCList[1]) * 60 * 60
        seconds += int(UTCList[2]) * 60
        seconds += int(UTCList[3])
    else:
        seconds = 0
    return int(seconds)


pVal = [1, 2, 4, 8, 0, 10, 20, 40, 80, 0, 100, 200]
tSeconds = 0
tMinutes = 0
tHours = 0
tDays = 0
tYears = 0

# arguments to select tape directory, tweak RMS threshold for bit detection, and skip x first seconds if the first decoded frame is malformed
tape = get_arg(1)

if get_arg(2) == 'E':
    datafile_path = 'E:/Apollo_11_Data_Delivery/concatenated_wav_files/defluttered/'
else:
    datafile_path = 'F:/'

if get_arg(3) == '':
    rms_threshold = 0.20
else:
    rms_threshold = float(get_arg(3))

if get_arg(4) == '':
    skip_first_seconds = 0
else:
    skip_first_seconds = int(get_arg(4))

if get_arg(5) == '':
    bitrate = 8
else:
    bitrate = int(get_arg(5))

if get_arg(6) == '':
    record_every_nth = 10
else:
    record_every_nth = int(get_arg(6))

locdirlisting = os.listdir(datafile_path + '/' + tape)

channel1_filename = ''
for locfile in locdirlisting:
    if "CH1.wav" in locfile:
        channel1_filename = locfile
        break

filename = datafile_path + tape + '/' + channel1_filename

output_file_name_and_path = datafile_path + tape + '/' + channel1_filename[:-8] + "_IRIG.csv"
outputFile = open(output_file_name_and_path, "w")
outputFile.write('file_seconds|file_seconds_diff|IRIG_time|IRIG_in_seconds|irig_seconds_diff|file_to_irig_seconds_diff|GET\n')
outputFile.close()

# make a file in adobe marker format for import into Premiere or Audition. Will place markers containing decoded GET locations
marker_output_file_name_and_path = datafile_path + tape + '/' + channel1_filename[:-8] + "_adobe_markers.csv"
markerFile = open(marker_output_file_name_and_path, "w")
markerFile.write('Name\tStart\tDuration Time\tFormat\tType\tDescription\n')
markerFile.close()

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

blocksize = bitrate  # 8 = 1ms for 8khz soundfile
overlap = 0

# loop through sound file 1ms at a time
for block in sf.blocks(filename, blocksize=blocksize, overlap=overlap):
    block_count += 1
    rms = np.sqrt(np.mean(block**2))
    # print(rms)
    if rms > rms_threshold:
        signal_ms_duration += 1 # count duration that this signal lasts 1ms at a time
    elif signal_ms_duration > 1: #  signal has dropped down - figure out what kind it is and add the appropriate bit
        bit = ptype(signal_ms_duration)
        if bit == "R":
            if last_bit == "R":  # double R - IRIG frame start found
                if len(frame_segments) == 10:  # If previous frame is not malformed, decode it
                    if frame_start_time_secs > skip_first_seconds:
                        # Only analyze and print every x successfully decoded frame if seconds to skip parameter provided, only start after that parameter
                        outputFile = open(output_file_name_and_path, "a")
                        markerFile = open(marker_output_file_name_and_path, "a")

                        # decode the 8 different portions of the IRIG frame
                        # see this reference for IRIG format:
                        # https://ferrara.space/content/images/2017/02/IRIG-B-1.png
                        tSeconds = get_int_by_binary(frame_segments[0])
                        tMinutes = get_int_by_binary(frame_segments[1])
                        tHours = get_int_by_binary(frame_segments[2])
                        tDays = get_int_by_binary(frame_segments[3])
                        # Add the additional day bits in segment 4
                        try:
                            tDays = tDays + int(frame_segments[4][0]) * pVal[10] + int(frame_segments[4][1]) * pVal[11]
                        except Exception as e:
                            # bad. I really don't care if this tDays increment works. It's more important that nothing crashes
                            pass
                        tYears = get_int_by_binary(frame_segments[5])
                        ctrl_funcs = frame_segments[6] + frame_segments[7] #  unused part of IRIG spec
                        binary_tod = frame_segments[8] + frame_segments[9]

                        # derive time variables from IRIG data. Compare decoded time with actual wav file time to measure wav speed drift
                        irig_in_seconds = tDays * 24 * 60 * 60 + tHours * 60 * 60 + tMinutes * 60 + tSeconds
                        if first_seconds_decoded == 0:
                            first_seconds_decoded = irig_in_seconds
                            first_seconds_file = frame_start_time_secs

                        irig_seconds_differential = irig_in_seconds - first_seconds_decoded
                        file_seconds_differential = frame_start_time_secs - first_seconds_file
                        file_to_irig_seconds_diff = file_seconds_differential - irig_seconds_differential
                        irig_time = '{0}:{1}:{2}:{3}'.format(str(tDays).zfill(3), str(tHours).zfill(2), str(tMinutes).zfill(2), str(tSeconds).zfill(2))

                        output_string = 'Seconds since file start: %.3f' % frame_start_time_secs
                        output_string = output_string + ' | {0:.3f}'.format(file_seconds_differential)
                        output_string = output_string + ' | IRIG time: {0} | in seconds: {1} | {2} | {3} | GET {4}'.format(irig_time, irig_in_seconds, irig_seconds_differential, file_to_irig_seconds_diff, GET_by_UTC(irig_time))

                        outputLine = '{0}|{1:.3f}|{2}|{3}|{4}|{5}|{6}\n'.format(frame_start_time_secs, file_seconds_differential,
                                                                            irig_time, irig_in_seconds, irig_seconds_differential, file_to_irig_seconds_diff, GET_by_UTC(irig_time))
                        # Name\tStart\tDuration Time\tFormat\tType\tDescription\n
                        markerLine = '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n'.format(GET_by_UTC(irig_time), HMS_by_seconds(frame_start_time_secs), "0:00:00", "decimal", "Cue", "GET error (seconds): " + str(file_to_irig_seconds_diff))

                        print(output_string)
                        # Only write line if the UTC is likely to be correct (time diff between IRIG and file time not too much).
                        # Only works with defluttered NASA 30-track files. Otherwise the drift can be 1000s of seconds.
                        if file_to_irig_seconds_diff < 10 and file_to_irig_seconds_diff > -10:
                            outputFile.write(outputLine)
                            outputFile.close()
                            if decoded_time_count % record_every_nth == 0:
                                markerFile.write(markerLine)
                                markerFile.close()
                                print("marker record written")

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

        # print raw frame bits - uncomment this to see the ugly details. Helps in determining best RMS threshold parameter
        # if bit == "R":
        #     print(bit + '-' + str(len(frame_segments)))
        # elif bit != '':
        #     print(bit, end='')

        if signal_ms_duration > 0:
            signal_ms_duration = 0

    # if block_count >= 100000:
    #     break