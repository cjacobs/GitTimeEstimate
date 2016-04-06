

# parses git command:
# git log --pretty=format:"#### %ae %at" --name-status

def parseFile(filename):
    lines = []
    with open(filename) as fp:
        lines = fp.readlines()

    # TODO: keep a record of unique user, week, filename triplets
    # map from (username,week) -> set(filename) would work
    # so would set(username, week, filename)
    map = {}
    uniqueTriplets = set()
    currentUser = ''
    currentTime = 0 # in seconds
    currentWeek = 0
    for line in lines:
        parts = line.split()
        if(line.startswith('####')):
            currentUser = parts[1]
            currentTime = int(parts[2])
            currentWeek = int(currentTime / (60*60*24*7))
        elif len(line) > 1:
            operation = parts[0]
            filename = parts[1]
            print "{}\t{}\t{}\t{}".format(currentUser, currentWeek, operation, filename)    