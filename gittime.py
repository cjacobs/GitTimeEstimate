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

class Graph(object):
    def __init__(self):
        self.components = {}
        self.nodeToComponentMap = {}

    # node1, node2 are ints. Use memoizeString to convert strings to ints    
    def addEdge(self, node1, node2):
        if node1 not in self.nodeToComponentMap:
            # new node, gets its own graph component
            assert node1 not in self.components
            self.components[node1] = {node1}
            self.nodeToComponentMap[node1] = node1

        if node2 not in self.nodeToComponentMap:
            # new node, gets its own graph component
            assert node2 not in self.components
            self.components[node2] = {node2}
            self.nodeToComponentMap[node2] = node2

        component1 = self.nodeToComponentMap[node1]
        component2 = self.nodeToComponentMap[node2]
        minComponent = min(component1, component2)
        maxComponent = max(component1, component2)

        if minComponent == maxComponent:
            return 
            
        self.components[minComponent] |= self.components[maxComponent]
        for node in self.components[maxComponent]:
            self.nodeToComponentMap[node] = minComponent
        self.components[maxComponent] = set()

    def numComponents(self):   
        return len([c for c in self.components if self.components[c]]) # strip out empty components
        
    def getComponent(self, node):
        return self.nodeToComponentMap[node]
#
#
# 

# returns # files, line additions
def getGitDiffStatsFromEmptySummary(gitDirectory):
    emptyTreeSha = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    handle = Popen(['git', '-C', gitDirectory, 'diff', '--shortstat', emptyTreeSha], shell=True, stdout=PIPE)
    out, err = handle.communicate()
    # "xxx files changed, yyy insertions"
    parts = out.split(',')
    return int(parts[0].split()[0]), int (parts[1].split()[0])

def getGitLog(gitDirectory, useCommiters=False):
    personFlag = 'c' if useCommiters else 'a'
    handle = Popen(['git', '-C', gitDirectory, 'log', '--all', '--pretty=format:####%x09%{0}n%x09%{0}e%x09%{0}t'.format(personFlag), '--numstat', '--diff-filter=AM'], shell=True, stdout=PIPE)
    out, err = handle.communicate()
    return out.split('\n')

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
        
def summarizeLog(commits, excludeDirs=[]):
    def exclude(filename):
        for dir in excludeDirs:
            if filename.startswith(dir):
                return True
        return False

    uniqueTuples = set()
    uniqueUsers = set()
    uniqueEmails = set()
    totalLinesAdded = 0
    totalLinesDeleted = 0

    ## TODO: use the graph to get unique users
    graph = Graph()
    for commit in commits:
        userId = memoizeString(commit.user)
        emailId = memoizeString(commit.email)
        graph.addEdge(userId, emailId)
    
    for commit in commits:
        uniqueUsers.add(commit.user)
        uniqueEmails.add(commit.email)
        for fileInfo in commit.fileInfo:
            filename = fileInfo.filename
            if not exclude(filename):
                currentUserId = graph.getComponent(memoizeString(commit.user))
                uniqueTuples.add((currentUserId, commit.week))
                totalLinesAdded += fileInfo.additions
                totalLinesDeleted += fileInfo.deletions
                
    return len(uniqueTuples), graph.numComponents(), totalLinesAdded, totalLinesDeleted

def printTimeEstimate(gitDirectory, useCommiters=False, excludeDirs=[]):
    gitlog = getGitLog(gitDirectory, useCommiters)
    commits = processLog(gitlog)

    uniqueThings, uniqueUsers, totalLinesAdded, totalLinesDeleted = summarizeLog(commits, excludeDirs)
    print "person-weeks of effort: {}\ttotal line-edits: {}\tby {} authors.".format(uniqueThings, totalLinesAdded, uniqueUsers)
    
    filesChanged, linesAdded = getGitDiffStatsFromEmptySummary(gitDirectory)
    print "# files: {}\tlines added: {}".format(filesChanged, linesAdded)
    print
    
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
    
    # find graph
    graph = Graph()
    for commit in commits:
        userId = memoizeString(commit.user)
        emailId = memoizeString(commit.email)
        graph.addEdge(userId, emailId)

    print "Num unique components: {}".format(graph.numComponents())
    
def getUsernames(gitDirectory, outFile=None, useCommiters=False):
    gitlog = getGitLog(gitDirectory, useCommiters)
    commits = processLog(gitlog)        
    users = set([commit.user for commit in commits])
    print "{} unique usernames".format(len(users))
    writeLines(sorted(users), outFile)
            
def getEmails(gitDirectory, outFile=None):
    gitlog = getGitLog(gitDirectory)
    commits = processLog(gitlog)        
    emails = set([commit.email for commit in commits])
    print "{} unique emails".format(len(emails))
    writeLines(sorted(emails), outFile)
        
if __name__ == '__main__':
    getUsernames('.')
