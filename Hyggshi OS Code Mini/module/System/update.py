import os
import requests
from module.System.Notification import show_notification, show_update_confirm
import subprocess

GITHUB_API_URL = "https://api.github.com/repos/Hyggshi-OS-project-center/Hyggshi-OS-Code-Mini/contents/Hyggshi%20OS%20Code%20Mini"

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

def update_from_github(local_dir=".", github_api_url=GITHUB_API_URL):
    """Đệ quy kiểm tra và cập nhật các file mới nhất từ GitHub repo."""
    print(f"\n🔄 Đang kiểm tra cập nhật tại: {github_api_url}")
    try:
        r = requests.get(github_api_url)
        r.raise_for_status()
        files = r.json()
        for file_info in files:
            if file_info["type"] == "file":
                local_path = os.path.join(local_dir, file_info["name"])
                need_update = True
                if os.path.exists(local_path):
                    # Có thể so sánh SHA ở đây nếu muốn tối ưu
                    pass
                if need_update:
                    download_file_from_github(file_info, local_dir)
            elif file_info["type"] == "dir":
                subdir = os.path.join(local_dir, file_info["name"])
                sub_api_url = file_info["url"]
                update_from_github(subdir, sub_api_url)
        print(f"✅ Đã kiểm tra và cập nhật xong: {local_dir}\n")
    except Exception as e:
        print(f"❌ Lỗi cập nhật tại {github_api_url}: {e}")

if __name__ == "__main__":
    if show_update_confirm("Cập nhật", "Có bản cập nhật mới. Bạn có muốn cập nhật và cài đặt không?"):
        print("=== BẮT ĐẦU KIỂM TRA VÀ CẬP NHẬT TỪ GITHUB ===")
        update_from_github(".")
        show_notification("Cập nhật", "Đã kiểm tra và cập nhật xong từ Github!")
        print("=== ĐÃ HOÀN THÀNH CẬP NHẬT ===")
    else:
        print("Bạn đã từ chối cập nhật.")