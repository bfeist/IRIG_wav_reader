import os
import datetime

# def secondsToGET(totalSeconds):
#     a = datetime.timedelta(seconds=totalSeconds)
#     return str(a)

def secondsToGET(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)


def GET_to_seconds(locGET):
    splitTimestamp = locGET.split(":")
    totalSeconds = (int(splitTimestamp[0]) * 60 * 60) + (int(splitTimestamp[1]) * 60) + int(splitTimestamp[2])
    return totalSeconds


inputFilePath = "E:/Apollo_11_Data_Delivery/concatenated_wav_files/defluttered/"
for dirname in os.listdir(inputFilePath):
    print("dir: " + dirname)
    for filename in os.listdir(inputFilePath + dirname):
        if filename[-8:] == "IRIG.csv":
            print("csv filename: " + filename)
            with open(inputFilePath + dirname + "/" + filename) as f:
                first_line = f.readline()
                second_line = f.readline()
                print(second_line)
                data_list = second_line.split("|")
                seconds_into_file = float(data_list[0])
                GET = data_list[6]
                print(str(seconds_into_file) + " - " + GET)
                startGET = secondsToGET(GET_to_seconds(GET) - seconds_into_file)

                print('startGET: ' + startGET)
