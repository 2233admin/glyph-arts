$ErrorActionPreference = 'Stop'
Set-Location "D:\projects\glyph-arts"
$before = (git show edd9b7b:cli_charts/cmd/_helpers.py | Measure-Object -Line).Lines
$after = (Get-Content cli_charts/cmd/_helpers.py | Measure-Object -Line).Lines
$delta = $before - $after
Write-Output ("before: {0} | after: {1} | delta: -{2}" -f $before, $after, $delta)
