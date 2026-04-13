Output demo/chartex-demo.gif
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

Type `cd ~/.claude/skills/cli-charts`
Enter
Sleep 800ms

Type `python -m cli_charts.chart bar --json '{"labels":["API","DB","Cache"],"values":[42,18,76]}' --title 'Latency ms'`
Sleep 500ms
Enter
Sleep 2500ms

Type `python -m cli_charts.chart sparkline --json '{"values":[10,22,18,35,29,40,55,48]}' --title 'RPS'`
Sleep 500ms
Enter
Sleep 2500ms

Type `python -m cli_charts.chart pie --json '{"labels":["Stocks","Bonds","Cash"],"values":[60,30,10]}' --title 'Portfolio'`
Sleep 500ms
Enter
Sleep 2500ms

Type `python -m cli_charts.dashboard --demo --no-interactive`
Sleep 500ms
Enter
Sleep 3500ms
