# CMake generator for Unreal Engine Projects
# by LordSk
import os
import xml.etree.ElementTree as ET

# find project name
projectDir = input("Enter project directory: ").replace("\\", "/")
fileList = os.listdir(projectDir)

fnUproject = None
for f in fileList:
	if f.endswith(".uproject"):
		fnUproject = f
		break
		
projectName = fnUproject.split(".")[0]
print("Project name: ", projectName)
print("Opening visual studio file...")

# parse visual studio file
fileVS = open(projectDir + "/Intermediate/ProjectFiles/" + projectName + ".vcxproj", "rb")
fileBuff = fileVS.read()
fileVS.close()

print("Parsing...")

# remove namespace
nsInd = fileBuff.find(b"xmlns")
cvInd = fileBuff.find(b">", nsInd)
fileBuff = fileBuff[:nsInd] + fileBuff[cvInd:]

root = ET.fromstring(fileBuff)

defList = []
incList = []
buildCmds = []
rebuildCmds = []
cleanCmds = []

cmakeFileStr = """cmake_minimum_required(VERSION 3.0.0)
project({project_name})

file(GLOB_RECURSE SRC_LIST "../../Source/*.cpp" "../../Source/*.c" "../../Source/*.cs" "../../Source/*.h")

add_definitions({definitions})
include_directories({includes})

{custom_targets}
"""

for pg in root.findall("PropertyGroup"):
	nmakeDefs = pg.find("NMakePreprocessorDefinitions")
	nmakeInc = pg.find("NMakeIncludeSearchPath")
	if nmakeDefs != None:
		defList = nmakeDefs.text.split(";")
		incList = nmakeInc.text.replace("\\", "/").split(";")
	
	output = pg.find("NMakeOutput")
	if output != None and output.text != None:
		buildCmd = pg.find("NMakeBuildCommandLine")
		if buildCmd != None: buildCmds.append(buildCmd.text)
		rebuildCmd = pg.find("NMakeReBuildCommandLine")
		if rebuildCmd != None: rebuildCmds.append(rebuildCmd.text)
		cleanCmd = pg.find("NMakeCleanCommandLine")
		if cleanCmd != None: cleanCmds.append(cleanCmd.text)

definitions = ""
for d in defList:
	definitions += "-D" + d + "\n"

includePaths = ""
for i in incList:
	if(len(i) > 0):
		includePaths += '"' + i + '"\n'
	

customTargetStr = "add_custom_target({name} COMMAND {command})\n"
customTargets = ""

def doCustomTarget(cmdList, typeStr):
	global customTargets
	for cmd in cmdList:
		cmd = cmd.replace("\\", "/")
		cmd = cmd.replace("$(SolutionDir)$(ProjectName)", projectDir + "/" + projectName)
		ns = cmd.find(projectName)
		ne = cmd.find('"', ns)
		name = '_'.join(cmd[ns:ne].split(' '))
		name += typeStr
		customTargets += customTargetStr.format(name=name, command=cmd)

doCustomTarget(buildCmds, "Build")
doCustomTarget(rebuildCmds, "Rebuild")
doCustomTarget(cleanCmds, "Clean")

cmakeFileStr = cmakeFileStr.format(
	project_name=projectName,
	definitions=definitions,
	includes=includePaths,
	custom_targets=customTargets)

cmakeFileStr += "add_executable(${PROJECT_NAME}Dummy ${SRC_LIST})"

print("Writing CMakeLists.txt...")

cmakeFile = open(projectDir + "/Intermediate/ProjectFiles/CMakeLists.txt", "w")
cmakeFile.write(cmakeFileStr)
cmakeFile.close()
	
print("Done.")

