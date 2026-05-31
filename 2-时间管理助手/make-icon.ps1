Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap(192,192)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$bg = [System.Drawing.Color]::FromArgb(37,99,235)
$g.Clear($bg)
$brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
$font = New-Object System.Drawing.Font('Segoe UI', 52, [System.Drawing.FontStyle]::Bold)
$sf = New-Object System.Drawing.StringFormat
$sf.Alignment = [System.Drawing.StringAlignment]::Center
$sf.LineAlignment = [System.Drawing.StringAlignment]::Center
$rect = New-Object System.Drawing.RectangleF(0,0,192,192)
$g.DrawString('TM', $font, $brush, $rect, $sf)
$g.Dispose()
$tmpPath = 'C:\Windows\Temp\icon-192.png'
$bmp.Save($tmpPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
$dest = [System.IO.Path]::Combine('D:\AI-项目\2-时间管理助手\src', 'icon-192.png')
[System.IO.File]::Copy($tmpPath, $dest, $true)
Write-Host 'icon-192.png created successfully'
