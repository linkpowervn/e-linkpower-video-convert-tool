# Link Power E Learning video convert tool

## Yêu cầu

- Hệ điều hành windows
- Python 3
- PySide6
- `ffmpeg` được cài đặt trên máy tính với thiết lập mặc định và đã thêm file binary vào `PATH`
  (https://github.com/BtbN/FFmpeg-Builds/releases)
- `openssl` được cài đặt trên máy tính với thiết lập mặc định và đã thêm file binary vào `PATH` (https://slproweb.com/products/Win32OpenSSL.html)

## Đóng gói

Sử dụng `pyinstaller`:

```
pyinstaller --onefile --windowed main.py
```
