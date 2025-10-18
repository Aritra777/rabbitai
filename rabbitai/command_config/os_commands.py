"""OS-specific command lists for RabbitAI system context"""

# Commands available on most Unix-like and Windows systems
COMMON_COMMANDS = [
    'echo', 'cat', 'ls', 'pwd', 'whoami', 'date',
    'hostname', 'ping',
]

# Linux-specific diagnostic commands
LINUX_COMMANDS = [
    # Process management
    'ps', 'top', 'htop', 'pstree', 'pgrep', 'pidof',

    # System information
    'uname', 'uptime', 'lsb_release', 'hostnamectl',
    'lscpu', 'lspci', 'lsusb', 'lshw', 'dmidecode',
    'hwinfo', 'inxi', 'neofetch',

    # Memory and disk
    'free', 'vmstat', 'df', 'du', 'lsblk', 'blkid',
    'fdisk -l', 'parted -l', 'mount',

    # Network diagnostics
    'ip', 'ss', 'netstat', 'route', 'arp', 'iptables -L',
    'nmap', 'tcpdump', 'traceroute', 'mtr', 'dig', 'nslookup',
    'host', 'whois', 'curl', 'wget', 'nc', 'ncat',
    'ethtool', 'iwconfig', 'nmcli', 'iftop', 'nethogs',

    # File operations
    'find', 'grep', 'egrep', 'fgrep', 'locate', 'which', 'whereis',
    'file', 'stat', 'wc', 'head', 'tail', 'less', 'more',
    'tree', 'realpath', 'readlink', 'basename', 'dirname',

    # System services
    'systemctl', 'systemctl status', 'systemctl list-units',
    'systemctl is-active', 'systemctl is-enabled',
    'journalctl', 'service',

    # Logs and monitoring
    'dmesg', 'last', 'lastlog', 'w', 'who', 'uptime',
    'iostat', 'mpstat', 'sar', 'iotop',

    # File systems
    'lsof', 'fuser', 'findmnt', 'mountpoint',

    # Security and users
    'id', 'groups', 'getent', 'sudo -l', 'sestatus',
    'aa-status', 'loginctl',

    # Package management (Debian/Ubuntu)
    'apt', 'apt-get', 'apt-cache', 'dpkg', 'dpkg-query',

    # Package management (RedHat/CentOS/Fedora)
    'yum', 'dnf', 'rpm', 'rpm -qa',

    # Package management (Arch)
    'pacman', 'pacman -Q',

    # Performance monitoring
    'perf', 'strace', 'ltrace', 'sysctl',

    # Hardware sensors
    'sensors', 'acpi',

    # Compression/archives
    'tar', 'gzip', 'gunzip', 'bzip2', 'bunzip2', 'xz', 'unxz',
    'zip', 'unzip', '7z',

    # Text processing
    'awk', 'sed', 'cut', 'tr', 'sort', 'uniq', 'diff', 'comm',
    'column', 'paste', 'join', 'fmt', 'nl', 'tac', 'rev',

    # Checksums
    'md5sum', 'sha1sum', 'sha256sum', 'sha512sum', 'cksum',

    # Development tools
    'git', 'make', 'gcc', 'g++', 'gdb', 'objdump', 'nm', 'ldd',
    'strace', 'ltrace',

    # Containers and virtualization
    'docker', 'podman', 'lxc', 'virsh', 'virt-top',
    'kubectl', 'crictl',

    # Databases
    'mysql', 'psql', 'redis-cli', 'mongo', 'sqlite3',

    # Web servers
    'nginx', 'apache2', 'httpd',
]

