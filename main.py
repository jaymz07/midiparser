from mido import MidiFile, MetaMessage
import sys

DEFAULT_TEMPO = 0.5

ARDUINO_CODE_MODE = False
NUM_NOTES_TO_OUTPUT = None


def ticks2s(ticks, tempo, ticks_per_beat):
    """
        Converts ticks to seconds
    """
    return ticks/ticks_per_beat * tempo


def note2freq(x):
    """
        Convert a MIDI note into a frequency (given in Hz)
    """
    a = 440
    return (a/32) * (2 ** ((x-9)/12))

def commandLineHelp():
    print("Usage:\npython main.py {-a} {-n NUM_NOTES} inputfile.mid\n")
    print("-a, --arduino\t\t\tOutput textfile as list of tone(outPin, freq, duration); calls that can be pasted into arduino sketch.\n")
    print("-n, --num-notes\t[NUM_NOTES]\tOnly output the first NUM_NOTES that have duration greater than zero into output file\n")
    print("-h, --help\t\t\tDisplay this help")


if __name__ == '__main__':

    
    # Parse command line options
    if(len(sys.argv) < 2):
        commandLineHelp()
        sys.exit(1)
    for i in range(1,len(sys.argv)-1):
        if(  sys.argv[i] in ['-a', '--arduino']):
            print("Arduino code output mode enabled")
            ARDUINO_CODE_MODE = True
            
        elif(sys.argv[i] in ['-n', '--num-notes']):
            try:
                NUM_NOTES_TO_OUTPUT = int(sys.argv[i+1])
            except ValueError:
                print("-n option takes an INTEGER as an argument. Ex.\npython [filename].py -n 100")
            print("Only outputting first %d notes" % NUM_NOTES_TO_OUTPUT)
        
        elif(sys.argv[i] in ['-h', '--help']):
            commandLineHelp()
            sys.exit(0)
            
    # Import the MIDI file...    
    mid = MidiFile(sys.argv[-1])
    print("TYPE: " + str(mid.type))
    print("LENGTH: " + str(mid.length))
    print("TICKS PER BEAT: " + str(mid.ticks_per_beat))

    if mid.type == 3:
        print("Unsupported type.")
        exit()

    """
        First read all the notes in the MIDI file
    """

    tracksMerged = []
    notes = {}

    for i, track in enumerate(mid.tracks):
        tempo = DEFAULT_TEMPO
        totaltime = 0
        print("Track: " + str(i))

        for message in track:
            t = ticks2s(message.time, tempo, mid.ticks_per_beat)
            totaltime += t

            if isinstance(message, MetaMessage):  # Tempo change
                if message.type == "set_tempo":
                    tempo = message.tempo / 10**6
                elif message.type == "end_of_track":
                    pass
                else:
                    print("Unsupported metamessage: " + str(message))

            else:  # Note
                if message.type == "control_change" or \
                   message.type == "program_change":
                    pass

                elif message.type == "note_on" or message.type == "note_off":
                    if message.note not in notes:
                        notes[message.note] = 0
                    if message.type == "note_on" and message.velocity != 0:
                        notes[message.note] += 1
                        if(notes[message.note] == 1):
                            tracksMerged += \
                                [(totaltime, message.note, message.velocity)]

                    else:
                        notes[message.note] -= 1
                        if(notes[message.note] == 0):
                            tracksMerged += \
                                [(totaltime, message.note, message.velocity)]

                else:
                    print(message)

        print("totaltime: " + str(totaltime)+"s")

    """
        Now merge all the tracks alltogether
    """

    tracksMerged = sorted(tracksMerged, key=lambda x: x[0])
    music = []

    for i in range(len(tracksMerged)-1):
        a = tracksMerged[i][0]
        b = tracksMerged[i+1][0]
        t = round(b-a, 3)
        m = tracksMerged[i]
        music += [(m[0], t, round(note2freq(m[1])), m[2])]
    """
        Finally write it in CSV format in a file
    """

    he = ""
    
    if(not ARDUINO_CODE_MODE):
        for msg in music:
            he += str(msg[0])+"," + str(msg[1]) + "," +str(msg[2])+","+str(msg[3])+"\n"
    else:
        nloop = len(music)
        if(NUM_NOTES_TO_OUTPUT is not None):
            nloop = NUM_NOTES_TO_OUTPUT
        count = 0
        i = 0
        while count < nloop and i < len(music):
            msg = music[i]
            if(msg[1] > 0):
                he += "tone(outPin, " + str(msg[2]) + ", " +str(int(msg[1]*1000)) + ");\n"
                count += 1
            i += 1
    f = open("./music.csv", "w")
    if(not ARDUINO_CODE_MODE):
        f.write("#Total Time,Note Len,note2freq,velocity\n")
    f.write(he)
    f.close()
