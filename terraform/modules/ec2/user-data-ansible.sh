#!/bin/bash
# Minimal user-data for Ansible-managed EC2 instances
# This script only prepares the instance for Ansible configuration

set -euo pipefail

# Logging functions
log_info() { echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2; }

log_info "Starting minimal EC2 setup for Ansible management..."

# Update system
log_info "Updating system packages..."
yum update -y

# Install Python 3 and pip (required for Ansible)
log_info "Installing Python 3..."
yum install -y python3 python3-pip

# Install httpd-tools for htpasswd
log_info "Installing httpd-tools..."
yum install -y httpd-tools

# Create ansible user
log_info "Creating ansible user..."
useradd -m -s /bin/bash ansible

# Set up SSH for ansible user
log_info "Configuring SSH for ansible user..."
mkdir -p /home/ansible/.ssh
cat > /home/ansible/.ssh/authorized_keys << 'EOF'
${ansible_ssh_key}
EOF
chown -R ansible:ansible /home/ansible/.ssh
chmod 700 /home/ansible/.ssh
chmod 600 /home/ansible/.ssh/authorized_keys

# Allow ansible user to sudo without password
log_info "Configuring sudo for ansible user..."
echo "ansible ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ansible
chmod 0440 /etc/sudoers.d/ansible

# Install AWS CLI for Secrets Manager access
log_info "Installing AWS CLI..."
pip3 install --upgrade awscli

# Create application directory with proper permissions
log_info "Creating application directory..."
mkdir -p /opt/blindstrader
chown ansible:ansible /opt/blindstrader

# Signal completion
log_info "Minimal setup complete! Instance ready for Ansible configuration."
log_info "Next step: Run ansible-playbook -i inventory/${environment}.yml playbooks/site.yml"

# Create marker file to indicate setup completion
touch /var/log/user-data-complete
