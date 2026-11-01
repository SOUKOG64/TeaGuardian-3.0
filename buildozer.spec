[app]
title = TeaGuardian
package.name = teaguardian
package.domain = org.teaguardian
source.dir = .
source.include_exts = py,kv
source.exclude_dirs = bin,.buildozer,.github,server,tests,__pycache__
version = 0.2
requirements = python3,kivy==2.3.0,certifi
orientation = portrait
fullscreen = 0
android.permissions = VIBRATE,INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
