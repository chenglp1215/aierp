#!/usr/bin/env python3
"""
CI/CD Deploy Script
自动打包并部署到远程服务器（使用 paramiko，单次密码输入）
"""

import os
import sys
import shutil
import tempfile
import tarfile
import io

try:
    import paramiko
except ImportError:
    print("请先安装 paramiko: pip install paramiko")
    sys.exit(1)

REMOTE_HOST = "132.232.212.151"
REMOTE_USER = "root"
REMOTE_PATH = "/root/aierp"

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'


def log_info(msg):
    print(f"{GREEN}[INFO]{NC} {msg}")


def log_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}", file=sys.stderr)


def get_password():
    try:
        import getpass
        return getpass.getpass(f"{YELLOW}请输入 SSH 密码: {NC}")
    except Exception:
        return input(f"{YELLOW}请输入 SSH 密码: {NC}")


def build_frontend(project_root):
    log_info("构建前端...")
    web_dir = os.path.join(project_root, "web")

    if not os.path.exists(os.path.join(web_dir, "node_modules")):
        log_info("安装前端依赖...")
        os.system(f"cd {web_dir} && npm install")

    log_info("执行 npm run build...")
    result = os.system(f"cd {web_dir} && npm run build")

    if result != 0:
        log_error("前端构建失败")
        sys.exit(1)

    dist_dir = os.path.join(web_dir, "dist")
    if not os.path.exists(dist_dir):
        log_error("前端构建失败")
        sys.exit(1)
    log_info("前端构建完成")


def prepare_files(project_root):
    log_info("准备打包文件...")

    temp_dir = tempfile.mkdtemp()
    backend_temp = os.path.join(temp_dir, "backend")
    backend_src = os.path.join(project_root, "backend")

    shutil.copytree(backend_src, backend_temp)

    for exclude in ["__pycache__", ".git", "venv", ".venv"]:
        for root, dirs, files in os.walk(backend_temp):
            if exclude in dirs:
                shutil.rmtree(os.path.join(root, exclude))

    for root, dirs, files in os.walk(backend_temp):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))

    settings_pro = os.path.join(backend_temp, "config", "settings-pro.py")
    settings_py = os.path.join(backend_temp, "config", "settings.py")
    if os.path.exists(settings_pro):
        shutil.copy(settings_pro, settings_py)
        log_info("已复制 settings-pro.py 为 settings.py")

    dist_dir = os.path.join(project_root, "web", "dist")

    backend_tar = os.path.join(temp_dir, "backend.tar")
    frontend_tar = os.path.join(temp_dir, "frontend.tar")

    log_info("打包后端...")
    with tarfile.open(backend_tar, "w") as tar:
        tar.add(backend_temp, arcname=".")

    log_info("打包前端...")
    with tarfile.open(frontend_tar, "w") as tar:
        tar.add(dist_dir, arcname=".")

    return temp_dir, backend_tar, frontend_tar


def transfer_and_deploy(password, temp_dir, backend_tar, frontend_tar):
    log_info("连接远程服务器...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_HOST, username=REMOTE_USER, password=password)

    sftp = ssh.open_sftp()

    log_info("创建远程目录...")
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_PATH}/backend {REMOTE_PATH}/dist")
    stdout.channel.recv_exit_status()

    log_info("上传后端...")
    sftp.put(backend_tar, f"/tmp/backend.tar")
    log_info("上传前端...")
    sftp.put(frontend_tar, f"/tmp/frontend.tar")

    sftp.close()

    log_info("解压并部署...")
    remote_script = f'''
        tar -xf /tmp/backend.tar -C {REMOTE_PATH}/backend
        tar -xf /tmp/frontend.tar -C {REMOTE_PATH}/dist
        rm -f /tmp/backend.tar /tmp/frontend.tar
        cd {REMOTE_PATH}/backend && /root/aierp/venv/bin/python scripts/init_db.py
        bash {REMOTE_PATH}/restart.sh
    '''
    stdin, stdout, stderr = ssh.exec_command(remote_script)

    stdout_lines = stdout.read().decode('utf-8', errors='ignore')
    stderr_lines = stderr.read().decode('utf-8', errors='ignore')
    exit_status = stdout.channel.recv_exit_status()

    if stdout_lines:
        for line in stdout_lines.strip().split('\n'):
            if line.strip():
                log_info(f"[远程] {line}")
    if stderr_lines:
        for line in stderr_lines.strip().split('\n'):
            if line.strip() and 'error' not in line.lower() and 'fail' not in line.lower():
                log_info(f"[远程] {line}")
            elif line.strip():
                log_error(f"[远程] {line}")

    if exit_status != 0:
        log_error(f"远程执行失败，退出码: {exit_status}")
        ssh.close()
        sys.exit(1)

    ssh.close()
    log_info("部署完成")


def main():
    log_info("开始部署...")

    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    log_info(f"项目目录: {project_root}")

    build_frontend(project_root)
    temp_dir, backend_tar, frontend_tar = prepare_files(project_root)

    try:
        password = get_password()
        transfer_and_deploy(password, temp_dir, backend_tar, frontend_tar)
    except Exception as e:
        log_error(f"部署失败: {e}")
        sys.exit(1)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    log_info("部署完成!")


if __name__ == "__main__":
    main()
