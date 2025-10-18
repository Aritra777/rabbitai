"""Safety patterns and command lists for RabbitAI command execution"""

# Dangerous command patterns that should always be blocked
# These patterns will prevent execution even if user tries to confirm
DANGEROUS_PATTERNS = [
    # File deletion - destructive operations
    r'rm\s+-rf',
    r'sudo\s+rm',
    r'del\s+/[sf]',

    # Disk operations - can destroy data
    r'format',
    r'mkfs',
    r'fdisk',
    r'parted.*rm',
    r'dd\s+if=',
    r'>\s*/dev/',

    # System control - can crash or shutdown system
    r'shutdown',
    r'reboot',
    r'halt',
    r'poweroff',
    r'init\s+0',
    r'init\s+6',
    r'telinit\s+[06]',

    # Permission changes - security risks
    r'chmod\s+777',
    r'chmod\s+-R\s+777',
    r'chown\s+-R\s+root',

    # Process killing - can kill critical processes
    r'killall',
    r'pkill.*-9',
    r'kill\s+-9\s+1',  # killing init

    # Package management - can break system
    r'apt-get\s+remove.*--purge',
    r'yum\s+remove',
    r'dnf\s+remove',
    r'pacman\s+-R',
    r'brew\s+uninstall',

    # Network attacks
    r':()\s*{\s*:\|:\s*&\s*};:',  # fork bomb
    r'while\s+true.*do',  # infinite loops that could DoS

    # Privilege escalation
    r'sudo\s+su',
    r'sudo\s+-i',
    r'sudo\s+bash',
    r'sudo\s+sh',

    # File overwrites
    r'>\s*/etc/',
    r'>.*passwd',
    r'>.*shadow',
    r'>.*sudoers',
]

# Safe read-only commands that don't require user confirmation
# These are diagnostic/informational commands that cannot harm the system
SAFE_COMMANDS = [
    # File operations (read-only)
    'ls', 'cat', 'head', 'tail', 'less', 'more', 'file',
    'grep', 'egrep', 'fgrep', 'find', 'locate', 'which', 'whereis',
    'wc', 'sort', 'uniq', 'diff', 'cmp', 'comm',
    'stat', 'du', 'tree', 'realpath', 'readlink',

    # System information
    'uname', 'hostname', 'uptime', 'date', 'cal', 'whoami', 'id',
    'pwd', 'env', 'printenv', 'echo',

    # Process monitoring
    'ps', 'top', 'htop', 'pstree', 'pgrep', 'pidof',

    # Disk usage
    'df', 'free', 'lsblk', 'blkid', 'fdisk -l',

    # Network diagnostics
    'ping', 'ping6', 'traceroute', 'traceroute6', 'tracert',
    'nslookup', 'dig', 'host', 'whois',
    'netstat', 'ss', 'lsof', 'route', 'ip', 'ip addr', 'ip route',
    'ifconfig', 'ipconfig', 'arp',
    'curl', 'wget', 'nc -zv', 'nmap -sn',

    # Service status (read-only)
    'systemctl status', 'systemctl list-units', 'systemctl is-active',
    'service --status-all', 'service status',
    'launchctl list', 'launchctl print',
    'sc query', 'sc queryex',
    'tasklist', 'qprocess',

    # Docker/Container diagnostics
    'docker ps', 'docker images', 'docker stats', 'docker inspect',
    'docker logs', 'docker version', 'docker info',
    'kubectl get', 'kubectl describe', 'kubectl logs',
    'podman ps', 'podman images', 'podman stats',

    # Version control (read-only)
    'git status', 'git log', 'git diff', 'git show', 'git branch',
    'git remote', 'git config --list', 'git rev-parse',

    # Package information (read-only)
    'apt list', 'apt-cache search', 'apt-cache show', 'apt-cache policy',
    'yum list', 'yum info', 'dnf list', 'dnf info',
    'pacman -Q', 'pacman -Ss', 'pacman -Si',
    'brew list', 'brew info', 'brew search',
    'pip list', 'pip show', 'pip freeze',
    'npm list', 'npm info', 'npm view',

    # Hardware information
    'lscpu', 'lspci', 'lsusb', 'lshw', 'dmidecode',
    'sensors', 'hwinfo', 'inxi',

    # Logs (read-only)
    'journalctl', 'dmesg', 'last', 'lastlog', 'w', 'who',

    # Security/Authentication (read-only)
    'ssh -V', 'openssl version', 'gpg --version',

    # Database (read-only queries)
    'mysql --version', 'psql --version', 'redis-cli --version',

    # Programming languages/tools
    'python --version', 'python3 --version', 'node --version',
    'java -version', 'go version', 'ruby --version', 'php --version',

    # Compression/archives (list only)
    'tar -tf', 'tar -tzf', 'unzip -l', 'zip -sf', '7z l',

    # Text processing
    'awk', 'sed -n', 'cut', 'tr', 'column', 'paste', 'join', 'fmt',

    # System monitoring
    'vmstat', 'iostat', 'mpstat', 'sar', 'nmon',
    'iotop', 'iftop', 'nethogs',

    # Cloud CLI tools (read-only)
    'aws --version', 'gcloud --version', 'az --version',
    'aws s3 ls', 'gcloud compute instances list', 'az vm list',

    # Kubernetes
    'kubectl version', 'kubectl cluster-info', 'kubectl get nodes',

    # File checksums
    'md5sum', 'sha1sum', 'sha256sum', 'sha512sum', 'cksum',
]

# Write operation indicators that suggest a command modifies system state
# Commands containing these will require user confirmation
WRITE_INDICATORS = [
    # Redirection
    '>', '>>', '|',

    # File operations
    'rm', 'del', 'mv', 'cp', 'mkdir', 'rmdir', 'touch',
    'ln', 'link', 'unlink',

    # Permission/ownership
    'chmod', 'chown', 'chgrp', 'chattr', 'setfacl',

    # Process control
    'kill', 'killall', 'pkill', 'sudo',

    # Text indicators
    'write', 'append', 'create', 'update', 'delete',
    'install', 'remove', 'uninstall', 'purge',
    'add', 'modify', 'set', 'enable', 'disable',
    'start', 'stop', 'restart', 'reload',

    # Package management
    'apt-get install', 'apt install', 'yum install', 'dnf install',
    'pacman -S', 'brew install', 'pip install', 'npm install',

    # Service control
    'systemctl start', 'systemctl stop', 'systemctl restart',
    'service start', 'service stop', 'service restart',

    # Network configuration
    'ifconfig', 'ip addr add', 'ip route add',
    'iptables', 'firewall-cmd',

    # File editing
    'vi', 'vim', 'nano', 'emacs', 'ed', 'sed -i',

    # Download/upload
    'wget -O', 'curl -o', 'scp', 'rsync', 'ftp',

    # Database operations
    'drop', 'truncate', 'insert', 'update', 'delete',
    'alter', 'create table', 'create database',

    # Docker/Container operations
    'docker run', 'docker start', 'docker stop', 'docker rm',
    'docker exec', 'kubectl apply', 'kubectl delete', 'kubectl create',

    # Git operations
    'git commit', 'git push', 'git pull', 'git clone',
    'git merge', 'git rebase', 'git reset', 'git checkout',

    # Compression operations
    'tar -c', 'tar -x', 'zip', 'unzip -o', 'gzip', 'gunzip',
]