# macOS-specific diagnostic commands
MACOS_COMMANDS = [
    # Process management
    'ps', 'top', 'pstree', 'pgrep',

    # System information
    'uname', 'uptime', 'hostname', 'sw_vers', 'system_profiler',
    'sysctl', 'ioreg', 'kextstat', 'diskutil',

    # Memory and disk
    'df', 'du', 'mount', 'diskutil list', 'diskutil info',
    'vm_stat', 'purge',

    # Network diagnostics
    'ifconfig', 'netstat', 'route', 'arp', 'ping', 'traceroute',
    'dig', 'nslookup', 'host', 'whois', 'curl', 'nc',
    'networksetup', 'scutil', 'ndp', 'airport',

    # File operations
    'find', 'grep', 'egrep', 'fgrep', 'locate', 'which', 'whereis',
    'file', 'stat', 'wc', 'head', 'tail', 'less', 'more',
    'readlink', 'basename', 'dirname', 'mdls', 'mdfind',

    # System services
    'launchctl', 'launchctl list', 'launchctl print',

    # Logs and monitoring
    'log', 'log show', 'log stream', 'last', 'w', 'who',
    'fs_usage', 'sc_usage', 'latency', 'powermetrics',

    # File systems
    'lsof', 'fuser',

    # Security and users
    'id', 'groups', 'dscl', 'security', 'csrutil status',

    # Package management
    'brew', 'brew list', 'brew info', 'brew search',
    'port', 'pkgutil',

    # Performance monitoring
    'dtrace', 'instruments', 'fs_usage', 'vm_stat',

    # Hardware information
    'ioreg', 'pmset', 'system_profiler', 'sysctl -a',

    # Compression/archives
    'tar', 'gzip', 'gunzip', 'bzip2', 'bunzip2', 'xz', 'unxz',
    'zip', 'unzip', 'ditto',

    # Text processing
    'awk', 'sed', 'cut', 'tr', 'sort', 'uniq', 'diff', 'comm',
    'column', 'paste', 'join', 'fmt',

    # Checksums
    'md5', 'shasum', 'md5sum', 'sha1sum', 'sha256sum',

    # Development tools
    'git', 'make', 'gcc', 'clang', 'xcodebuild', 'swift',
    'otool', 'nm', 'lipo', 'codesign',

    # Containers
    'docker', 'kubectl', 'podman',

    # Databases
    'mysql', 'psql', 'redis-cli', 'mongo', 'sqlite3',

    # macOS-specific
    'osascript', 'defaults', 'plutil', 'tmutil', 'caffeinate',
    'softwareupdate', 'xattr', 'codesign', 'spctl',
]

# Windows-specific diagnostic commands
WINDOWS_COMMANDS = [
    # System information
    'systeminfo', 'hostname', 'ver', 'winver', 'msinfo32',
    'wmic', 'wmic os', 'wmic cpu', 'wmic memorychip',

    # Process management
    'tasklist', 'tasklist /v', 'qprocess', 'wmic process',

    # Network diagnostics
    'ipconfig', 'ipconfig /all', 'ping', 'tracert', 'pathping',
    'netstat', 'netstat -ano', 'nslookup', 'route print',
    'arp', 'arp -a', 'nbtstat', 'netsh', 'getmac',

    # Disk operations
    'dir', 'tree', 'diskpart', 'chkdsk', 'fsutil',
    'wmic logicaldisk', 'vol',

    # File operations
    'type', 'more', 'find', 'findstr', 'where', 'fc', 'comp',
    'attrib', 'icacls', 'cacls',

    # System services
    'sc query', 'sc queryex', 'net start', 'tasklist /svc',
    'wmic service',

    # Logs and events
    'eventvwr', 'wevtutil', 'query', 'get-eventlog',

    # User and security
    'whoami', 'whoami /all', 'net user', 'net localgroup',
    'gpresult', 'secedit', 'cipher',

    # Performance monitoring
    'perfmon', 'typeperf', 'logman', 'wmic cpu get loadpercentage',

    # Drivers and devices
    'driverquery', 'pnputil', 'devcon',

    # Registry (read-only)
    'reg query',

    # Package management
    'wmic product', 'winget list', 'choco list',

    # Environment
    'set', 'echo', 'path',

    # Compression
    'tar', 'expand', 'compact',

    # Checksums
    'certutil -hashfile',

    # PowerShell commands
    'powershell', 'pwsh', 'Get-Process', 'Get-Service',
    'Get-ComputerInfo', 'Get-NetAdapter', 'Get-NetIPAddress',
    'Get-NetRoute', 'Test-Connection', 'Test-NetConnection',
    'Get-EventLog', 'Get-WinEvent', 'Get-Volume', 'Get-Disk',
    'Get-PhysicalDisk', 'Get-PSDrive', 'Get-Item', 'Get-ChildItem',
    'Get-Content', 'Select-String', 'Measure-Object',

    # Containers (Windows)
    'docker', 'kubectl',

    # Databases
    'mysql', 'psql', 'sqlcmd', 'redis-cli', 'mongo', 'sqlite3',
]
