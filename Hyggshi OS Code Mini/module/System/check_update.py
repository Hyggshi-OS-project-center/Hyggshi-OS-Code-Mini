import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from module.System.Notification import show_notification, show_update_confirm

import os
import requests
import subprocess
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QTimer

GITHUB_API_URL = "https://api.github.com/repos/Hyggshi-OS-project-center/Hyggshi-OS-Code-Mini/releases/latest"
GITHUB_CONTENTS_API_URL = "https://api.github.com/repos/Hyggshi-OS-project-center/Hyggshi-OS-Code-Mini/contents"
LOCAL_VERSION = "2025.09.17"  # Đặt phiên bản hiện tại của bạn ở đây

def download_file_from_github(file_info, save_dir="."):
    """Tải file từ GitHub về local."""
    download_url = file_info.get("download_url")
    name = file_info.get("name")
    if not download_url or not name:
        return False
    save_path = os.path.join(save_dir, name)
    try:
        print(f"Đang tải: {save_path} ...")
        r = requests.get(download_url)
        r.raise_for_status()
        os.makedirs(save_dir, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(r.content)
        print(f"✅ Đã cập nhật: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi tải {save_path}: {e}")
        return False

def update_from_github(local_dir=".", github_contents_url=None):
    """Đệ quy kiểm tra và cập nhật các file mới nhất từ GitHub repo."""
    if github_contents_url is None:
        github_contents_url = GITHUB_CONTENTS_API_URL
        if local_dir != ".":
            # Nếu đây là subdirectory, thêm path vào URL
            github_contents_url += f"/{local_dir.replace(os.sep, '/')}"
    
    print(f"\n🔄 Đang kiểm tra cập nhật tại: {github_contents_url}")
    try:
        r = requests.get(github_contents_url, timeout=10)
        r.raise_for_status()
        files = r.json()
        
        # Đảm bảo files là một list
        if not isinstance(files, list):
            print(f"❌ Phản hồi API không đúng định dạng: {type(files)}")
            return
            
        for file_info in files:
            if file_info["type"] == "file":
                local_path = os.path.join(local_dir, file_info["name"])
                need_update = True
                
                if os.path.exists(local_path):
                    # Có thể so sánh SHA ở đây nếu muốn tối ưu
                    # local_sha = get_file_sha(local_path)
                    # if local_sha == file_info.get("sha"):
                    #     need_update = False
                    pass
                    
                if need_update:
                    download_file_from_github(file_info, local_dir)
                    
            elif file_info["type"] == "dir":
                subdir = os.path.join(local_dir, file_info["name"])
                sub_api_url = file_info["url"]
                update_from_github(subdir, sub_api_url)
                
        print(f"✅ Đã kiểm tra và cập nhật xong: {local_dir}\n")
    except Exception as e:
        print(f"❌ Lỗi cập nhật tại {github_contents_url}: {e}")

def get_latest_version():
    """Lấy phiên bản mới nhất từ GitHub releases."""
    try:
        r = requests.get(GITHUB_API_URL, timeout=5)
        r.raise_for_status()
        data = r.json()  # Đây là dict của release
        return data.get("tag_name") or data.get("name")
    except Exception as e:
        print("Lỗi lấy phiên bản mới nhất:", e)
        return None

def download_release_assets():
    """Tải các assets từ release mới nhất."""
    try:
        r = requests.get(GITHUB_API_URL, timeout=10)
        r.raise_for_status()
        release_data = r.json()
        
        assets = release_data.get("assets", [])
        if not assets:
            print("Không có assets nào trong release này")
            return False
            
        success = True
        for asset in assets:
            asset_name = asset.get("name")
            download_url = asset.get("browser_download_url")
            
            if asset_name and download_url:
                print(f"Đang tải asset: {asset_name}...")
                try:
                    asset_response = requests.get(download_url)
                    asset_response.raise_for_status()
                    
                    with open(asset_name, "wb") as f:
                        f.write(asset_response.content)
                    print(f"✅ Đã tải xong: {asset_name}")
                except Exception as e:
                    print(f"❌ Lỗi khi tải {asset_name}: {e}")
                    success = False
            else:
                print(f"❌ Thiếu thông tin cho asset: {asset}")
                success = False
                
        return success
    except Exception as e:
        print(f"❌ Lỗi khi tải release assets: {e}")
        return False

def show_update_confirm(title, message):
    """
    Hiển thị thông báo xác nhận cập nhật (QMessageBox).
    Trả về True nếu người dùng chọn Đồng ý, False nếu chọn Không.
    """
    app = QApplication.instance()
    close_app = False
    if app is None:
        app = QApplication(sys.argv)
        close_app = True
    msg = QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setIcon(QMessageBox.Question)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.button(QMessageBox.Yes).setText("Đồng ý")
    msg.button(QMessageBox.No).setText("Không đồng ý")
    result = msg.exec_()
    if close_app:
        app.quit()
    return result == QMessageBox.Yes

def check_and_update():
    """Kiểm tra và thông báo nếu có bản cập nhật mới."""
    latest = get_latest_version()
    if latest and latest != LOCAL_VERSION:
        def notify():
            if show_update_confirm("Có bản cập nhật mới!", 
                                   f"Đã phát hiện bản cập nhật mới ({latest}). Bạn có muốn cập nhật không?"):
                # Gọi update.py để cập nhật
                subprocess.Popen([sys.executable, "module/System/update.py"])
        # Đảm bảo chạy notify trên main thread
        QTimer.singleShot(0, notify)
    else:
        print("Đã là phiên bản mới nhất.")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    check_and_update()
    sys.exit(app.exec_())

    print("=== BẮT ĐẦU KIỂM TRA VÀ CẬP NHẬT TỪ GITHUB ===")
    
    # Lựa chọn 1: Cập nhật từ source code (contents API)
    print("\n1️⃣ Cập nhật từ source code...")
    update_from_github(".")
    
    # Lựa chọn 2: Tải assets từ release (nếu có)
    print("\n2️⃣ Kiểm tra và tải release assets...")
    download_release_assets()
    
    # Sau khi cập nhật xong:
    show_update_confirm("Cập nhật", "Đã kiểm tra và cập nhật xong từ Github!")
    print("=== ĐÃ HOÀN THÀNH CẬP NHẬT ===")