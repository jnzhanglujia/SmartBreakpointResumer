Set ws = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")

baseDir = fs.GetParentFolderName(WScript.ScriptFullName)
ws.CurrentDirectory = baseDir

pythonwPath = fs.BuildPath(baseDir, ".venv\Scripts\pythonw.exe")
If Not fs.FileExists(pythonwPath) Then
    pythonwPath = fs.BuildPath(baseDir, "venv\Scripts\pythonw.exe")
End If
If Not fs.FileExists(pythonwPath) Then
    pythonwPath = fs.BuildPath(baseDir, ".venv\Scripts\python.exe")
End If
If Not fs.FileExists(pythonwPath) Then
    pythonwPath = "pythonw"
End If

scriptPath = fs.BuildPath(baseDir, "breakpoint_resumer.py")
cmd = """" & pythonwPath & """ """ & scriptPath & """ --listen"
ws.Run cmd, 0, False
