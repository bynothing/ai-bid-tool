# Draw.io local tool

Draw.io is downloaded from the official GitHub release repository:

https://github.com/jgraph/drawio-desktop

The binary is intentionally kept under `.tools/` and ignored by git. To install or refresh it:

```powershell
.\tools\install-drawio.ps1
```

Use the wrapper when a drawing step needs Draw.io:

```powershell
.\tools\drawio.ps1 --export --format png --output output\diagram.png input\diagram.drawio
.\tools\drawio.ps1 -x -f svg -o output\diagram.svg input\diagram.drawio
.\tools\drawio.ps1 input\diagram.drawio
```

The wrapper checks `DRAWIO_EXE` first, then the local `.tools\drawio-msi` install.
