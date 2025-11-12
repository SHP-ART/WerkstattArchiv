Set WshShell = CreateObject("WScript.Shell")

' Wechsle zum Script-Verzeichnis
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Pruefe ob venv existiert
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FolderExists("venv") Then
    MsgBox "FEHLER: Virtuelle Umgebung nicht gefunden!" & vbCrLf & vbCrLf & "Bitte zuerst 'install.bat' ausfuehren!", vbCritical, "WerkstattArchiv"
    WScript.Quit 1
End If

' Starte Python-Anwendung komplett unsichtbar (kein Fenster)
WshShell.Run "venv\Scripts\pythonw.exe main.py", 0, False

Set WshShell = Nothing
Set fso = Nothing
