Website Blocker

A simple Windows desktop app (Tkinter GUI) that blocks websites by
redirecting their domains to 127.0.0.1 in your system's hosts file.

How it works


Blocked domains are written into C:\Windows\System32\drivers\etc\hosts
inside a clearly marked section (# === WebsiteBlocker START/END ===),
so it won't touch anything else in that file.
Editing this file requires administrator rights, so the app
automatically prompts for elevation (UAC popup) when you launch it.
After every change, the app flushes your DNS cache so the block/unblock
takes effect immediately without needing a restart.
Adding a domain also automatically blocks its www. variant.


Requirements


Windows 10/11
Python 3.10+ (Tkinter ships with standard Python on Windows, no extra
install needed)


Running it


Open VS Code in this folder (or just a terminal).
Run:


   python website_blocker.py


Accept the UAC "Run as administrator" prompt — this is required to
edit the hosts file.
Type a domain (e.g. facebook.com or https://www.reddit.com) and
click Add, or press Enter.
Select a site in the list and click Remove Selected to unblock it.


Notes & limitations


This only blocks access via domain name (works for regular browsing).
It won't stop apps that hardcode IP addresses or use their own DNS
(e.g. some browsers with DNS-over-HTTPS enabled may bypass it — you may
need to disable "Secure DNS" in Chrome/Edge settings for this to work
reliably).
Because it edits a system file, some antivirus software may flag it —
that's expected behavior for any hosts-file editor, not a sign of a
problem.
