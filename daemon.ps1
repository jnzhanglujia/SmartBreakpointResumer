$baseDir = Split-Path $MyInvocation.MyCommand.Path
$pythonw = Join-Path $baseDir ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $pythonw)) {
    $pythonw = Join-Path $baseDir "venv\Scripts\pythonw.exe"
}
if (-not (Test-Path $pythonw)) {
    $pythonw = "pythonw"
}
$script = Join-Path $baseDir "breakpoint_resumer.py"
$env:PYTHONIOENCODING = "utf-8"
Start-Process -FilePath $pythonw -ArgumentList "`"$script`" --listen" -WorkingDirectory $baseDir -WindowStyle Hidden
