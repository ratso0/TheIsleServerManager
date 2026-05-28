import subprocess
import os
from core.os_utils import get_os, is_admin

# Default ports used by The Isle Evrima dedicated server
DEFAULT_PORTS = [
    {"port": 7777, "protocol": "UDP", "description": "Game Port"},
    {"port": 7778, "protocol": "UDP", "description": "Game Port (alt)"},
    {"port": 27015, "protocol": "UDP", "description": "Steam Query Port"},
    {"port": 27020, "protocol": "TCP", "description": "RCON Port"},
]


def open_port_windows(port: int, protocol: str, name: str) -> tuple[bool, str]:
    """Open a port using Windows Firewall (netsh)"""
    direction_in = [
        'netsh', 'advfirewall', 'firewall', 'add', 'rule',
        f'name=TheIsle_{name}_{port}_IN',
        'dir=in', 'action=allow',
        f'protocol={protocol}',
        f'localport={port}'
    ]
    direction_out = [
        'netsh', 'advfirewall', 'firewall', 'add', 'rule',
        f'name=TheIsle_{name}_{port}_OUT',
        'dir=out', 'action=allow',
        f'protocol={protocol}',
        f'localport={port}'
    ]
    try:
        r1 = subprocess.run(direction_in, capture_output=True, text=True)
        r2 = subprocess.run(direction_out, capture_output=True, text=True)
        if r1.returncode == 0 and r2.returncode == 0:
            return True, f"Port {port}/{protocol} opened successfully"
        else:
            err = r1.stderr or r2.stderr
            return False, f"Error: {err}"
    except Exception as e:
        return False, str(e)


def close_port_windows(port: int, protocol: str, name: str) -> tuple[bool, str]:
    """Remove a firewall rule on Windows"""
    for direction in ['IN', 'OUT']:
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'delete', 'rule',
            f'name=TheIsle_{name}_{port}_{direction}'
        ], capture_output=True)
    return True, f"Port {port}/{protocol} rule removed"


def open_port_linux_ufw(port: int, protocol: str) -> tuple[bool, str]:
    """Open a port using UFW"""
    try:
        r = subprocess.run(
            ['ufw', 'allow', f'{port}/{protocol.lower()}'],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            return True, f"Port {port}/{protocol} opened via UFW"
        return False, r.stderr
    except FileNotFoundError:
        return False, "UFW not found"


def open_port_linux_iptables(port: int, protocol: str) -> tuple[bool, str]:
    """Open a port using iptables"""
    try:
        r = subprocess.run([
            'iptables', '-A', 'INPUT', '-p', protocol.lower(),
            '--dport', str(port), '-j', 'ACCEPT'
        ], capture_output=True, text=True)
        if r.returncode == 0:
            return True, f"Port {port}/{protocol} opened via iptables"
        return False, r.stderr
    except FileNotFoundError:
        return False, "iptables not found"


def open_port_linux(port: int, protocol: str) -> tuple[bool, str]:
    """Try UFW first, fall back to iptables"""
    ok, msg = open_port_linux_ufw(port, protocol)
    if ok:
        return ok, msg
    return open_port_linux_iptables(port, protocol)


def open_all_ports(os_type: str = None, log_callback=None) -> list:
    """Open all default The Isle server ports"""
    if os_type is None:
        os_type = get_os()

    results = []
    for entry in DEFAULT_PORTS:
        port = entry['port']
        proto = entry['protocol']
        desc = entry['description']

        if log_callback:
            log_callback(f"Opening {port}/{proto} ({desc})...")

        if os_type == 'windows':
            ok, msg = open_port_windows(port, proto, desc.replace(' ', '_'))
        else:
            ok, msg = open_port_linux(port, proto)

        results.append({
            'port': port,
            'protocol': proto,
            'description': desc,
            'success': ok,
            'message': msg
        })

        if log_callback:
            status = "✓" if ok else "✗"
            log_callback(f"  {status} {msg}")

    return results


def check_port_open_windows(port: int) -> bool:
    """Check if a firewall rule exists for a port on Windows"""
    r = subprocess.run(
        ['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name=TheIsle_Game_Port_{port}_IN'],
        capture_output=True, text=True
    )
    return r.returncode == 0


def get_firewall_status(os_type: str = None) -> list:
    """Return list of port statuses"""
    if os_type is None:
        os_type = get_os()
    status = []
    for entry in DEFAULT_PORTS:
        status.append({
            **entry,
            'open': False  # Placeholder – extend per-OS check as needed
        })
    return status
