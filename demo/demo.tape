Output demo/chartex-demo.gif
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

Type `cli-charts bar --json '{"labels":["API","DB","Cache"],"values":[42,18,76]}' --title 'Latency ms'`
Sleep 500ms
Enter
Sleep 2s

Type `cli-charts sparkline --json '{"values":[10,22,18,35,29,40,55,48]}' --title 'RPS'`
Sleep 500ms
Enter
Sleep 2s

Type "python -m cli_charts.dashboard --demo --no-interactive"
Sleep 500ms
Enter
Sleep 3s
