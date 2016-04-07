from subprocess import Popen, PIPE

# parses git command:
# git log --pretty=format:"####%x09%an%x09%at" --numstat --diff-filter=AM

gStringDict = {}   
def memoizeString(s):
    global gStringDict
    if s not in gStringDict:
        val = len(gStringDict)
        gStringDict[s] = val
        return val
    else:
        return gStringDict[s]

def parseInt(s):
    try:
        return int(s)
    except:
        return 0

#
# finding connected components in graphs
#

# nodeToComponentMap = {} # map of node ID -> graph component ID
# componentNodes = {} # map of component ID -> list of nodes

# node1, node2 are ints. Use memoizeString to convert strings to ints
def addEdge(node1, node2, components, nodeToComponentMap):
    if node1 not in nodeToComponentMap:
        # new node, gets its own graph component
        assert node1 not in components
        components[node1] = {node1}
        nodeToComponentMap[node1] = node1

    if node2 not in nodeToComponentMap:
        # new node, gets its own graph component
        assert node2 not in components
        components[node2] = {node2}
        nodeToComponentMap[node2] = node2

    component1 = nodeToComponentMap[node1]
    component2 = nodeToComponentMap[node2]
    minComponent = min(component1, component2)
    maxComponent = max(component1, component2)

    if minComponent == maxComponent:
        return 
        
    components[minComponent] |= components[maxComponent]
    for node in components[maxComponent]:
        nodeToComponentMap[node] = minComponent
    components[maxComponent] = set()
    
def getNodeToComponentMap(componentNodes):
    result = {}
    for componentId in componentNodes:
        nodes = componentNodes[componentId]
        for node in nodes:
            result[node] = componentId
    return result

#
#
#    
def getGetDiffFromEmptySummary(gitDirectory):
    emptyTreeSha = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    handle = Popen(['git', '-C', gitDirectory, 'diff', '--shortstat', emptyTreeSha], shell=True, stdout=PIPE)
    out, err = handle.communicate()
    return out.split('\n')

def getGitLog(gitDirectory, useCommiters=False):
    personFlag = 'c' if useCommiters else 'a'
    handle = Popen(['git', '-C', gitDirectory, 'log', '--all', '--pretty=format:####%x09%{0}n%x09%{0}e%x09%{0}t'.format(personFlag), '--numstat', '--diff-filter=AM'], shell=True, stdout=PIPE)
    out, err = handle.communicate()
    return out.split('\n')
 
 
 

def getTuple(username, filename, weekId):
    # return (memoizeString(username), memoizeString(filename), weekId)
    return (memoizeString(username), weekId)

class FileInfo(object):
    def __init__(self, additions, deletions, filename):
        self.additions = additions
        self.deletions = deletions
        self.filename = filename

class Commit(object):
    def __init__(self, user, email, time, week):
        self.user = user
        self.email = email
        self.time = time
        self.week = week
        self.fileInfo = []
            

def processLog(lines):
    commits = []
    
    # a commit looks like this: [username, email, time, week, [numAdditions, numDeletions, filename]]
    currentCommit = None
    for line in lines:
        parts = line.split('\t')
        if(line.startswith('####')):
            if currentCommit:
                commits.append(currentCommit)
            user = parts[1][:50] 
            email = parts[2][:50] 
            time = int(parts[3])
            week = int(time / (60*60*24*7))
            currentCommit = Commit(user, email, time, week)
        elif len(line) > 1:
            numAdditions = parseInt(parts[0])
            numDeletions = parseInt(parts[1])
            filename = parts[2]
            currentCommit.fileInfo.append(FileInfo(numAdditions, numDeletions, filename))
    if currentCommit:
        commits.append(currentCommit)            
    return commits
        
def summarizeLog(commits):
    uniqueTuples = set()
    uniqueUsers = set()
    uniqueEmails = set()
    totalLinesAdded = 0
    totalLines = 0

    for commit in commits:
        currentUser = commit.user
        currentEmail = commit.email
        currentTime = commit.time
        currentWeek = commit.week
        
        uniqueUsers.add(currentUser)
        uniqueEmails.add(currentEmail)
        for fileInfo in commit.fileInfo:
            numAdditions = fileInfo.additions
            numDeletions = fileInfo.deletions
            filename = fileInfo.filename
            uniqueTuples.add(getTuple(currentUser, filename, currentWeek))
            totalLinesAdded += numAdditions
            totalLines += (numAdditions-numDeletions)
    return len(uniqueTuples), len(uniqueUsers), totalLines, totalLinesAdded

def printTimeEstimate(gitDirectory, useCommiters=False):
    gitlog = getGitLog(gitDirectory, useCommiters)
    commits = processLog(gitlog)

    uniqueThings, uniqueUsers, totalLines, totalLineEdits = summarizeLog(commits)
    print "{} person-weeks of effort\t{} total line-edits by\t{} authors.".format(uniqueThings, totalLineEdits, uniqueUsers)

    # find graph
    components = {}
    nodeToComponentMap = {}
    for commit in commits:
        userId = memoizeString(commit.user)
        emailId = memoizeString(commit.email)
        addEdge(userId, emailId, components, nodeToComponentMap)

    components = [c for c in components if components[c]] # strip out empty components
    numComponents = len(components)
    print "Num unique authors: {}".format(numComponents)
    
    print getGetDiffFromEmptySummary(gitDirectory)[0]

def writeLines(lines, outFile):
    if outFile:
        with open(outFile, 'w') as fp:
            fp.writelines([line + '\n' for line in lines])
    else:
        for line in lines:
            print line

def getUniqueComponents(gitDirectory, outFile=None, useCommiters=False):
    gitlog = getGitLog(gitDirectory, useCommiters)
    commits = processLog(gitlog)        
    pairs = set()
    
    # find graph
    components = {}
    nodeToComponentMap = {}
    for commit in commits:
        userId = memoizeString(commit.user)
        emailId = memoizeString(commit.email)
        addEdge(userId, emailId, components, nodeToComponentMap)

    components = [c for c in components if components[c]] # strip out empty components
    numComponents = len(components)
    print "Num unique components: {}".format(numComponents)
    print
    
    for commit in commits:
        pairs.add((commit.user, commit.email))

#    print "User, email pairs:"
#    for pair in pairs:
#        print "{}\t{}".format(pair[0], pair[1])

def getUsernames(gitDirectory, outFile=None, useCommiters=False):
    gitlog = getGitLog(gitDirectory, useCommiters)
    commits = processLog(gitlog)        
    users = set()
    
    for commit in commits:
        users.add((commit.user, memoizeString(commit.user)))

    users = sorted(users)
    print "{} unique usernames".format(len(users))
    writeLines([entry[0] for entry in users], outFile)
            
def getEmails(gitDirectory, outFile=None):
    gitlog = getGitLog(gitDirectory)
    commits = processLog(gitlog)        
    emails = set()
        
    for commit in commits:
        emails.add((commit.email, memoizeString(commit.email)))

    emails = sorted(emails)
    print "{} unique emails".format(len(emails))
    writeLines([entry[0] for entry in emails], outFile)
        
if __name__ == '__main__':
    getUsernames('.')