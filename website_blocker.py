"""
Website Blocker
A simple Windows desktop app to block/unblock websites by editing the
system hosts file (C:\\Windows\\System32\\drivers\\etc\\hosts).

Blocked domains are redirected to 127.0.0.1, which makes the browser
fail to reach the real site.

Requires administrator privileges to write to the hosts file — the app
will automatically request elevation on Windows if it isn't already
running as admin.
"""

import ctypes
import os
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
MARKER_START = "# === WebsiteBlocker START ==="
MARKER_END = "# === WebsiteBlocker END ==="


# ---------------------------------------------------------------------------
# Admin elevation (Windows only)
# ---------------------------------------------------------------------------

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relaunch_as_admin():
    """Re-launch this script with admin rights and exit the current process."""
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{os.path.abspath(sys.argv[0])}" {params}', None, 1
    )
    sys.exit(0)


# ---------------------------------------------------------------------------
# Hosts file logic
# ---------------------------------------------------------------------------

def read_hosts_lines() -> list[str]:
    with open(HOSTS_PATH, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def write_hosts_lines(lines: list[str]) -> None:
    with open(HOSTS_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_blocked_domains() -> list[str]:
    """Read the current list of domains inside our managed block.

    Each domain is listed once even though we write both the apex
    (e.g. reddit.com) and www. variant (e.g. www.reddit.com) as separate
    hosts entries under the hood — the www. line is collapsed into its
    apex domain here so the UI shows a single entry per site.
    """
    lines = read_hosts_lines()
    domains = []
    seen = set()
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == MARKER_START:
            inside = True
            continue
        if stripped == MARKER_END:
            inside = False
            continue
        if inside and stripped and not stripped.startswith("#"):
            parts = stripped.split()
            if len(parts) >= 2:
                domain = parts[1]
                canonical = domain[4:] if domain.startswith("www.") else domain
                if canonical not in seen:
                    seen.add(canonical)
                    domains.append(canonical)
    return domains


def save_blocked_domains(domains: list[str]) -> None:
    """Rewrite the hosts file, replacing our managed block with the given domains."""
    lines = read_hosts_lines()

    # Strip out any existing managed block
    new_lines = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == MARKER_START:
            inside = True
            continue
        if stripped == MARKER_END:
            inside = False
            continue
        if not inside:
            new_lines.append(line)

    # Ensure file ends with a newline before appending our block
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"

    if domains:
        new_lines.append(MARKER_START + "\n")
        for domain in sorted(set(domains)):
            new_lines.append(f"{REDIRECT_IP} {domain}\n")
            # also block the www. variant automatically
            if not domain.startswith("www."):
                new_lines.append(f"{REDIRECT_IP} www.{domain}\n")
        new_lines.append(MARKER_END + "\n")

    write_hosts_lines(new_lines)
    flush_dns()


def flush_dns():
    """Flush the DNS cache so blocks/unblocks take effect immediately."""
    os.system("ipconfig /flushdns >nul 2>&1")


def normalize_domain(raw: str) -> str:
    """Turn user input like 'https://www.example.com/path' into 'example.com'."""
    domain = raw.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.split("/")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class WebsiteBlockerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Website Blocker")
        self.geometry("420x480")
        self.resizable(False, False)

        self._build_widgets()
        self._refresh_list()

    def _build_widgets(self):
        header = tk.Label(self, text="Website Blocker", font=("Segoe UI", 16, "bold"))
        header.pack(pady=(15, 5))

        subtext = tk.Label(
            self,
            text="Add a domain (e.g. facebook.com) to block it.",
            font=("Segoe UI", 9),
            fg="gray",
        )
        subtext.pack(pady=(0, 10))

        entry_frame = tk.Frame(self)
        entry_frame.pack(pady=5, padx=15, fill="x")

        self.entry = tk.Entry(entry_frame, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", lambda e: self._add_site())

        add_btn = tk.Button(entry_frame, text="Add", command=self._add_site, width=8)
        add_btn.pack(side="left", padx=(8, 0))

        list_frame = tk.Frame(self)
        list_frame.pack(pady=10, padx=15, fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 11),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=(0, 15))

        remove_btn = tk.Button(
            button_frame, text="Remove Selected", command=self._remove_site, width=18
        )
        remove_btn.grid(row=0, column=0, padx=5)

        refresh_btn = tk.Button(
            button_frame, text="Refresh", command=self._refresh_list, width=10
        )
        refresh_btn.grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(self, text="", font=("Segoe UI", 9), fg="green")
        self.status_label.pack(pady=(0, 10))

    def _set_status(self, message: str, ok: bool = True):
        self.status_label.config(text=message, fg="green" if ok else "red")

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        try:
            for domain in sorted(get_blocked_domains()):
                self.listbox.insert(tk.END, domain)
            self._set_status(f"{self.listbox.size()} site(s) blocked.")
        except PermissionError:
            self._set_status("Permission denied reading hosts file.", ok=False)
        except Exception as e:
            self._set_status(f"Error: {e}", ok=False)

    def _add_site(self):
        raw = self.entry.get()
        if not raw.strip():
            return
        domain = normalize_domain(raw)
        if not domain or "." not in domain:
            messagebox.showwarning("Invalid domain", "Please enter a valid domain, e.g. facebook.com")
            return

        try:
            domains = get_blocked_domains()
            if domain in domains:
                self._set_status(f"{domain} is already blocked.")
            else:
                domains.append(domain)
                save_blocked_domains(domains)
                self._set_status(f"Blocked {domain}")
            self.entry.delete(0, tk.END)
            self._refresh_list()
        except PermissionError:
            messagebox.showerror("Permission denied", "Could not write to the hosts file. Try running as administrator.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _remove_site(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        domain = self.listbox.get(selection[0])
        try:
            domains = get_blocked_domains()
            if domain in domains:
                domains.remove(domain)
                save_blocked_domains(domains)
                self._set_status(f"Unblocked {domain}")
            self._refresh_list()
        except PermissionError:
            messagebox.showerror("Permission denied", "Could not write to the hosts file. Try running as administrator.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if sys.platform != "win32":
        print("This app currently only supports Windows (edits the Windows hosts file).")
        sys.exit(1)

    if not is_admin():
        relaunch_as_admin()
        return  # relaunch_as_admin() exits the process

    app = WebsiteBlockerApp()
    app.mainloop()


if __name__ == "__main__":
    main()