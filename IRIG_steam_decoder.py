import soundfile as sf

filename = 'irig_frame_sample.wav'
soundob = sf.SoundFile(filename)
sr = soundob.samplerate

print(sr)