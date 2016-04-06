from subprocess import Popen, PIPE



# parses git command:
# git log --pretty=format:"#### %ae %at" --name-status
## better:

# git log --pretty=format:"####%x09%an%x09%at" --numstat --diff-filter=AM


def estimateTime(directory):
    gitlog = callGit(directory)
    lines = gitlog.split('\n')
    uniqueThings = parseLines(lines)
    print "{} person-weeks of effort".format(len(uniqueThings))
    # return uniqueThings    

def callGit(directory):
    handle = Popen(['git', '-C', directory, 'log', '--all', '--pretty=format:####%x09%an%x09%at', '--numstat', '--diff-filter=AM'], shell=True, stdout=PIPE)    
    out, err = handle.communicate()
    return out
    
gStringDict = {}
def memoizeString(s):
    global gStringDict
    if s not in gStringDict:
        val = len(gStringDict)
        gStringDict[s] = val
        return val
    else:
        return gStringDict[s]
        
def getTuple(username, filename, weekId):
    # return (memoizeString(username), memoizeString(filename), weekId)
    return (memoizeString(username), weekId)

def parseFile(filename):
    lines = []
    with open(filename) as fp:
        lines = fp.readlines()
    return parseLines(lines)
    
def parseLines(lines):
    # TODO: keep a record of unique user, week, filename triplets
    # map from (username,week) -> set(filename) would work
    # so would set(username, week, filename)
    uniqueTuples = set()
    currentUser = ''
    currentTime = 0 # in seconds
    currentWeek = 0
    for line in lines:
        parts = line.split('\t')
        if(line.startswith('####')):
            currentUser = parts[1]
            currentTime = int(parts[2])
            currentWeek = int(currentTime / (60*60*24*7))
        elif len(line) > 1:
            numAdds = parts[0]
            subSub = parts[1]
            filename = parts[2]
            uniqueTuples.add(getTuple(currentUser, filename, currentWeek))
    return uniqueTuples
    