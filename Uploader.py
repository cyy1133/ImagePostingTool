# 스크립트 최상단에 위치 - 표준 라이브러리 및 필수 패키지 정의
import subprocess
import sys
import os
import json
import importlib
import importlib.util
from pathlib import Path
import tkinter as tk # ensure_packages_installed 에서 messagebox를 사용하기 위해 필요
from tkinter import messagebox # ensure_packages_installed 에서 사용

# --- 자동 모듈 설치 로직을 위한 패키지 목록 ---
REQUIRED_PACKAGES_CORE = [
    ("customtkinter", "customtkinter"),
    ("tweepy", "tweepy"),
    ("pytumblr", "pytumblr"),
    ("APScheduler", "apscheduler"),
    ("requests", "requests"),
    ("BeautifulSoup4", "bs4"), # HTML 파싱용
    ("Pillow", "PIL"),
    ("keyring", "keyring"),
    ("requests-oauthlib", "requests_oauthlib"),
    ("tkcalendar", "tkcalendar"),
    ("selenium", "selenium"), # Selenium 추가
]

# --- 전역 변수 및 설정 (필수 모듈 임포트 전에 정의될 수 있는 것들) ---
SCRIPT_DIR = Path(__file__).resolve().parent
API_CONFIG_FILE = SCRIPT_DIR / "API_Config.json"
POST_PRESET_FILE = SCRIPT_DIR / "Post_Preset.json"
SCHEDULED_POSTS_FILE = SCRIPT_DIR / "Scheduled_Posts.json"
TAG_PRESET_FILE = SCRIPT_DIR / "Tag_Presets.json" # 태그 프리셋 파일 경로
APP_NAME_FOR_KEYRING = "MyAdvancedUploader"
SELENIUM_PROFILES_DIR = SCRIPT_DIR / "selenium_profiles"


OAUTH_CALLBACK_HOST = "localhost" 
OAUTH_CALLBACK_PORT_TUMBLR = 8080
OAUTH_CALLBACK_PORT_TWITTER = 8081 

REDIRECT_URI_TUMBLR = f"http://{OAUTH_CALLBACK_HOST}:{OAUTH_CALLBACK_PORT_TUMBLR}/callback"
REDIRECT_URI_TWITTER = f"http://{OAUTH_CALLBACK_HOST}:{OAUTH_CALLBACK_PORT_TWITTER}/callback" 

# Pixiv 관련 URL
PIXIV_BASE_URL = "https://www.pixiv.net"
PIXIV_LOGIN_URL = "https://accounts.pixiv.net/login"
PIXIV_ILLUST_CREATE_URL = f"{PIXIV_BASE_URL}/illustration/create" 
PIXIV_AJAX_UPLOAD_URL = f"{PIXIV_BASE_URL}/ajax/work/create/illustration" 


INKBUNNY_BASE_URL = "https://inkbunny.net/"
INKBUNNY_API_LOGIN_URL = f"{INKBUNNY_BASE_URL}api_login.php"
INKBUNNY_API_UPLOAD_URL = f"{INKBUNNY_BASE_URL}api_upload.php" 
INKBUNNY_API_EDITSUBMISSION_URL = f"{INKBUNNY_BASE_URL}api_editsubmission.php" 

# --- 패키지 설치 확인 함수 ---
def ensure_packages_installed():
    print("DEBUG: Checking for missing packages...")
    missing_packages = []
    for pkg_name, import_name in REQUIRED_PACKAGES_CORE:
        try:
            if importlib.util.find_spec(import_name) is None:
                missing_packages.append((pkg_name, import_name))
        except ImportError: 
            missing_packages.append((pkg_name, import_name))

    if missing_packages:
        temp_root_for_mb = tk.Tk()
        temp_root_for_mb.withdraw() 
        
        missing_list_str = "\n".join([f"- {pkg} (import name: {imp})" for pkg, imp in missing_packages])
        
        if messagebox.askyesno("필수 모듈 누락",
                               f"다음 필수 Python 모듈이 설치되어 있지 않습니다:\n{missing_list_str}\n\n지금 설치하시겠습니까? (pip 필요)",
                               parent=temp_root_for_mb):
            all_installed_successfully = True
            for pkg_name, _ in missing_packages:
                try:
                    print(f"{pkg_name} 설치 중...")
                    process = subprocess.Popen([sys.executable, "-m", "pip", "install", pkg_name], 
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()
                    
                    if process.returncode != 0:
                         all_installed_successfully = False
                         error_details_for_console = f"--- PIP Install Error for {pkg_name} ---\nSTDOUT:\n{stdout.decode(sys.stdout.encoding or 'utf-8', 'ignore')}\nSTDERR:\n{stderr.decode(sys.stdout.encoding or 'utf-8', 'ignore')}\n--- End PIP Install Error ---"
                         print(error_details_for_console)
                         messagebox.showerror("설치 실패", f"{pkg_name} 설치 중 오류 발생:\n{stderr.decode(sys.stdout.encoding or 'utf-8', 'ignore')}\n\n콘솔에서 자세한 오류를 확인하고 수동으로 설치해주세요: pip install {pkg_name}", parent=temp_root_for_mb)
                    else: 
                        print(f"{pkg_name} 설치 성공.")
                except Exception as e:
                    all_installed_successfully = False
                    print(f"--- Exception during pip install for {pkg_name} ---")
                    import traceback
                    traceback.print_exc()
                    print(f"--- End Exception for {pkg_name} ---")
                    messagebox.showerror("설치 오류", f"{pkg_name} 설치 중 예외 발생: {e}\n콘솔에서 자세한 오류를 확인하고 수동으로 설치해주세요.", parent=temp_root_for_mb)
            
            if all_installed_successfully:
                messagebox.showinfo("설치 완료", "필수 모듈 설치(시도)가 완료되었습니다. 프로그램을 다시 시작해주세요.", parent=temp_root_for_mb)
            else:
                messagebox.showwarning("설치 확인 필요", "일부 모듈 설치에 실패했을 수 있습니다. 콘솔 로그를 확인하고, 문제가 지속되면 프로그램을 다시 시작하거나 수동으로 설치해주세요.", parent=temp_root_for_mb)
            temp_root_for_mb.destroy()
            sys.exit("설치 후 프로그램 재시작 필요")
        else: 
            messagebox.showerror("실행 불가", "필수 모듈이 없어 프로그램을 종료합니다.", parent=temp_root_for_mb)
            temp_root_for_mb.destroy()
            sys.exit("필수 모듈 누락으로 종료")
    print("DEBUG: All required packages are present.")
    return True 

# --- 애플리케이션 주요 로직을 포함할 함수 ---
def run_main_application():
    import customtkinter as ctk
    from PIL import Image 
    import keyring
    from apscheduler.schedulers.background import BackgroundScheduler
    from tkcalendar import DateEntry
    import requests 
    from bs4 import BeautifulSoup 
    
    import mimetypes 
    import webbrowser 
    import re 
    import threading 
    import time 
    from datetime import datetime, timedelta 
    import uuid 
    from http.server import HTTPServer, BaseHTTPRequestHandler 
    from urllib.parse import urlparse, parse_qs, urlencode 
    import queue 
    from tkinter import filedialog, simpledialog 
    import tweepy 
    import pytumblr 
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

    print("DEBUG: Essential libraries for application logic imported successfully.")

    # --- 설정 관리 함수 ---
    def _load_config_generic(filepath_obj, default_value=None):
        if default_value is None:
            default_value = {}
        try:
            with open(filepath_obj, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            return default_value
        except json.JSONDecodeError:
            print(f"Error: Config file at {filepath_obj} is corrupted. Returning default.")
            return default_value
        except Exception as e:
            print(f"Error loading config from {filepath_obj}: {e}")
            return default_value

    def _save_config_generic(filepath_obj, config_data):
        try:
            with open(filepath_obj, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"ERROR: Failed to save app config to {filepath_obj}: {e}")
            return False

    def load_api_config():
        return _load_config_generic(API_CONFIG_FILE)

    def save_api_config(config_data):
        return _save_config_generic(API_CONFIG_FILE, config_data)

    def load_post_preset_config():
        return _load_config_generic(POST_PRESET_FILE)

    def save_post_preset_config(config_data):
        return _save_config_generic(POST_PRESET_FILE, config_data)
    
    def load_tag_presets():
        return _load_config_generic(TAG_PRESET_FILE, default_value={}) # 기본값 빈 딕셔너리

    def save_tag_presets(presets):
        return _save_config_generic(TAG_PRESET_FILE, presets)

    # --- OAuth 콜백 핸들러 ---
    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.callback_queue = kwargs.pop('callback_queue')
            super().__init__(*args, **kwargs)

        def do_GET(self):
            parsed_url = urlparse(self.path)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers() 
            success_html = """
            <html><head><title>인증 성공</title></head>
            <body style='font-family: sans-serif; text-align: center; padding-top: 50px;'>
                <h1>인증 성공!</h1>
                <p>이 창을 닫고 애플리케이션으로 돌아가세요.</p>
                <script>setTimeout(function() { window.close(); }, 1500);</script>
            </body></html>
            """
            self.wfile.write(success_html.encode("utf-8"))

            if self.callback_queue:
                self.callback_queue.put(self.path)
            else:
                print("[OAuthCallbackHandler] ERROR: callback_queue is None!")
        def log_message(self, format, *args):
            return
            
    # --- 계정 관리 클래스 ---
    class AccountManager:
        def __init__(self, app_name_for_keyring):
            self.app_name = app_name_for_keyring
            api_cfg = load_api_config() 
            self.accounts = api_cfg.get("connected_accounts", {})

        def _save_accounts_to_config(self):
            api_cfg = load_api_config()
            api_cfg["connected_accounts"] = self.accounts
            if not save_api_config(api_cfg):
                print("ERROR: Failed to save connected_accounts to API_Config.json.")

        def add_account(self, service, username, details=None):
            if service not in self.accounts:
                self.accounts[service] = []
            
            account_to_update = None
            for i, acc in enumerate(self.accounts[service]):
                if acc.get("username") == username:
                    account_to_update = acc
                    break
            
            if account_to_update: 
                if details: account_to_update.update(details)
                print(f"Updating existing account: {service} - {username}")
            else: 
                account_info = {"username": username}
                if details: account_info.update(details)
                self.accounts[service].append(account_info)
                print(f"Adding new account: {service} - {username}")

            self._save_accounts_to_config()
            return True


        def remove_account(self, service, username):
            if service in self.accounts:
                self.accounts[service] = [acc for acc in self.accounts[service] if acc['username'] != username]
                if not self.accounts[service]: del self.accounts[service]
                self._save_accounts_to_config()
            keyring_service_name = f"{self.app_name}_{service}_{username}"
            try:
                if service == "tumblr":
                    keyring.delete_password(keyring_service_name, "oauth_token")
                    keyring.delete_password(keyring_service_name, "oauth_secret")
                elif service == "twitter": 
                    keyring.delete_password(keyring_service_name, "access_token") 
                    keyring.delete_password(keyring_service_name, "refresh_token") 
                    keyring.delete_password(keyring_service_name, "oauth1_access_token") 
                    keyring.delete_password(keyring_service_name, "oauth1_access_token_secret") 
                elif service == "inkbunny":
                    keyring.delete_password(keyring_service_name, "password")
                elif service == "pixiv":
                    print(f"Pixiv 계정 {username} 정보 삭제 (Keyring에 저장된 토큰은 없음)")
                print(f"Keyring에서 {username} ({service}) 계정의 인증 정보 삭제 시도.")
            except keyring.errors.NoKeyringError: 
                print("Keyring 시스템을 사용할 수 없습니다 (인증 정보 삭제 시).")
            except Exception as e:
                print(f"Keyring에서 자격 증명 삭제 중 오류: {e}")

        def get_connected_accounts(self, service=None):
            if service: return self.accounts.get(service, [])
            return self.accounts
        
        def get_account_details(self, service, username):
            if service in self.accounts:
                return next((acc for acc in self.accounts[service] if acc['username'] == username), None)
            return None

        def store_credential(self, service, username, key, value): 
            keyring_service_name = f"{self.app_name}_{service}_{username}"
            try:
                keyring.set_password(keyring_service_name, key, value)
            except keyring.errors.NoKeyringError:
                messagebox.showerror("오류", "Keyring 시스템을 사용할 수 없습니다.") 
            except Exception as e: messagebox.showerror("오류", f"Keyring 저장 오류: {e}")

        def get_credential(self, service, username, key): 
            keyring_service_name = f"{self.app_name}_{service}_{username}"
            try:
                return keyring.get_password(keyring_service_name, key)
            except keyring.errors.NoKeyringError: return None
            except Exception as e: return None

    # --- 플랫폼별 업로더 클래스 ---
    class BaseUploader:
        def __init__(self, account_manager):
            self.account_manager = account_manager
        def upload(self, account_username, image_path, title, description, tags, rating=None, source_url=None, **kwargs):
            raise NotImplementedError(f"{self.__class__.__name__}의 업로드 기능이 구현되지 않았습니다.")

    class E621Uploader(BaseUploader):
        SERVICE_NAME = "e621"
        def upload(self, account_username, image_path, title, description, tags, rating='s', source_url=None, **kwargs):
            api_cfg = load_api_config()
            e621_api_keys_map = api_cfg.get("e621_api_keys", {})
            api_key = e621_api_keys_map.get(account_username)
            e621_login_user = account_username
            if not api_key:
                return None, f"{account_username}: e621 API 키가 API_Config.json에 없습니다."
            user_agent = f"{APP_NAME_FOR_KEYRING}/1.0 (by {e621_login_user})"
            headers = {"User-Agent": user_agent}
            login_params = {"login": e621_login_user, "api_key": api_key}
            upload_url = "https://e621.net/uploads.json"
            tag_string = " ".join(tags) if isinstance(tags, list) else tags
            data = {
                "upload[tag_string]": tag_string, "upload[rating]": rating if rating else 's',
                "upload[source]": source_url if source_url else "", "upload[description]": description,
            }
            data.update(login_params)
            files = {}
            try:
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type: mime_type = 'application/octet-stream'
                with open(image_path, 'rb') as f:
                    files['upload[file]'] = (Path(image_path).name, f, mime_type)
                    response = requests.post(upload_url, data=data, files=files, headers=headers)
                if response.status_code == 200 or response.status_code == 201:
                    response_json = response.json()
                    if response_json.get("success", True): 
                        post_id = response_json.get("post_id", "알 수 없음")
                        return f"https://e621.net/posts/{post_id}", None
                    else:
                        error_msg = response_json.get("reason", response_json.get("message", "알 수 없는 API 오류"))
                        if "duplicate" in str(error_msg).lower():
                             location = response_json.get('location')
                             if location: return f"https://e621.net{location}", f"중복된 파일 (기존 게시물 링크 반환): {error_msg}"
                             return None, f"중복된 파일: {error_msg}"
                        return None, f"e621 API 오류: {error_msg}"
                elif response.status_code == 412: 
                     response_json = response.json()
                     reason = response_json.get("reason", "알 수 없는 조건 실패")
                     location = response_json.get("location") 
                     if "duplicate" in reason.lower() and location:
                         return f"https://e621.net{location}", f"중복된 파일 (기존 게시물 링크 반환): {reason}"
                     return None, f"e621 오류 ({response.status_code}): {reason}"
                else: return None, f"e621 업로드 실패 ({response.status_code}): {response.text}"
            except requests.exceptions.RequestException as e: return None, f"e621 네트워크 오류: {e}"
            except FileNotFoundError: return None, f"이미지 파일을 찾을 수 없습니다: {image_path}"
            except Exception as e: return None, f"e621 업로드 중 알 수 없는 오류: {e}"


    class TumblrUploader(BaseUploader):
        SERVICE_NAME = "tumblr"
        def __init__(self, account_manager, root_for_dialog):
            super().__init__(account_manager)
            self.root_for_dialog = root_for_dialog
        def _get_authenticated_client(self, account_username, consumer_key, consumer_secret):
            oauth_token = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "oauth_token")
            oauth_secret = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "oauth_secret")
            if not all([consumer_key, consumer_secret, oauth_token, oauth_secret]):
                print(f"Tumblr 인증 정보 부족 (CK/CS/OT/OS): {account_username}")
                return None
            try:
                return pytumblr.TumblrRestClient(consumer_key, consumer_secret, oauth_token, oauth_secret)
            except Exception as e: print(f"pytumblr 클라이언트 생성 실패: {e}"); return None

        def start_oauth_flow(self, callback_queue, consumer_key, consumer_secret, use_pin_auth=False):
            service_name = "Tumblr"
            if not consumer_key or not consumer_secret:
                messagebox.showerror(" 설정 오류", "Tumblr Consumer Key 또는 Secret이 제공되지 않았습니다.", parent=self.root_for_dialog)
                return None, None, [], None  # Consistently return 4 values
            try:
                from requests_oauthlib import OAuth1Session 
                request_token_url = 'https://www.tumblr.com/oauth/request_token'
                oauth_session = OAuth1Session(client_key=consumer_key, client_secret=consumer_secret, callback_uri=None if use_pin_auth else REDIRECT_URI_TUMBLR)
                fetch_response = oauth_session.fetch_request_token(request_token_url)
                resource_owner_key = fetch_response.get('oauth_token')
                resource_owner_secret = fetch_response.get('oauth_token_secret')
                base_authorization_url = 'https://www.tumblr.com/oauth/authorize'
                authorization_url = oauth_session.authorization_url(base_authorization_url)
                webbrowser.open(authorization_url)
                if use_pin_auth:
                    verifier = simpledialog.askstring("Tumblr 인증", "브라우저에서 Tumblr 인증 후 표시되는 PIN(Verifier)을 입력하세요:", parent=self.root_for_dialog)
                    if not verifier: return None, None, [], None 
                else:
                    try:
                        callback_response_path = callback_queue.get(block=True, timeout=300)
                        parsed_callback = urlparse(callback_response_path)
                        query_params = parse_qs(parsed_callback.query)
                        verifier = query_params.get('oauth_verifier', [None])[0]
                        if not verifier:
                            messagebox.showerror("Tumblr 인증 오류", "콜백에서 oauth_verifier를 찾을 수 없습니다.", parent=self.root_for_dialog)
                            return None, None, [], None 
                    except queue.Empty:
                        messagebox.showerror("Tumblr 인증 오류", "인증 시간 초과.", parent=self.root_for_dialog)
                        return None, None, [], None 
                    except Exception as e:
                        messagebox.showerror("Tumblr 인증 오류", f"콜백 처리 중 오류: {e}", parent=self.root_for_dialog)
                        return None, None, [], None 
                access_token_url = 'https://www.tumblr.com/oauth/access_token'
                oauth_session = OAuth1Session(client_key=consumer_key, client_secret=consumer_secret,
                                              resource_owner_key=resource_owner_key, resource_owner_secret=resource_owner_secret,
                                              verifier=verifier)
                access_token_response = oauth_session.fetch_access_token(access_token_url)
                final_oauth_token = access_token_response.get('oauth_token')
                final_oauth_token_secret = access_token_response.get('oauth_token_secret')

                user_blogs_list = []
                primary_blog_name = None
                if final_oauth_token and final_oauth_token_secret:
                    temp_client = pytumblr.TumblrRestClient(consumer_key, consumer_secret, final_oauth_token, final_oauth_token_secret)
                    user_info = temp_client.info()
                    if user_info and 'user' in user_info and user_info['user']['blogs']:
                        for blog_info_item in user_info['user']['blogs']:
                            is_primary = blog_info_item.get('primary', False)
                            blog_details = {
                                'name': blog_info_item['name'],
                                'title': blog_info_item.get('title', blog_info_item['name']),
                                'url': blog_info_item.get('url', ''),
                                'primary': is_primary
                            }
                            user_blogs_list.append(blog_details)
                            if is_primary:
                                primary_blog_name = blog_info_item['name']
                
                return final_oauth_token, final_oauth_token_secret, user_blogs_list, primary_blog_name

            except ImportError:
                messagebox.showerror("라이브러리 오류", "requests-oauthlib 라이브러리가 필요합니다.", parent=self.root_for_dialog); return None, None, [], None
            except Exception as e:
                messagebox.showerror("Tumblr 인증 오류", f"Tumblr OAuth 과정 중 오류: {e}", parent=self.root_for_dialog); return None, None, [], None

        def upload(self, account_username, image_path, title, description, tags, consumer_key, consumer_secret, rating=None, source_url=None, blog_name=None, state="published", **kwargs):
            client = self._get_authenticated_client(account_username, consumer_key, consumer_secret)
            if not client: return None, "Tumblr 클라이언트 인증 실패"
            
            target_blog_name = blog_name 
            if not target_blog_name: 
                acc_details = self.account_manager.get_account_details("tumblr", account_username)
                if acc_details:
                    target_blog_name = acc_details.get("primary_blog_name")
                    if not target_blog_name and acc_details.get("blogs"):
                        target_blog_name = acc_details["blogs"][0]['name'] 
                if not target_blog_name: 
                    try:
                        user_info = client.info()
                        if user_info and 'user' in user_info and user_info['user']['blogs']:
                            primary_blog = next((b for b in user_info['user']['blogs'] if b.get('primary')), None)
                            target_blog_name = primary_blog['name'] if primary_blog else user_info['user']['blogs'][0]['name']
                        else: return None, "Tumblr 블로그 이름을 결정할 수 없습니다."
                    except Exception as e: return None, f"Tumblr 사용자 정보 조회 실패 (업로드 시): {e}"
            
            if not target_blog_name:
                return None, "업로드할 Tumblr 블로그를 지정해야 합니다."

            if isinstance(tags, str): tags = [tag.strip() for tag in tags.split(',')]
            try:
                response = client.create_photo(
                    target_blog_name, state=state, tags=tags,
                    caption=f"{title}\n\n{description}" if title and description else title or description,
                    link=source_url if source_url else "", data=str(image_path)
                )
                if response and ('id' in response or (isinstance(response, list) and response and 'id' in response[0])):
                    post_id = response.get('id') if isinstance(response, dict) else response[0].get('id')
                    return f"https://{target_blog_name}.tumblr.com/post/{post_id}", None
                else: return None, f"Tumblr API 오류: {str(response) if response else '알 수 없는 응답'}"
            except FileNotFoundError: return None, f"이미지 파일을 찾을 수 없습니다: {image_path}"
            except Exception as e: return None, f"Tumblr 업로드 중 알 수 없는 오류: {e}"

    class TwitterUploader(BaseUploader):
        # ... (기존과 동일) ...
        SERVICE_NAME = "twitter"
        def __init__(self, account_manager, root_for_dialog):
            super().__init__(account_manager)
            self.root_for_dialog = root_for_dialog

        def _get_v2_client(self, account_username):
            """OAuth 2.0 PKCE로 얻은 토큰으로 v2 Client 생성"""
            access_token = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "access_token")
            if not access_token:
                print(f"Twitter OAuth 2.0 액세스 토큰 없음: {account_username}")
                return None
            try:
                return tweepy.Client(bearer_token=None, access_token=access_token, access_token_secret=None) 
            except Exception as e:
                print(f"tweepy v2 클라이언트 (OAuth 2.0) 생성 실패: {e}")
                return None

        def _get_v1_api(self, account_username):
            """API_Config.json에 저장된 OAuth 1.0a 정보로 v1.1 API Client 생성"""
            api_cfg = load_api_config()
            oauth1_app_creds = api_cfg.get("twitter_oauth1_app_credentials", {})
            consumer_key = oauth1_app_creds.get("api_key")
            consumer_secret = oauth1_app_creds.get("api_secret_key")
            access_token = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "oauth1_access_token")
            access_token_secret = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "oauth1_access_token_secret")


            if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
                print(f"Twitter OAuth 1.0a 인증 정보 부족 ({account_username}). API 설정에서 앱 및 사용자 토큰 확인 필요.")
                return None
            try:
                auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
                return tweepy.API(auth)
            except Exception as e:
                print(f"tweepy v1.1 API 클라이언트 (OAuth 1.0a) 생성 실패: {e}")
                return None

        def start_oauth_flow(self, callback_queue, client_id, client_secret=None): # OAuth 2.0 PKCE
            service_name = "Twitter"
            print(f"[{service_name} OAuth 2.0] Starting OAuth flow with Client ID: {client_id[:5]}...")
            if not client_id:
                messagebox.showerror("설정 오류", "Twitter Client ID가 제공되지 않았습니다.", parent=self.root_for_dialog)
                return None, None, None, None
            try:
                scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"] 
                print(f"[{service_name} OAuth 2.0] Scopes: {scopes}")
                oauth2_user_handler = tweepy.OAuth2UserHandler(
                    client_id=client_id,
                    redirect_uri=REDIRECT_URI_TWITTER,
                    scope=scopes,
                    client_secret=client_secret
                )
                auth_url = oauth2_user_handler.get_authorization_url()
                print(f"[{service_name} OAuth 2.0] Opening authorization URL in browser: {auth_url}")
                webbrowser.open(auth_url)
                print(f"[{service_name} OAuth 2.0] Waiting for callback from queue (timeout 300s)...")
                try:
                    callback_response_url = callback_queue.get(block=True, timeout=300)
                    token_response = oauth2_user_handler.fetch_token(callback_response_url)
                    access_token = token_response.get("access_token")
                    refresh_token = token_response.get("refresh_token")
                    
                    temp_client = tweepy.Client(access_token=access_token) 
                    user_info_resp = temp_client.get_me(user_fields=["username", "id"])
                    user_id_str = str(user_info_resp.data.id) if user_info_resp.data else None
                    twitter_username = user_info_resp.data.username if user_info_resp.data else "UnknownTwitterUser"
                    print(f"[{service_name} OAuth 2.0] User Info: ID={user_id_str}, Username={twitter_username}")
                    return access_token, refresh_token, twitter_username, user_id_str
                except queue.Empty:
                    messagebox.showerror("Twitter 인증 오류", "인증 시간 초과.", parent=self.root_for_dialog); return None,None,None,None
                except Exception as e:
                    messagebox.showerror("Twitter 인증 오류", f"콜백/토큰 처리 오류: {e}", parent=self.root_for_dialog); return None,None,None,None
            except ImportError:
                messagebox.showerror("라이브러리 오류", "tweepy 라이브러리가 필요합니다.", parent=self.root_for_dialog); return None,None,None,None
            except Exception as e:
                messagebox.showerror("Twitter 인증 오류", f"Twitter OAuth 과정 중 오류: {e}", parent=self.root_for_dialog); return None,None,None,None


        def upload(self, account_username, image_path, title, description, tags, client_id, client_secret=None, rating=None, source_url=None, **kwargs):
            api_v1 = self._get_v1_api(account_username)
            if not api_v1:
                return None, f"Twitter 미디어 업로드 실패: {account_username} 계정의 OAuth 1.0a 설정이 필요합니다. API 설정에서 Twitter (OAuth 1.0a) 정보를 입력하세요."

            client_v2 = self._get_v2_client(account_username)
            if not client_v2:
                 return None, f"Twitter 트윗 생성 실패: {account_username} 계정의 OAuth 2.0 인증이 필요합니다."


            tweet_text = f"{title}\n\n{description}" if title and description else title or description or ""
            if tags:
                hashtags = " ".join([f"#{tag.replace(' ', '_')}" for tag in tags])
                tweet_text += f"\n\n{hashtags}"
            if len(tweet_text) > 280: tweet_text = tweet_text[:277] + "..."
            
            media_ids_list = []
            if Path(image_path).exists():
                try:
                    print(f"Twitter: 이미지({image_path}) 업로드 시도 중 (OAuth 1.0a 사용)...")
                    media = api_v1.media_upload(filename=str(image_path))
                    media_ids_list.append(media.media_id_string)
                    print(f"Twitter: Media ID 획득: {media.media_id_string}")
                except tweepy.TweepyException as e:
                    return None, f"Twitter 미디어 업로드 실패 (v1.1 API): {e}"
                except Exception as e:
                    return None, f"Twitter 미디어 업로드 중 알 수 없는 오류: {e}"
            
            try:
                response = client_v2.create_tweet(text=tweet_text, media_ids=media_ids_list if media_ids_list else None)
                if response and response.data and response.data.get('id'):
                    tweet_id = response.data['id']
                    tweet_url = f"https://twitter.com/{account_username}/status/{tweet_id}" 
                    return tweet_url, None
                else:
                    error_msg = str(response.errors) if hasattr(response, 'errors') and response.errors else str(response.data)
                    return None, f"Twitter API 응답 오류 (트윗 생성): {error_msg}"
            except tweepy.TweepyException as e: return None, f"Twitter API 오류 (트윗 생성): {e}"
            except Exception as e: return None, f"Twitter 트윗 생성 중 알 수 없는 오류: {e}"

    class PixivUploader(BaseUploader):
        SERVICE_NAME = "pixiv"

        def __init__(self, account_manager, root_for_dialog):
            super().__init__(account_manager)
            self.root_for_dialog = root_for_dialog

        def _get_webdriver(self, profile_name="default_pixiv_profile", headless=True):
            options = ChromeOptions()
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            if headless:
                options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            profile_path = SELENIUM_PROFILES_DIR / profile_name
            profile_path.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"user-data-dir={str(profile_path.resolve())}")

            driver = None
            try:
                service = ChromeService() 
                driver = webdriver.Chrome(service=service, options=options)
                if headless: 
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                              get: () => undefined
                            });
                        """
                    })
                return driver
            except WebDriverException as e:
                messagebox.showerror("WebDriver 오류", f"ChromeDriver를 시작할 수 없습니다. 설치되어 있고 PATH에 설정되어 있는지 확인하세요.\n오류: {e}", parent=self.root_for_dialog)
                if driver: driver.quit()
                return None
            except Exception as e:
                messagebox.showerror("오류", f"WebDriver 초기화 중 오류 발생: {e}", parent=self.root_for_dialog)
                if driver: driver.quit()
                return None

        def login_with_browser(self, profile_name_for_login):
            driver = self._get_webdriver(profile_name_for_login, headless=False) 
            if not driver:
                return False, "WebDriver 초기화 실패"
            
            try:
                driver.get(PIXIV_LOGIN_URL)
                login_instructions = (
                    "브라우저 창이 열립니다. Pixiv에 로그인해주세요.\n\n"
                    "**중요:** 로그인이 완료되고 Pixiv 메인 페이지(홈) 또는 사용자 대시보드가 완전히 로드된 것을 확인한 후, "
                    "이 메시지 창의 '확인' 버튼을 눌러주세요.\n\n"
                    "로그인 후 브라우저 창은 이 프로그램이 자동으로 닫습니다."
                )
                messagebox.showinfo("Pixiv 로그인 필요", login_instructions, parent=self.root_for_dialog) 

                time.sleep(1) 
                
                driver.get(PIXIV_BASE_URL) 
                WebDriverWait(driver, 15).until(EC.url_to_be(PIXIV_BASE_URL + "/")) 

                current_url = driver.current_url
                if "pixiv.net" in current_url and "accounts.pixiv.net/login" not in current_url:
                    print(f"[Pixiv Login] 사용자가 로그인을 확인했습니다. 현재 URL: {current_url}")
                    self.account_manager.add_account(self.SERVICE_NAME, profile_name_for_login, {"login_method": "browser_session", "status": "logged_in"})
                    return True, f"{profile_name_for_login} 계정으로 Pixiv 로그인 세션이 준비되었습니다."
                else:
                    print(f"[Pixiv Login] 로그인 페이지에 머물러 있거나 예기치 않은 URL: {current_url}. 로그인이 완료되지 않았을 수 있습니다.")
                    return False, "Pixiv 로그인이 완료되지 않은 것 같습니다. 브라우저에서 로그인을 마치고 다시 시도해주세요."

            except TimeoutException:
                 print(f"[Pixiv Login] Pixiv 메인 페이지 로딩 시간 초과. 로그인이 완료되지 않았거나 네트워크 문제일 수 있습니다.")
                 return False, "Pixiv 메인 페이지 로딩 시간 초과. 로그인이 완료되지 않았거나 네트워크 문제일 수 있습니다."
            except WebDriverException as e:
                print(f"[Pixiv Login] WebDriverException: {e}")
                return False, f"Pixiv 로그인 중 WebDriver 오류 발생: {e}\nChromeDriver 설정을 확인하세요."
            except Exception as e:
                print(f"[Pixiv Login] Exception: {e}")
                return False, f"Pixiv 로그인 중 예상치 못한 오류 발생: {e}"
            finally:
                if driver:
                    driver.quit()


        def _get_csrf_token(self, driver_instance):
            if not driver_instance:
                return None, None 
            try:
                print(f"[Pixiv CSRF] CSRF 토큰을 얻기 위해 {PIXIV_ILLUST_CREATE_URL}로 이동합니다.")
                driver_instance.get(PIXIV_ILLUST_CREATE_URL)
                
                token = None
                try:
                    print("[Pixiv CSRF] meta-global-data에서 토큰 추출 시도...")
                    WebDriverWait(driver_instance, 20).until(
                        EC.presence_of_element_located((By.ID, "meta-global-data"))
                    )
                    meta_tag = driver_instance.find_element(By.ID, "meta-global-data")
                    global_data_json = meta_tag.get_attribute("content")
                    if global_data_json:
                        global_data = json.loads(global_data_json)
                        token = global_data.get("token") 
                        if token: print(f"Pixiv CSRF 토큰 (meta-global-data): {token}")
                except (TimeoutException, NoSuchElementException, json.JSONDecodeError) as e:
                    print(f"[Pixiv CSRF] meta-global-data 방식 실패 또는 오류: {e}")

                if not token:
                    try:
                        print("[Pixiv CSRF] __NEXT_DATA__에서 토큰 추출 시도...")
                        WebDriverWait(driver_instance, 10).until( 
                            EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                        )
                        next_data_script = driver_instance.find_element(By.ID, "__NEXT_DATA__")
                        script_content = next_data_script.get_attribute('innerHTML')
                        if script_content:
                            json_data = json.loads(script_content)
                            token = json_data.get("props", {}).get("pageProps", {}).get("token")
                            if not token: 
                                preloaded_state = json_data.get("props", {}).get("pageProps", {}).get("serverSerializedPreloadedState", {})
                                if isinstance(preloaded_state, str): 
                                    try: preloaded_state = json.loads(preloaded_state)
                                    except: preloaded_state = {}
                                token = preloaded_state.get("api", {}).get("token")
                            if token: print(f"Pixiv CSRF 토큰 (__NEXT_DATA__): {token}")
                    except (TimeoutException, NoSuchElementException, json.JSONDecodeError) as e:
                        print(f"[Pixiv CSRF] __NEXT_DATA__ 방식 실패 또는 오류: {e}")
                
                if not token:
                    print("[Pixiv CSRF] 알려진 input 필드에서 토큰 검색 시도...")
                    page_source = driver_instance.page_source 
                    soup = BeautifulSoup(page_source, 'html.parser')
                    tt_input = soup.find('input', {'name': 'tt'})
                    if tt_input and tt_input.get('value'):
                        token = tt_input.get('value')
                        print(f"Pixiv CSRF 토큰 (tt input): {token}")
                    else:
                        post_key_input = soup.find('input', {'name': 'post_key'})
                        if post_key_input and post_key_input.get('value'):
                            token = post_key_input.get('value')
                            print(f"Pixiv CSRF 토큰 (post_key input): {token}")
                
                if token:
                    selenium_cookies = driver_instance.get_cookies()
                    request_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
                    return token, request_cookies
                else:
                    print("Pixiv CSRF 토큰을 찾을 수 없습니다.")
                    print(f"[Pixiv CSRF] 토큰 못 찾음. 현재 URL: {driver_instance.current_url}, 타이틀: {driver_instance.title}")
                    return None, None

            except TimeoutException:
                print("[Pixiv CSRF] 페이지 로딩 시간 초과 (CSRF 토큰 추출 페이지)")
                return None, None
            except Exception as e:
                print(f"Pixiv CSRF 토큰 및 쿠키 추출 중 오류: {e}")
                import traceback
                traceback.print_exc()
                return None, None

        def upload(self, account_username, image_path, title, description, tags, rating=None, source_url=None, **kwargs):
            driver = self._get_webdriver(account_username, headless=True) 
            if not driver:
                return None, "WebDriver 초기화 실패 (업로드)"

            csrf_token, request_cookies = None, None
            try:
                csrf_token, request_cookies = self._get_csrf_token(driver)
                if not csrf_token or not request_cookies:
                    return None, "Pixiv CSRF 토큰 또는 쿠키를 가져올 수 없습니다. 로그인이 유효한지 확인하세요."
            finally: 
                if driver:
                    driver.quit()
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
                "X-CSRF-Token": csrf_token, 
                "Referer": PIXIV_ILLUST_CREATE_URL,
                "Origin": PIXIV_BASE_URL,
                "Accept": "application/json", 
            }
            
            # PostyBirb의 postFileSubmissionNew의 form 객체 참고하여 payload 구성
            payload_dict = {
                "title": title[:32],
                "caption": description,
                "tags": tags[:10], # 리스트로 전달, requests가 처리
                "allowTagEdit": "true" if kwargs.get("community_tags", True) else "false",
                "xRestrict": "general", 
                "aiType": "notAiGenerated",
                "restrict": "public", 
                "responseAutoAccept": "false",
                "suggestedtags[]": [], 
                "original": "true" if kwargs.get("original_work", True) else "false",
                "ratings": { "violent": "false", "drug": "false", "thoughts": "false", "antisocial": "false", "religion": "false" },
                "attributes": { "yuri": "false", "bl": "false", "furry": "false", "lo": "false" },
                "tweet": "false",
                "allowComment": "true",
                "titleTranslations[en]": "", 
                "captionTranslations[en]": "",
            }
            # xRestrict 및 sexual 필드 조정 (PostyBirb 로직 참고)
            if rating == 'q': 
                payload_dict['xRestrict'] = 'r18'
                # r18 이상일 경우 sexual 필드는 PostyBirb에서 제거되므로, 여기서도 명시적으로 설정하지 않거나 제거
                if 'sexual' in payload_dict: del payload_dict['sexual']
                if kwargs.get('mature_content'): 
                    for content_type in kwargs['mature_content']:
                        if content_type in payload_dict['attributes']:
                            payload_dict['attributes'][content_type] = 'true'
            elif rating == 'e': 
                payload_dict['xRestrict'] = 'r18g' 
                if 'sexual' in payload_dict: del payload_dict['sexual']
                if kwargs.get('mature_content'):
                    for content_type in kwargs['mature_content']:
                         if content_type in payload_dict['attributes']:
                            payload_dict['attributes'][content_type] = 'true'
            else: # General
                 payload_dict['sexual'] = 'true' if kwargs.get('sexual_content', False) else 'false'
            
            if 'sexual' not in payload_dict and payload_dict['xRestrict'] == 'general':
                payload_dict['sexual'] = 'false'


            if kwargs.get('ai_generated', False):
                payload_dict['aiType'] = 'aiGenerated'
            
            if kwargs.get('contains_content'): 
                for content_type in kwargs['contains_content']:
                    if content_type in payload_dict['ratings']:
                        payload_dict['ratings'][content_type] = 'true'

            # 최종 데이터 리스트 구성 (튜플 리스트 for requests data)
            final_data_list = []
            for key, value in payload_dict.items():
                if key == "tags": # 태그는 'tags[]'로 여러번 보내야 함
                    for tag_item in value: # value는 이미 리스트여야 함
                        final_data_list.append(('tags[]', tag_item))
                elif key == "suggestedtags[]": # 이것도 리스트
                     for stag_item in value:
                         final_data_list.append(('suggestedtags[]', stag_item))
                elif isinstance(value, dict): # ratings, attributes는 평탄화
                    for sub_key, sub_value in value.items():
                        final_data_list.append((f'{key}[{sub_key}]', str(sub_value)))
                else:
                    final_data_list.append((key, str(value)))
            
            # imageOrder는 PostyBirb에서 FormData에 직접 추가됨.
            # 이 엔드포인트는 JSON body + 파일일 수도 있고, 순수 FormData일 수도 있음.
            # PostyBirb의 postSpecial은 FormData를 사용하므로, 여기도 FormData로.
            final_data_list.append(('imageOrder[0][type]', 'newFile'))
            final_data_list.append(('imageOrder[0][fileKey]: ', '0')) # PostyBirb의 키 이름


            files_to_upload = {}
            opened_file = None
            try:
                opened_file = open(image_path, 'rb')
                # PostyBirb는 files[] 필드명 사용
                files_to_upload['files[]'] = (Path(image_path).name, opened_file, mimetypes.guess_type(image_path)[0] or 'application/octet-stream')
            except FileNotFoundError:
                if opened_file: opened_file.close()
                return None, f"이미지 파일을 찾을 수 없습니다: {image_path}"
            
            print(f"[Pixiv Upload] 최종 데이터 (튜플 리스트 전송용): {final_data_list}")
            print(f"[Pixiv Upload] 파일: {files_to_upload.keys()}")
            print(f"[Pixiv Upload] 헤더: {headers.keys()}")
            
            try:
                response = requests.post(
                    PIXIV_AJAX_UPLOAD_URL, 
                    headers=headers,
                    cookies=request_cookies,
                    data=final_data_list, 
                    files=files_to_upload,
                    verify=False 
                )
                response.raise_for_status()
                response_json = response.json()

                print(f"[Pixiv Upload] 응답: {response_json}")
                if not response_json.get('error'):
                    post_id = response_json.get('body', {}).get('id', response_json.get('id')) 
                    if post_id:
                         return f"{PIXIV_BASE_URL}/artworks/{post_id}", None
                    return f"{PIXIV_BASE_URL}/?upload_successful_id_unknown", None 
                else:
                    error_message = response_json.get('message', '알 수 없는 Pixiv API 오류')
                    # PostyBirb에서 body.errors.imageOrder와 같은 상세 오류 메시지 파싱 참고
                    if isinstance(response_json.get('body'), dict) and 'errors' in response_json.get('body'):
                        errors_dict = response_json.get('body')['errors']
                        first_error_key = next(iter(errors_dict)) if errors_dict else None
                        if first_error_key:
                            error_message = f"{first_error_key}: {errors_dict[first_error_key]}"
                    elif isinstance(response_json.get('body'), dict) and 'error_detail' in response_json.get('body'):
                         error_message = response_json.get('body')['error_detail'].get('user_message', error_message)


                    return None, f"Pixiv API 오류: {error_message}"

            except requests.exceptions.RequestException as e:
                err_msg = f"Pixiv 업로드 요청 실패: {e}"
                if e.response is not None: 
                    err_msg += f"\n응답 상태: {e.response.status_code}"
                    try: err_msg += f"\n응답 내용: {e.response.json()}" 
                    except: err_msg += f"\n응답 내용: {e.response.text}" 
                return None, err_msg
            except Exception as e_upload:
                import traceback
                traceback.print_exc()
                return None, f"Pixiv 업로드 중 알 수 없는 오류: {e_upload}"
            finally:
                if opened_file:
                    opened_file.close()


    class FurAffinityUploader(BaseUploader):
        # ... (기존과 동일) ...
        SERVICE_NAME = "furaffinity"
        def __init__(self, account_manager, root_for_dialog):
            super().__init__(account_manager)
            self.root_for_dialog = root_for_dialog 
        def upload(self, account_username, image_path, title, description, tags, **kwargs):
            api_cfg = load_api_config()
            fa_auth_info_map = api_cfg.get("furaffinity_auth_info", {}) 
            auth_info = fa_auth_info_map.get(account_username)

            if not auth_info:
                return None, f"{account_username}: FurAffinity 인증 정보가 API_Config.json에 없습니다."
            print(f"FurAffinity 업로드 시도: 사용자={account_username}, 파일={image_path} (구현 필요)")
            return None, super().upload(account_username, image_path, title, description, tags, **kwargs)

    class InkbunnyUploader(BaseUploader):
        # ... (기존과 동일) ...
        SERVICE_NAME = "inkbunny"

        def __init__(self, account_manager, root_for_dialog):
            super().__init__(account_manager)
            self.root_for_dialog = root_for_dialog

        def _ib_api_call(self, url, params=None, files=None, sid=None, method='post'):
            if params is None:
                params = {}
            if sid: 
                params['sid'] = sid
            
            response = None 
            try:
                if method.lower() == 'post':
                    response = requests.post(url, data=params, files=files, timeout=120) 
                else: 
                    response = requests.get(url, params=params, timeout=30)
                
                response.raise_for_status() 
                
                if not response.text.strip():
                    return {}, None 

                try:
                    data = response.json()
                except json.JSONDecodeError:
                    if response.ok and response.text.strip().upper().startswith("ERROR:"):
                        return None, response.text.strip() 
                    return None, f"API 반환값 JSON 파싱 실패: {response.text}" 
                
                if 'error_code' in data and str(data['error_code']) != "0": 
                    error_message = data.get('error_message', 'Unknown Inkbunny API error')
                    return None, error_message
                
                if 'sid' in data and sid and data['sid'] != sid: 
                    pass

                return data, None 
                
            except requests.exceptions.HTTPError as e:
                err_text = e.response.text if e.response else "No response body"
                return None, f"HTTP 오류 ({e.response.status_code if e.response else 'N/A'}): {err_text}"
            except requests.exceptions.RequestException as e: 
                return None, f"네트워크 오류: {e}"
            except Exception as e: 
                import traceback
                print(f"[_ib_api_call] 알 수 없는 오류: {traceback.format_exc()}")
                return None, f"알 수 없는 오류: {e}"

        def _ib_login(self, username, password):
            payload = {"username": username, "password": password, "output_mode": "json"} 
            
            data, error_msg = self._ib_api_call(INKBUNNY_API_LOGIN_URL, params=payload)
            
            if error_msg:
                return None, None, error_msg
            
            if data and "sid" in data:
                sid = data["sid"]
                user_id = data.get("user_id") 
                return sid, user_id, None
            else:
                return None, None, data.get("error_message", "로그인 실패: SID 또는 사용자 ID를 받지 못했습니다.")


        def _ib_perform_file_upload(self, sid, image_path):
            params = {'output_mode': 'json'} 
            files_payload = {}
            file_p = Path(image_path)

            try:
                with open(file_p, 'rb') as f_obj:
                    files_payload['uploadedfile[]'] = (file_p.name, f_obj.read(), mimetypes.guess_type(file_p)[0] or 'application/octet-stream')
            except FileNotFoundError:
                return None, f"파일을 찾을 수 없습니다: {image_path}"
            except Exception as e:
                return None, f"파일 처리 중 오류: {e}"

            data, error_msg = self._ib_api_call(INKBUNNY_API_UPLOAD_URL, params=params, files=files_payload, sid=sid)

            if error_msg:
                return None, error_msg
            
            if data and data.get('submission_id'): 
                submission_id = str(data['submission_id'])
                return submission_id, None
            else:
                err = data.get("error_message", f"파일 업로드 실패: 응답에 submission_id가 없습니다. 응답: {str(data)[:200]}")
                return None, err


        def _ib_edit_submission_details(self, sid, submission_id, title, description, tags, rating_app, submission_type='1'): 
            params = {
                'submission_id': submission_id,
                'title': title,
                'desc': description, 
                'keywords': ",".join(tags) if isinstance(tags, list) else tags, 
                'type_': submission_type, 
                'scraps': 'no', 
                'output_mode': 'json' 
            }

            if rating_app == 'q': 
                params['tag[3]'] = 'yes' 
            elif rating_app == 'e': 
                params['tag[4]'] = 'yes' 
            else: 
                params['tag[2]'] = 'yes' 


            data, error_msg = self._ib_api_call(INKBUNNY_API_EDITSUBMISSION_URL, params=params, sid=sid)

            if error_msg:
                return False, error_msg
            
            if data and (str(data.get("error_code", "0")) == "0" or data.get("error_code") is None): 
                if str(data.get('submission_id')) == str(submission_id) or not data.get('submission_id'): 
                     return True, None
                else:
                     err = f"메타데이터 업데이트 후 반환된 submission_id 불일치: {data.get('submission_id')}"
                     return False, err
            else:
                err = data.get("error_message", f"메타데이터 업데이트 실패. 응답: {str(data)[:200]}")
                return False, err

        def _ib_set_submission_visibility(self, sid, submission_id, visibility_status="yes"): 
            params = {
                'submission_id': submission_id,
                'visibility': visibility_status, 
                'output_mode': 'json' 
            }

            data, error_msg = self._ib_api_call(INKBUNNY_API_EDITSUBMISSION_URL, params=params, sid=sid)

            if error_msg:
                return False, error_msg
            
            if data and (str(data.get("error_code", "0")) == "0" or data.get("error_code") is None):
                return True, None
            else:
                err = data.get("error_message", f"공개 상태 변경 실패. 응답: {str(data)[:200]}")
                return False, err

        def upload(self, account_username, image_path, title, description, tags, rating=None, source_url=None, **kwargs):
            password = self.account_manager.get_credential(self.SERVICE_NAME, account_username, "password")
            if not password:
                return None, f"{account_username}: Inkbunny 비밀번호를 Keyring에서 찾을 수 없습니다."

            sid, _, login_error = self._ib_login(account_username, password)
            if login_error or not sid:
                return None, f"Inkbunny 로그인 실패: {login_error}"

            final_description = description
            if source_url:
                final_description += f"\n\nSource: {source_url}"

            submission_id, upload_error = self._ib_perform_file_upload(sid, image_path)
            if upload_error or not submission_id:
                return None, f"Inkbunny 파일 업로드 실패: {upload_error}"

            current_tags = list(tags) 
            min_tags_inkbunny = 4
            if len(current_tags) < min_tags_inkbunny:
                num_tags_to_add = min_tags_inkbunny - len(current_tags)
                base_auto_tag = "auto_tag" 
                existing_tags_lower = {t.lower() for t in current_tags}
                default_tags_to_add = []
                i = 1
                while len(default_tags_to_add) < num_tags_to_add:
                    new_tag = f"{base_auto_tag}_{i}"
                    if new_tag.lower() not in existing_tags_lower:
                        default_tags_to_add.append(new_tag)
                    i += 1
                current_tags.extend(default_tags_to_add)
            
            metadata_success, edit_error = self._ib_edit_submission_details(sid, submission_id, title, final_description, current_tags, rating, submission_type='1')
            if edit_error or not metadata_success:
                msg = f"Inkbunny 메타데이터 업데이트 실패: {edit_error}. 파일은 ID {submission_id}(으)로 업로드되었으나, 정보 수정이 필요할 수 있습니다."
                return f"https://inkbunny.net/s/{submission_id} (메타데이터 설정 오류)", msg
            
            visibility_success, visibility_error = self._ib_set_submission_visibility(sid, submission_id, "yes") 
            if visibility_error or not visibility_success:
                msg = f"Inkbunny 게시물 공개 설정 실패: {visibility_error}. 게시물 ID: {submission_id} (비공개 상태일 수 있음)."
                return f"https://inkbunny.net/s/{submission_id} (공개 설정 실패)", msg
                
            submission_url = f"https://inkbunny.net/s/{submission_id}"
            return submission_url, None

    # --- API 연결 대화창 ---
    # ... (ApiConnectionDialog 클래스 내 _create_pixiv_tab 메서드만 아래와 같이 수정, 나머지는 이전과 유사) ...
    class ApiConnectionDialog(ctk.CTkToplevel):
        def __init__(self, master, account_manager):
            super().__init__(master)
            self.title("API 계정 연결 관리")
            self.geometry("700x800") 
            self.master_app = master 
            self.account_manager = account_manager
            self.api_config_dialog_copy = load_api_config() 

            self.oauth_callback_queue = queue.Queue() 
            self.local_http_server = None
            self.server_thread = None
            self.protocol("WM_DELETE_WINDOW", self._on_close) 

            self.tab_view = ctk.CTkTabview(self, width=680) 
            self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)
            self.tab_view.add("e621"); self.tab_view.add("Tumblr"); self.tab_view.add("Twitter")
            self.tab_view.add("Pixiv"); self.tab_view.add("FurAffinity"); self.tab_view.add("Inkbunny")

            self._create_e621_tab(self.tab_view.tab("e621"))
            self._create_tumblr_tab(self.tab_view.tab("Tumblr"))
            self._create_twitter_tab(self.tab_view.tab("Twitter"))
            self._create_pixiv_tab(self.tab_view.tab("Pixiv")) 
            self._create_furaffinity_tab(self.tab_view.tab("FurAffinity"))
            self._create_inkbunny_tab(self.tab_view.tab("Inkbunny"))

            self._create_connected_accounts_frame()

        def _start_local_server(self, port): 
            if self.server_thread and self.server_thread.is_alive():
                self._stop_local_server() 
            try:
                handler_class = lambda *args, **kwargs: OAuthCallbackHandler(*args, callback_queue=self.oauth_callback_queue, **kwargs)
                self.local_http_server = HTTPServer((OAUTH_CALLBACK_HOST, port), handler_class)
                self.server_thread = threading.Thread(target=self.local_http_server.serve_forever, daemon=True)
                self.server_thread.start()
                print(f"로컬 HTTP 서버 시작됨 (포트: {port})")
                return True
            except OSError as e: 
                 messagebox.showerror("서버 오류", f"로컬 HTTP 서버 시작 실패 (포트 {port}): {e}\n다른 프로그램이 해당 포트를 사용 중일 수 있습니다.", parent=self)
                 self.local_http_server = None; self.server_thread = None
                 return False
            except Exception as e:
                messagebox.showerror("서버 오류", f"로컬 HTTP 서버 시작 실패: {e}", parent=self)
                self.local_http_server = None; self.server_thread = None
                return False

        def _stop_local_server(self): 
            if self.local_http_server:
                print("로컬 HTTP 서버 종료 중...")
                shutdown_thread = threading.Thread(target=self.local_http_server.shutdown, daemon=True)
                shutdown_thread.start()
                shutdown_thread.join(timeout=2) 
                self.local_http_server.server_close() 
                self.local_http_server = None
                print("로컬 HTTP 서버 종료됨.")

            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=1) 
                self.server_thread = None
                print("서버 스레드 종료됨.")


        def _on_close(self):
            self._save_api_keys_to_api_config() 
            self._stop_local_server() 
            self.destroy()
            if hasattr(self.master_app, 'reload_api_config_and_update_ui'):
                self.master_app.reload_api_config_and_update_ui()


        def _save_api_keys_to_api_config(self): 
            current_api_cfg_on_disk = load_api_config() 

            if hasattr(self, 'tumblr_consumer_key_entry'): self.api_config_dialog_copy["tumblr_consumer_key"] = self.tumblr_consumer_key_entry.get()
            if hasattr(self, 'tumblr_consumer_secret_entry'): self.api_config_dialog_copy["tumblr_consumer_secret"] = self.tumblr_consumer_secret_entry.get()
            
            if hasattr(self, 'twitter_oauth1_consumer_key_entry'): self.api_config_dialog_copy.setdefault("twitter_oauth1_app_credentials", {})["api_key"] = self.twitter_oauth1_consumer_key_entry.get()
            if hasattr(self, 'twitter_oauth1_consumer_secret_entry'): self.api_config_dialog_copy.setdefault("twitter_oauth1_app_credentials", {})["api_secret_key"] = self.twitter_oauth1_consumer_secret_entry.get()
            
            twitter_user_for_oauth1_entry_widget = getattr(self, 'twitter_username_for_oauth1_entry', None) 
            if twitter_user_for_oauth1_entry_widget:
                twitter_user_for_oauth1 = twitter_user_for_oauth1_entry_widget.get()
                if twitter_user_for_oauth1: 
                    self.api_config_dialog_copy.setdefault("twitter_user_oauth1_tokens", {}).setdefault(twitter_user_for_oauth1, {})
                    if hasattr(self, 'twitter_oauth1_access_token_entry'):
                        user_access_token = self.twitter_oauth1_access_token_entry.get()
                        user_access_token_secret = self.twitter_oauth1_access_token_secret_entry.get()
                        if user_access_token and user_access_token_secret:
                            self.account_manager.store_credential("twitter", twitter_user_for_oauth1, "oauth1_access_token", user_access_token)
                            self.account_manager.store_credential("twitter", twitter_user_for_oauth1, "oauth1_access_token_secret", user_access_token_secret)
                            self.api_config_dialog_copy["twitter_user_oauth1_tokens"][twitter_user_for_oauth1]["has_oauth1_tokens"] = True
                        else: 
                             if twitter_user_for_oauth1 in self.api_config_dialog_copy.get("twitter_user_oauth1_tokens", {}):
                                 del self.api_config_dialog_copy["twitter_user_oauth1_tokens"][twitter_user_for_oauth1]


            if hasattr(self, 'twitter_client_id_entry'): self.api_config_dialog_copy["twitter_client_id"] = self.twitter_client_id_entry.get()
            if hasattr(self, 'twitter_client_secret_entry'): self.api_config_dialog_copy["twitter_client_secret"] = self.twitter_client_secret_entry.get()
            
            for key, value in self.api_config_dialog_copy.items():
                if key != "connected_accounts": 
                    current_api_cfg_on_disk[key] = value
            
            if save_api_config(current_api_cfg_on_disk):
                self.api_config_dialog_copy = current_api_cfg_on_disk 
            else:
                print("ERROR: API Key/Secret 설정 저장 실패.")
                messagebox.showerror("저장 오류", "API Key/Secret 설정 저장에 실패했습니다. 콘솔 로그를 확인하세요.", parent=self)


        def _create_e621_tab(self, tab):
            ctk.CTkLabel(tab, text="e621 계정 연결 (API 키 사용)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            ctk.CTkLabel(tab, text="e621 사용자 이름:").pack(pady=(5,0))
            self.e621_username_entry = ctk.CTkEntry(tab, width=250)
            self.e621_username_entry.pack()
            ctk.CTkLabel(tab, text="e621 API 키:").pack(pady=(10,0))
            self.e621_apikey_entry = ctk.CTkEntry(tab, width=350, show="*")
            self.e621_apikey_entry.pack()

            def _load_e621_key_on_user_change(event=None):
                user = self.e621_username_entry.get()
                if user:
                    keys_map = self.api_config_dialog_copy.get("e621_api_keys", {})
                    self.e621_apikey_entry.delete(0, tk.END)
                    self.e621_apikey_entry.insert(0, keys_map.get(user, ""))
            self.e621_username_entry.bind("<FocusOut>", _load_e621_key_on_user_change)
            self.e621_username_entry.bind("<Return>", _load_e621_key_on_user_change)


            ctk.CTkButton(tab, text="e621 API 키 도움말", command=lambda: webbrowser.open("https://e621.net/help/api")).pack(pady=5)
            ctk.CTkButton(tab, text="e621 계정 저장", command=self._connect_e621).pack(pady=10)

        def _connect_e621(self):
            e621_user = self.e621_username_entry.get()
            api_key = self.e621_apikey_entry.get()
            if not e621_user or not api_key:
                messagebox.showerror("입력 오류", "e621 사용자 이름과 API 키를 모두 입력하세요.", parent=self)
                return

            if "e621_api_keys" not in self.api_config_dialog_copy:
                self.api_config_dialog_copy["e621_api_keys"] = {}
            self.api_config_dialog_copy["e621_api_keys"][e621_user] = api_key

            if self.account_manager.add_account("e621", e621_user): 
                messagebox.showinfo("e621 연결", f"{e621_user} 계정 정보가 추가되었습니다. API 키는 대화창을 닫을 때 설정 파일에 저장됩니다.", parent=self)
                self._update_connected_accounts_list() 
            else:
                messagebox.showinfo("e621 정보 업데이트", f"{e621_user} 계정의 API 키 정보가 업데이트되었습니다 (저장 예정).", parent=self)


        def _create_tumblr_tab(self, tab):
            ctk.CTkLabel(tab, text="Tumblr 계정 연결 (OAuth 1.0a)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            key_frame = ctk.CTkFrame(tab, fg_color="transparent")
            key_frame.pack(pady=5, fill="x", padx=20)
            ctk.CTkLabel(key_frame, text="Consumer Key:").pack(side="left", padx=(0,5))
            self.tumblr_consumer_key_entry = ctk.CTkEntry(key_frame, width=300)
            self.tumblr_consumer_key_entry.pack(side="left", expand=True, fill="x")
            self.tumblr_consumer_key_entry.insert(0, self.api_config_dialog_copy.get("tumblr_consumer_key", ""))

            secret_frame = ctk.CTkFrame(tab, fg_color="transparent")
            secret_frame.pack(pady=5, fill="x", padx=20)
            ctk.CTkLabel(secret_frame, text="Consumer Secret:").pack(side="left", padx=(0,5))
            self.tumblr_consumer_secret_entry = ctk.CTkEntry(secret_frame, width=300, show="*")
            self.tumblr_consumer_secret_entry.pack(side="left", expand=True, fill="x")
            self.tumblr_consumer_secret_entry.insert(0, self.api_config_dialog_copy.get("tumblr_consumer_secret", ""))

            ctk.CTkButton(tab, text="Tumblr 앱 등록 및 Key/Secret 발급 방법",
                          command=lambda: webbrowser.open("https://www.tumblr.com/oauth/apps")).pack(pady=(5,10))
            
            self.tumblr_auth_method = tk.StringVar(value="callback") 
            ctk.CTkRadioButton(tab, text="자동 콜백 방식 (권장)", variable=self.tumblr_auth_method, value="callback").pack(anchor="w", padx=20)
            ctk.CTkRadioButton(tab, text="수동 PIN 입력 방식", variable=self.tumblr_auth_method, value="pin").pack(anchor="w", padx=20)

            ctk.CTkButton(tab, text="Tumblr 계정 연결 시작", command=self._connect_tumblr).pack(pady=20)

        def _connect_tumblr(self):
            service_name = "Tumblr"
            consumer_key = self.tumblr_consumer_key_entry.get()
            consumer_secret = self.tumblr_consumer_secret_entry.get()
            if not consumer_key or not consumer_secret:
                messagebox.showerror("입력 오류", "Tumblr Consumer Key와 Secret을 모두 입력하세요.", parent=self)
                return
            self.api_config_dialog_copy["tumblr_consumer_key"] = consumer_key
            self.api_config_dialog_copy["tumblr_consumer_secret"] = consumer_secret

            use_pin = self.tumblr_auth_method.get() == "pin"
            if not use_pin: 
                if not self._start_local_server(OAUTH_CALLBACK_PORT_TUMBLR):
                    return

            tumblr_uploader = TumblrUploader(self.account_manager, self) 
            
            def run_oauth_flow():
                oauth_token, oauth_secret, user_blogs, primary_blog = tumblr_uploader.start_oauth_flow(
                    self.oauth_callback_queue, consumer_key, consumer_secret, use_pin_auth=use_pin
                )

                if not use_pin: 
                    self._stop_local_server()

                if oauth_token and oauth_secret:
                    try:
                        temp_client_for_user_info = pytumblr.TumblrRestClient(consumer_key, consumer_secret, oauth_token, oauth_secret)
                        user_info_check = temp_client_for_user_info.info()
                        tumblr_username = user_info_check['user']['name'] if user_info_check and 'user' in user_info_check else "UnknownTumblrUser"

                        self.account_manager.store_credential("tumblr", tumblr_username, "oauth_token", oauth_token)
                        self.account_manager.store_credential("tumblr", tumblr_username, "oauth_secret", oauth_secret)
                        
                        account_details = {"blogs": user_blogs if user_blogs else []}
                        if primary_blog:
                            account_details["primary_blog_name"] = primary_blog
                        
                        self.account_manager.add_account("tumblr", tumblr_username, account_details)
                        messagebox.showinfo("Tumblr 연결 성공", f"{tumblr_username} 계정이 성공적으로 연결되었습니다.", parent=self)
                        self._update_connected_accounts_list()
                    except Exception as e:
                        messagebox.showerror("Tumblr 정보 오류", f"토큰 저장/사용자 정보 가져오기 실패: {e}", parent=self)
            
            threading.Thread(target=run_oauth_flow, daemon=True).start()


        def _create_twitter_tab(self, tab):
            ctk.CTkLabel(tab, text="Twitter (X) 계정 연결", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            
            ctk.CTkLabel(tab, text="OAuth 2.0 PKCE (사용자 인증용)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(10,0))
            id_frame = ctk.CTkFrame(tab, fg_color="transparent")
            id_frame.pack(pady=5, fill="x", padx=20)
            ctk.CTkLabel(id_frame, text="Client ID (OAuth 2.0):").pack(side="left", padx=(0,5))
            self.twitter_client_id_entry = ctk.CTkEntry(id_frame, width=300)
            self.twitter_client_id_entry.pack(side="left", expand=True, fill="x")
            self.twitter_client_id_entry.insert(0, self.api_config_dialog_copy.get("twitter_client_id", ""))

            client_secret_frame = ctk.CTkFrame(tab, fg_color="transparent") 
            client_secret_frame.pack(pady=5, fill="x", padx=20)
            ctk.CTkLabel(client_secret_frame, text="Client Secret (OAuth 2.0, 선택 사항):").pack(side="left", padx=(0,5))
            self.twitter_client_secret_entry = ctk.CTkEntry(client_secret_frame, width=300, show="*")
            self.twitter_client_secret_entry.pack(side="left", expand=True, fill="x")
            self.twitter_client_secret_entry.insert(0, self.api_config_dialog_copy.get("twitter_client_secret", ""))
            ctk.CTkButton(tab, text="Twitter OAuth 2.0 연결 시작", command=self._connect_twitter_oauth2).pack(pady=(5,10))

            ctk.CTkLabel(tab, text="OAuth 1.0a (미디어 업로드용 앱 인증 정보)", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(20,0))
            
            ctk.CTkLabel(tab, text="API Key (Consumer Key, OAuth 1.0a):").pack(pady=(5,0))
            self.twitter_oauth1_consumer_key_entry = ctk.CTkEntry(tab, width=300)
            self.twitter_oauth1_consumer_key_entry.pack()
            self.twitter_oauth1_consumer_key_entry.insert(0, self.api_config_dialog_copy.get("twitter_oauth1_app_credentials", {}).get("api_key", ""))

            ctk.CTkLabel(tab, text="API Secret (Consumer Secret, OAuth 1.0a):").pack(pady=(5,0))
            self.twitter_oauth1_consumer_secret_entry = ctk.CTkEntry(tab, width=300, show="*")
            self.twitter_oauth1_consumer_secret_entry.pack()
            self.twitter_oauth1_consumer_secret_entry.insert(0, self.api_config_dialog_copy.get("twitter_oauth1_app_credentials", {}).get("api_secret_key", ""))

            ctk.CTkLabel(tab, text="사용자 이름 (OAuth 1.0a 토큰 연결 대상):").pack(pady=(5,0))
            self.twitter_username_for_oauth1_entry = ctk.CTkEntry(tab, width=250, placeholder_text="OAuth 2.0으로 연결된 사용자명")
            self.twitter_username_for_oauth1_entry.pack()
            
            ctk.CTkLabel(tab, text="Access Token (OAuth 1.0a):").pack(pady=(5,0))
            self.twitter_oauth1_access_token_entry = ctk.CTkEntry(tab, width=300, show="*")
            self.twitter_oauth1_access_token_entry.pack()
            
            ctk.CTkLabel(tab, text="Access Token Secret (OAuth 1.0a):").pack(pady=(5,0))
            self.twitter_oauth1_access_token_secret_entry = ctk.CTkEntry(tab, width=300, show="*")
            self.twitter_oauth1_access_token_secret_entry.pack()

            ctk.CTkButton(tab, text="Twitter OAuth 1.0a 정보 저장", command=self._save_twitter_oauth1_details).pack(pady=(10,5))
            ctk.CTkButton(tab, text="Twitter 개발자 포털 (앱 생성 가이드)",
                          command=lambda: webbrowser.open("https://developer.twitter.com/en/portal/projects-and-apps")).pack(pady=(5,10))


        def _connect_twitter_oauth2(self): 
            service_name = "Twitter"
            client_id = self.twitter_client_id_entry.get()
            client_secret = self.twitter_client_secret_entry.get() 
            if not client_id:
                messagebox.showerror("입력 오류", "Twitter Client ID (OAuth 2.0)를 입력하세요.", parent=self)
                return
            self.api_config_dialog_copy["twitter_client_id"] = client_id
            if client_secret: self.api_config_dialog_copy["twitter_client_secret"] = client_secret

            if not self._start_local_server(OAUTH_CALLBACK_PORT_TWITTER):
                return

            twitter_uploader = TwitterUploader(self.account_manager, self)
            
            def run_oauth_flow():
                access_token, refresh_token, twitter_username, user_id_str = twitter_uploader.start_oauth_flow(
                    self.oauth_callback_queue, client_id, client_secret if client_secret else None
                )
                self._stop_local_server() 

                if access_token and twitter_username:
                    self.account_manager.store_credential("twitter", twitter_username, "access_token", access_token) 
                    if refresh_token: 
                        self.account_manager.store_credential("twitter", twitter_username, "refresh_token", refresh_token) 
                    self.account_manager.add_account("twitter", twitter_username, {"user_id": user_id_str, "auth_type": "oauth2_pkce"})
                    messagebox.showinfo("Twitter OAuth 2.0 연결 성공", f"@{twitter_username} 계정이 성공적으로 연결되었습니다 (OAuth 2.0 PKCE). 미디어 업로드를 위해서는 OAuth 1.0a 정보도 입력해주세요.", parent=self)
                    self._update_connected_accounts_list()
                    self.twitter_username_for_oauth1_entry.delete(0, tk.END)
                    self.twitter_username_for_oauth1_entry.insert(0, twitter_username)
            
            threading.Thread(target=run_oauth_flow, daemon=True).start()

        def _save_twitter_oauth1_details(self):
            service_name = "Twitter"
            
            app_api_key = self.twitter_oauth1_consumer_key_entry.get()
            app_api_secret = self.twitter_oauth1_consumer_secret_entry.get()
            
            target_username = self.twitter_username_for_oauth1_entry.get()
            user_access_token = self.twitter_oauth1_access_token_entry.get()
            user_access_token_secret = self.twitter_oauth1_access_token_secret_entry.get()

            if not all([app_api_key, app_api_secret]):
                messagebox.showerror("입력 오류", "Twitter 앱의 API Key와 API Secret (OAuth 1.0a)을 모두 입력하세요.", parent=self)
                return

            self.api_config_dialog_copy.setdefault("twitter_oauth1_app_credentials", {})
            self.api_config_dialog_copy["twitter_oauth1_app_credentials"]["api_key"] = app_api_key
            self.api_config_dialog_copy["twitter_oauth1_app_credentials"]["api_secret_key"] = app_api_secret
            
            if target_username and user_access_token and user_access_token_secret:
                self.account_manager.store_credential("twitter", target_username, "oauth1_access_token", user_access_token)
                self.account_manager.store_credential("twitter", target_username, "oauth1_access_token_secret", user_access_token_secret)
                
                self.api_config_dialog_copy.setdefault("twitter_user_oauth1_tokens", {}).setdefault(target_username, {})
                self.api_config_dialog_copy["twitter_user_oauth1_tokens"][target_username]["has_oauth1_tokens"] = True 

                messagebox.showinfo("Twitter OAuth 1.0a 저장", f"앱의 Consumer Key/Secret 및 '{target_username}' 사용자의 Access Token/Secret (OAuth 1.0a) 정보가 저장(예정)되었습니다.\n실제 저장은 이 대화창을 닫을 때 이루어집니다.", parent=self)
            else:
                messagebox.showinfo("Twitter OAuth 1.0a 앱 정보 저장", "앱의 Consumer Key/Secret (OAuth 1.0a) 정보가 저장(예정)되었습니다.\n사용자별 Access Token/Secret도 입력해야 미디어 업로드가 가능합니다.", parent=self)
            
        def _create_pixiv_tab(self, tab): # Selenium 방식으로 UI 수정
            ctk.CTkLabel(tab, text="Pixiv 계정 연결 (브라우저 로그인 방식)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

            ctk.CTkLabel(tab, text="Pixiv 계정 이름 (프로그램 내 식별용):").pack(pady=(10,0))
            self.pixiv_profile_name_entry = ctk.CTkEntry(tab, width=300, placeholder_text="예: MyPixivAccount1")
            self.pixiv_profile_name_entry.pack()
            
            ctk.CTkButton(tab, text="Pixiv 로그인 (브라우저 열기)", command=self._connect_pixiv_browser_login).pack(pady=(10,5))
            ctk.CTkLabel(tab, text="버튼 클릭 시 브라우저가 열립니다.\n브라우저에서 Pixiv 로그인을 완료한 후 안내에 따라 진행하세요.").pack(pady=(0,10))
            
            ctk.CTkButton(tab, text="Pixiv 연결 도움말 (WebDriver 설정)",
                          command=lambda: self.master_app.show_pixiv_selenium_help_dialog()).pack(pady=10)

        def _connect_pixiv_browser_login(self): # Selenium 로그인 호출
            profile_name = self.pixiv_profile_name_entry.get()
            if not profile_name:
                messagebox.showerror("입력 오류", "Pixiv 계정을 식별할 프로필 이름을 입력해주세요.", parent=self)
                return

            # App 클래스의 pixiv_uploader 인스턴스 사용
            pixiv_uploader_instance = self.master_app.pixiv_uploader 

            def login_thread_task():
                self.master_app.log_message(f"Pixiv 브라우저 로그인 시작 (프로필: {profile_name})...")
                success, message = pixiv_uploader_instance.login_with_browser(profile_name)
                
                def update_ui_after_login():
                    if success:
                        messagebox.showinfo("Pixiv 로그인 성공", message, parent=self) 
                        self._update_connected_accounts_list() 
                    else:
                        messagebox.showerror("Pixiv 로그인 실패", message, parent=self)
                    self.master_app.log_message(f"Pixiv 브라우저 로그인 시도 완료: {message}")

                self.master_app.after(0, update_ui_after_login) 
            
            threading.Thread(target=login_thread_task, daemon=True).start()


        def _create_furaffinity_tab(self, tab):
            # ... (기존과 동일) ...
            ctk.CTkLabel(tab, text="Fur Affinity 계정 연결", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            ctk.CTkLabel(tab, text="Fur Affinity 사용자 이름 (계정 식별용):").pack(pady=(5,0))
            self.furaffinity_username_entry = ctk.CTkEntry(tab, width=250)
            self.furaffinity_username_entry.pack()
            ctk.CTkLabel(tab, text="Fur Affinity 인증 정보 (예: 쿠키 a;b):").pack(pady=(10,0))
            self.furaffinity_api_key_entry = ctk.CTkEntry(tab, width=350, show="*", placeholder_text="예: cookie_a_value;cookie_b_value")
            self.furaffinity_api_key_entry.pack()
            def _load_fa_auth_on_user_change(event=None):
                user = self.furaffinity_username_entry.get()
                if user:
                    auth_map = self.api_config_dialog_copy.get("furaffinity_auth_info", {})
                    self.furaffinity_api_key_entry.delete(0, tk.END)
                    self.furaffinity_api_key_entry.insert(0, auth_map.get(user, ""))
            self.furaffinity_username_entry.bind("<FocusOut>", _load_fa_auth_on_user_change)
            self.furaffinity_username_entry.bind("<Return>", _load_fa_auth_on_user_change)

            ctk.CTkButton(tab, text="Fur Affinity 인증 정보 안내 (준비 중)",
                          command=lambda: messagebox.showinfo("안내", "Fur Affinity 연동 방식은 현재 조사 중입니다. (예: API 키 또는 쿠키 정보)", parent=self)).pack(pady=5)
            ctk.CTkButton(tab, text="Fur Affinity 계정 저장", command=self._connect_furaffinity).pack(pady=10)

        def _connect_furaffinity(self):
            # ... (기존과 동일) ...
            fa_user = self.furaffinity_username_entry.get()
            fa_auth_info = self.furaffinity_api_key_entry.get()
            if not fa_user or not fa_auth_info:
                messagebox.showerror("입력 오류", "Fur Affinity 사용자 이름과 인증 정보를 모두 입력하세요.", parent=self)
                return

            if "furaffinity_auth_info" not in self.api_config_dialog_copy:
                self.api_config_dialog_copy["furaffinity_auth_info"] = {}
            self.api_config_dialog_copy["furaffinity_auth_info"][fa_user] = fa_auth_info

            if self.account_manager.add_account("furaffinity", fa_user): 
                messagebox.showinfo("Fur Affinity 연결", f"{fa_user} 계정 정보가 추가되었습니다. 인증 정보는 대화창 닫을 때 설정 파일에 저장됩니다.", parent=self)
                self._update_connected_accounts_list()
            else:
                messagebox.showwarning("Fur Affinity 연결", f"{fa_user} 계정은 이미 추가되어 있습니다 (인증 정보는 업데이트 예정).", parent=self)

        def _create_inkbunny_tab(self, tab):
            # ... (기존과 동일) ...
            ctk.CTkLabel(tab, text="Inkbunny 계정 연결 (사용자명/비밀번호)", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            
            ctk.CTkLabel(tab, text="Inkbunny 사용자 이름:").pack(pady=(5,0))
            self.inkbunny_username_entry = ctk.CTkEntry(tab, width=250)
            self.inkbunny_username_entry.pack()
            
            ctk.CTkLabel(tab, text="Inkbunny 비밀번호:").pack(pady=(10,0))
            self.inkbunny_password_entry = ctk.CTkEntry(tab, width=250, show="*")
            self.inkbunny_password_entry.pack()
            
            ctk.CTkButton(tab, text="Inkbunny 계정 저장/확인", command=self._connect_inkbunny_credentials).pack(pady=20)
            ctk.CTkLabel(tab, text="비밀번호는 안전하게 Keyring에 저장됩니다.").pack(pady=(0,10))


        def _connect_inkbunny_credentials(self):
            # ... (기존과 동일) ...
            service_name = InkbunnyUploader.SERVICE_NAME
            username = self.inkbunny_username_entry.get()
            password = self.inkbunny_password_entry.get()

            if not username or not password:
                messagebox.showerror("입력 오류", "Inkbunny 사용자 이름과 비밀번호를 모두 입력하세요.", parent=self)
                return
            
            temp_ib_uploader = InkbunnyUploader(self.account_manager, self) 

            def verify_login_task():
                sid, user_id, error_msg = temp_ib_uploader._ib_login(username, password) 
                
                if error_msg is None and sid: 
                    self.account_manager.store_credential(service_name, username, "password", password)
                    
                    if self.account_manager.add_account(service_name, username, {"user_id_ib": user_id}):
                        self.after(0, lambda: messagebox.showinfo("Inkbunny 연결 성공", f"{username} 계정이 성공적으로 연결 및 확인되었습니다.\n비밀번호는 Keyring에 저장됩니다.", parent=self))
                        self.after(0, self._update_connected_accounts_list) 
                    else: 
                        self.after(0, lambda: messagebox.showinfo("Inkbunny 정보 업데이트", f"{username} 계정의 비밀번호가 업데이트되었습니다 (Keyring에 저장).", parent=self))
                    
                    self.after(0, lambda: self.inkbunny_password_entry.delete(0, tk.END))
                else: 
                    self.after(0, lambda: messagebox.showerror("Inkbunny 연결 실패", f"로그인 실패: {error_msg}\n사용자 이름과 비밀번호를 확인하세요.", parent=self))
            
            threading.Thread(target=verify_login_task, daemon=True).start()


        def _create_connected_accounts_frame(self):
            # ... (기존과 동일) ...
            self.connected_frame = ctk.CTkFrame(self) 
            self.connected_frame.pack(padx=10, pady=(0,10), fill="x", side="bottom") 
            ctk.CTkLabel(self.connected_frame, text="연결된 계정 목록", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
            self.accounts_listbox = tk.Listbox(self.connected_frame, height=5, width=60, relief="sunken", borderwidth=1)
            self.accounts_listbox.pack(pady=5, padx=10, fill="x")
            remove_button = ctk.CTkButton(self.connected_frame, text="선택한 계정 연결 해제", command=self._remove_selected_account)
            remove_button.pack(pady=5)
            self._update_connected_accounts_list() 

        def _update_connected_accounts_list(self):
            # ... (기존과 동일) ...
            self.accounts_listbox.delete(0, tk.END)
            connected_accounts = self.account_manager.get_connected_accounts() 
            for service, acc_list in connected_accounts.items():
                for acc_info in acc_list:
                    username = acc_info.get("username", "알 수 없음")
                    self.accounts_listbox.insert(tk.END, f"{service.capitalize()}: {username}")

        def _remove_selected_account(self):
            # ... (기존과 동일, Pixiv 관련 API_Config.json 수정 로직은 불필요해짐) ...
            selected_index = self.accounts_listbox.curselection()
            if not selected_index:
                messagebox.showwarning("선택 오류", "삭제할 계정을 목록에서 선택하세요.", parent=self)
                return
            selected_item_text = self.accounts_listbox.get(selected_index[0])
            try:
                service_name_display, username = selected_item_text.split(": ", 1)
                service_name_internal = service_name_display.lower() 
            except ValueError:
                messagebox.showerror("오류", "선택된 항목의 형식이 잘못되었습니다.", parent=self)
                return
            
            confirm_msg = f"'{username}' ({service_name_display}) 계정 연결을 해제하시겠습니까?"
            if service_name_internal in ["tumblr", "twitter", "inkbunny"]: 
                confirm_msg += "\n저장된 관련 인증 정보(토큰/비밀번호)도 Keyring에서 삭제됩니다."
            elif service_name_internal == "pixiv":
                confirm_msg += "\n프로그램 내 계정 목록에서 제거됩니다.\n(저장된 Selenium 프로필은 수동으로 삭제해야 할 수 있습니다: {프로그램_폴더}/selenium_profiles/{계정_이름})"
            else: 
                 confirm_msg += "\n저장된 관련 API 키 정보도 설정 파일에서 삭제됩니다."


            if messagebox.askyesno("계정 삭제 확인", confirm_msg, parent=self):
                self.account_manager.remove_account(service_name_internal, username) 
                
                if service_name_internal == "e621":
                    if "e621_api_keys" in self.api_config_dialog_copy and username in self.api_config_dialog_copy["e621_api_keys"]:
                        del self.api_config_dialog_copy["e621_api_keys"][username]
                
                self._update_connected_accounts_list() 
                if hasattr(self.master_app, 'update_account_option_menus'): 
                    self.master_app.update_account_option_menus()
                messagebox.showinfo("계정 삭제", f"'{username}' 계정 연결이 해제되었습니다.", parent=self)


    # --- 예약 포스팅 대화창 ---
    # ... (SchedulePostDialog 클래스는 기존과 동일하게 유지) ...
    class SchedulePostDialog(ctk.CTkToplevel):
        def __init__(self, master, callback):
            super().__init__(master)
            self.callback = callback 
            self.transient(master) 
            self.grab_set() 
            self.title("포스팅 예약")
            self.geometry("400x300") 

            main_frame = ctk.CTkFrame(self)
            main_frame.pack(expand=True, fill="both", padx=20, pady=20)

            ctk.CTkLabel(main_frame, text="예약 날짜:").pack(pady=(0,2))
            self.date_entry = DateEntry(main_frame, width=18, background='gray',
                                         foreground='white', borderwidth=2, 
                                         date_pattern='yyyy-mm-dd', 
                                         year=datetime.now().year, 
                                         month=datetime.now().month, 
                                         day=datetime.now().day)
            self.date_entry.pack(pady=(0,10), fill="x")


            ctk.CTkLabel(main_frame, text="예약 시간 (HH:MM):").pack(pady=(0,2))
            default_time = (datetime.now() + timedelta(minutes=5)).strftime('%H:%M')
            self.time_entry = ctk.CTkEntry(main_frame, placeholder_text=default_time)
            self.time_entry.pack(pady=(0,20), fill="x")

            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(10,0))

            confirm_button = ctk.CTkButton(button_frame, text="예약 설정", command=self._on_confirm)
            confirm_button.pack(side="left", padx=(0,10), expand=True)
            cancel_button = ctk.CTkButton(button_frame, text="취소", command=self.destroy, fg_color="gray")
            cancel_button.pack(side="right", expand=True)

        def _on_confirm(self):
            try:
                selected_date_obj = self.date_entry.get_date() 
                date_str = selected_date_obj.strftime('%Y-%m-%d')
            except Exception as e:
                messagebox.showerror("입력 오류", f"유효한 날짜를 선택해주세요: {e}", parent=self)
                return

            time_str = self.time_entry.get()
            if not time_str: time_str = self.time_entry.cget("placeholder_text")

            try:
                scheduled_dt_str = f"{date_str} {time_str}"
                scheduled_dt = datetime.strptime(scheduled_dt_str, "%Y-%m-%d %H:%M")

                if scheduled_dt <= datetime.now():
                    messagebox.showerror("입력 오류", "예약 시간은 현재 시간보다 이후여야 합니다.", parent=self)
                    return
                
                self.callback(scheduled_dt) 
                self.destroy()

            except ValueError:
                messagebox.showerror("입력 오류", "시간 형식이 잘못되었습니다. (HH:MM)", parent=self)


    # --- 메인 애플리케이션 클래스 ---
    class App(ctk.CTk):
        PREVIEW_MAX_FRAME_HEIGHT = 600 
        PREVIEW_MIN_FRAME_HEIGHT_WITH_IMAGE = 120 
        DEFAULT_PREVIEW_FRAME_HEIGHT = 100 
        PREVIEW_FRAME_PADDING = 10

        NAV_FRAME_EXPANDED_WIDTH = 380 
        NAV_FRAME_COLLAPSED_WIDTH = 60 

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            print("DEBUG: App.__init__ started.")
            self.title("이미지 동시 포스팅 프로그램 (최종)")
            self.geometry("1100x750")

            self.api_config = load_api_config()
            self.post_preset_config = load_post_preset_config()
            self.scheduled_posts_data = self._load_scheduled_posts() 
            self.tag_presets = load_tag_presets() # 태그 프리셋 로드

            ctk.set_appearance_mode(self.post_preset_config.get("appearance_mode", "System"))
            ctk.set_default_color_theme(self.post_preset_config.get("color_theme", "blue"))

            self.scheduler = BackgroundScheduler(timezone="Asia/Seoul") 
            try:
                self.scheduler.start()
                self.log_message("예약 스케줄러가 시작되었습니다.")
            except Exception as e:
                self.log_message(f"스케줄러 시작 중 오류 발생: {e}")
                messagebox.showerror("스케줄러 오류", f"예약 스케줄러 시작에 실패했습니다: {e}\n예약 기능이 정상 동작하지 않을 수 있습니다.", parent=self)


            self.account_manager = AccountManager(APP_NAME_FOR_KEYRING)
            self.e621_uploader = E621Uploader(self.account_manager)
            self.tumblr_uploader = TumblrUploader(self.account_manager, self)
            self.twitter_uploader = TwitterUploader(self.account_manager, self)
            self.pixiv_uploader = PixivUploader(self.account_manager, self) 
            self.furaffinity_uploader = FurAffinityUploader(self.account_manager, self)
            self.inkbunny_uploader = InkbunnyUploader(self.account_manager, self)

            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(0, weight=1) 
            self.grid_rowconfigure(1, weight=0) # 로그 영역은 고정 높이

            self.navigation_frame_expanded = True 
            self.navigation_frame = ctk.CTkFrame(self, corner_radius=0, width=self.NAV_FRAME_EXPANDED_WIDTH)
            self.navigation_frame.grid(row=0, column=0, rowspan=2, sticky="nsw") 
            self.navigation_frame.grid_propagate(False) 

            self.nav_top_bar = ctk.CTkFrame(self.navigation_frame, fg_color="transparent", height=40)
            self.nav_top_bar.pack(side="top", fill="x", padx=5, pady=5)

            self.nav_toggle_button = ctk.CTkButton(self.nav_top_bar, text="⚙", width=30, command=self.toggle_navigation_frame)
            self.nav_toggle_button.pack(side="left", padx=(5,0))
            
            self.nav_title_label = ctk.CTkLabel(self.nav_top_bar, text=" 포스팅 설정", font=ctk.CTkFont(size=16, weight="bold"))
            self.nav_title_label.pack(side="left", padx=5)


            self.nav_bottom_controls_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
            self.nav_bottom_controls_frame.pack(side="bottom", fill="x", padx=10, pady=(10, 20))

            self.help_button = ctk.CTkButton(self.nav_bottom_controls_frame, text="도움말 / 튜토리얼", command=self.show_help)
            self.help_button.pack(pady=(0,10), fill="x")

            self.appearance_mode_label = ctk.CTkLabel(self.nav_bottom_controls_frame, text="UI 테마:")
            self.appearance_mode_label.pack(anchor="w", pady=(5,0))
            self.appearance_mode_menu = ctk.CTkOptionMenu(self.nav_bottom_controls_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode)
            self.appearance_mode_menu.pack(fill="x")
            self.appearance_mode_menu.set(self.post_preset_config.get("appearance_mode", "System"))

            self.color_theme_label = ctk.CTkLabel(self.nav_bottom_controls_frame, text="UI 색상:")
            self.color_theme_label.pack(anchor="w", pady=(5,0))
            self.color_theme_menu = ctk.CTkOptionMenu(self.nav_bottom_controls_frame, values=["blue", "green", "dark-blue"], command=self.change_color_theme)
            self.color_theme_menu.pack(fill="x")
            self.color_theme_menu.set(self.post_preset_config.get("color_theme", "blue"))

            self.nav_content_frame = ctk.CTkScrollableFrame(self.navigation_frame, fg_color="transparent")
            self.nav_content_frame.pack(pady=(0,0), padx=10, fill="both", expand=True) 

            self.api_accounts_button = ctk.CTkButton(self.nav_content_frame, text="사이트 계정 / API 설정", command=self.open_api_connection_dialog)
            self.api_accounts_button.pack(pady=10, fill="x", padx=10)

            self.sites_label = ctk.CTkLabel(self.nav_content_frame, text="업로드할 사이트:", font=ctk.CTkFont(size=12))
            self.sites_label.pack(pady=(10,5), anchor="w", padx=10)

            self.site_vars = {}
            self.site_checkboxes = {}
            self.site_account_menus = {}
            self.site_account_vars = {}
            self.site_frames = {}
            self.tumblr_blog_vars = {} 
            self.tumblr_blog_menus = {} 

            self.supported_sites = ["e621", "twitter", "tumblr", "pixiv", "furaffinity", "inkbunny"]

            for site in self.supported_sites:
                site_ui_frame = ctk.CTkFrame(self.nav_content_frame, border_width=1, border_color="gray50")
                site_ui_frame.pack(fill="x", pady=3, padx=5) 
                self.site_frames[site] = site_ui_frame
                
                checkbox_var = tk.BooleanVar()
                self.site_vars[site] = checkbox_var
                command_func = None
                if site == "tumblr":
                    command_func = lambda s=site: self._toggle_tumblr_blog_menu_state(s)
                
                cb = ctk.CTkCheckBox(site_ui_frame, text=site.capitalize(), variable=checkbox_var, onvalue=True, offvalue=False, command=command_func)
                cb.pack(side="left", padx=(10,5), pady=5) 
                self.site_checkboxes[site] = cb
                
                dropdowns_container_frame = ctk.CTkFrame(site_ui_frame, fg_color="transparent")
                dropdowns_container_frame.pack(side="left", padx=(0, 10), pady=2, fill="x", expand=True) 

                account_var = tk.StringVar(value="선택 안함")
                self.site_account_vars[site] = account_var
                
                if site == "tumblr":
                    account_var.trace_add("write", lambda name, index, mode, s=site: self._on_tumblr_account_selected_wrapper(s))
                    account_menu = ctk.CTkOptionMenu(dropdowns_container_frame, variable=account_var, values=["선택 안함"], state="disabled")
                    account_menu.pack(side="top", fill="x", expand=True, pady=(0, 2)) 
                    self.site_account_menus[site] = account_menu

                    blog_var = tk.StringVar(value="블로그 선택")
                    self.tumblr_blog_vars[site] = blog_var
                    blog_menu = ctk.CTkOptionMenu(dropdowns_container_frame, variable=blog_var, values=["블로그 선택"], state="disabled") 
                    blog_menu.pack(side="top", fill="x", expand=True, pady=(2, 0)) 
                    self.tumblr_blog_menus[site] = blog_menu
                else:
                    account_menu = ctk.CTkOptionMenu(dropdowns_container_frame, variable=account_var, values=["선택 안함"], state="disabled")
                    account_menu.pack(side="top", fill="x", expand=True, pady=0) 
                    self.site_account_menus[site] = account_menu


            self.update_account_option_menus() 
            if "tumblr" in self.supported_sites and self.site_account_vars["tumblr"].get() != "선택 안함":
                self._load_tumblr_blogs_for_account(self.site_account_vars["tumblr"].get())
            self._toggle_tumblr_blog_menu_state("tumblr") 


            saved_selected_accounts_ui = self.post_preset_config.get("selected_accounts_ui", {})
            for site_name, selected_val_or_info in saved_selected_accounts_ui.items():
                if site_name in self.site_account_vars:
                    account_to_select = selected_val_or_info if isinstance(selected_val_or_info, str) else selected_val_or_info.get("account")
                    current_options = self.site_account_menus[site_name].cget("values")
                    if account_to_select and account_to_select in current_options:
                        self.site_account_vars[site_name].set(account_to_select)
                    elif current_options: 
                        self.site_account_vars[site_name].set(current_options[0])
                
                if site_name == "tumblr" and isinstance(selected_val_or_info, dict) and "selected_blog" in selected_val_or_info:
                    saved_blog = selected_val_or_info["selected_blog"]
                    self.after(100, lambda s=site_name, b=saved_blog: self._try_set_tumblr_blog(s,b))


            self.select_all_sites_var = tk.BooleanVar()
            self.select_all_sites_checkbox = ctk.CTkCheckBox(self.nav_content_frame, text="모든 사이트 선택/해제", variable=self.select_all_sites_var, command=self.toggle_all_sites)
            self.select_all_sites_checkbox.pack(pady=10, anchor="w", padx=10)

            # --- 우측 메인 프레임 ---
            self.main_content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
            self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
            self.main_content_frame.grid_rowconfigure(0, weight=1) 
            self.main_content_frame.grid_columnconfigure(0, weight=0) # Label column
            self.main_content_frame.grid_columnconfigure(1, weight=1) # Entry/Textbox column
            self.main_content_frame.grid_columnconfigure(2, weight=0) # Button column (for image select)

            self.preview_frame = ctk.CTkFrame(self.main_content_frame, border_width=1) 
            self.preview_frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
            self.preview_frame.grid_propagate(False) 
            self.preview_label = ctk.CTkLabel(self.preview_frame, text="선택된 이미지 미리 보기", text_color="gray")
            self.preview_label.pack(expand=True, fill="both")
            self.loaded_image_tk = None
            self.original_image_for_preview = None
            self._preview_configure_scheduled = False 
            self._last_rendered_preview_height = 0 
            self.preview_frame.bind("<Configure>", self._on_preview_frame_configure)

            # 입력 필드들
            fields_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
            fields_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
            fields_frame.grid_columnconfigure(1, weight=1) # 입력 필드가 확장되도록

            self.entries = {}
            self.image_path_var = tk.StringVar()

            field_definitions = [
                ("이미지 파일:", "image_path_var", "select_image_file_button"),
                ("제목:", "title_entry", None),
                ("내용 / 설명:", "description_text", None),
                ("태그 (쉼표/공백 구분):", "tags_entry", None),
                # 태그 프리셋 UI가 이 아래에 추가될 것임
                ("등급 (s,q,e):", "rating_entry", None),
                ("출처 URL:", "source_url_entry", None)
            ]
            
            current_row_for_fields = 0
            for label_text, var_name, button_info in field_definitions:
                fields_frame.grid_rowconfigure(current_row_for_fields, weight=0)
                ctk.CTkLabel(fields_frame, text=label_text).grid(row=current_row_for_fields, column=0, sticky="w", padx=5, pady=5)
                
                if var_name == "image_path_var":
                    self.entries[var_name] = ctk.CTkEntry(fields_frame, textvariable=self.image_path_var, state="readonly")
                    self.entries[var_name].grid(row=current_row_for_fields, column=1, sticky="ew", padx=5, pady=5)
                    ctk.CTkButton(fields_frame, text="이미지 선택", command=self.select_image_file).grid(row=current_row_for_fields, column=2, padx=5, pady=5)
                elif var_name == "description_text":
                    self.entries[var_name] = ctk.CTkTextbox(fields_frame, height=100)
                    self.entries[var_name].grid(row=current_row_for_fields, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
                elif var_name == "rating_entry":
                     self.entries[var_name] = ctk.CTkEntry(fields_frame, width=50) 
                     self.entries[var_name].grid(row=current_row_for_fields, column=1, sticky="w", padx=5, pady=5) 
                     self.entries[var_name].insert(0, "s") 
                else:
                    self.entries[var_name] = ctk.CTkEntry(fields_frame)
                    self.entries[var_name].grid(row=current_row_for_fields, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
                
                current_row_for_fields += 1

                # 태그 입력칸 바로 아래에 태그 프리셋 UI 추가
                if var_name == "tags_entry":
                    tag_preset_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
                    tag_preset_frame.grid(row=current_row_for_fields, column=1, columnspan=2, sticky="ew", padx=5, pady=(0,5))
                    tag_preset_frame.grid_columnconfigure(0, weight=1) # 이름 입력 필드
                    tag_preset_frame.grid_columnconfigure(1, weight=0) # 저장 버튼
                    tag_preset_frame.grid_columnconfigure(2, weight=1) # 드롭다운

                    self.tag_preset_name_entry = ctk.CTkEntry(tag_preset_frame, placeholder_text="저장할 태그 이름")
                    self.tag_preset_name_entry.grid(row=0, column=0, padx=(0,5), sticky="ew")
                    
                    self.save_tag_preset_button = ctk.CTkButton(tag_preset_frame, text="현재 태그 저장", command=self._save_tag_preset)
                    self.save_tag_preset_button.grid(row=0, column=1, padx=5)

                    self.tag_preset_var = tk.StringVar(value="태그 프리셋 선택")
                    self.tag_preset_menu = ctk.CTkOptionMenu(tag_preset_frame, variable=self.tag_preset_var, 
                                                             values=["태그 프리셋 선택"], command=self._apply_tag_preset)
                    self.tag_preset_menu.grid(row=0, column=2, padx=(5,0), sticky="ew")
                    current_row_for_fields +=1 # 태그 프리셋 UI 행 추가

            self._load_tag_presets_to_ui() # 태그 프리셋 로드 및 UI 업데이트
            self._load_posting_inputs() 

            # 버튼 프레임
            button_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
            button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew") # row 인덱스 수정
            button_frame.grid_columnconfigure((0,1,2), weight=1) # 버튼들이 공간을 균등하게 차지하도록

            ctk.CTkButton(button_frame, text="즉시 포스팅", command=self.start_upload_process).grid(row=0, column=0, padx=5, sticky="ew")
            ctk.CTkButton(button_frame, text="예약 포스팅", command=self.open_schedule_post_dialog).grid(row=0, column=1, padx=5, sticky="ew")
            self.save_inputs_button = ctk.CTkButton(button_frame, text="입력 값 저장", command=lambda: self._save_posting_inputs(save_to_file=True)) 
            self.save_inputs_button.grid(row=0, column=2, padx=5, sticky="ew")

            # 로그 텍스트 박스
            self.log_textbox = ctk.CTkTextbox(self, height=120) # 높이 약간 증가
            self.log_textbox.grid(row=1, column=1, sticky="nsew", padx=10, pady=(5,10))
            self.log_textbox.configure(state="disabled")
            # URL 클릭을 위한 태그 설정
            self.log_textbox.tag_config("hyperlink", foreground="blue", underline=True)
            self.log_textbox.tag_bind("hyperlink", "<Enter>", lambda e: self.log_textbox.configure(cursor="hand2"))
            self.log_textbox.tag_bind("hyperlink", "<Leave>", lambda e: self.log_textbox.configure(cursor=""))
            self.log_textbox.tag_bind("hyperlink", "<Button-1>", self._make_log_clickable)


            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            self._process_startup_scheduled_jobs()
            SELENIUM_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            print("DEBUG: App.__init__ finished.") 

        def _make_log_clickable(self, event):
            """로그 텍스트 박스에서 클릭된 URL을 웹 브라우저로 엽니다."""
            try:
                index = self.log_textbox.index(f"@{event.x},{event.y}")
                tag_ranges = self.log_textbox.tag_ranges("hyperlink")
                for i in range(0, len(tag_ranges), 2):
                    start, end = tag_ranges[i], tag_ranges[i+1]
                    if self.log_textbox.compare(start, "<=", index) and self.log_textbox.compare(index, "<", end):
                        url = self.log_textbox.get(start, end)
                        # URL 유효성 검사 (간단하게 http로 시작하는지 확인)
                        if url.startswith("http://") or url.startswith("https://"):
                            print(f"Opening URL from log: {url}")
                            webbrowser.open(url)
                        return
            except Exception as e:
                print(f"Error opening URL from log: {e}")

        def _load_tag_presets_to_ui(self):
            """JSON 파일에서 태그 프리셋을 로드하여 드롭다운 메뉴에 채웁니다."""
            self.tag_presets = load_tag_presets()
            preset_names = ["태그 프리셋 선택"] + list(self.tag_presets.keys())
            self.tag_preset_menu.configure(values=preset_names)
            if preset_names:
                self.tag_preset_var.set(preset_names[0])

        def _save_tag_preset(self):
            """현재 태그 입력칸의 태그들과 지정된 이름으로 프리셋을 저장합니다."""
            preset_name = self.tag_preset_name_entry.get()
            current_tags_str = self.entries["tags_entry"].get()

            if not preset_name:
                messagebox.showwarning("저장 오류", "저장할 태그 프리셋의 이름을 입력해주세요.", parent=self)
                return
            if not current_tags_str.strip():
                messagebox.showwarning("저장 오류", "저장할 태그가 없습니다. 태그를 입력해주세요.", parent=self)
                return
            
            # 쉼표 또는 공백으로 구분된 태그를 리스트로 변환 (중복 제거 및 공백 제거)
            if ',' in current_tags_str:
                tags_list = list(dict.fromkeys([tag.strip() for tag in current_tags_str.split(',') if tag.strip()]))
            else:
                tags_list = list(dict.fromkeys([tag.strip() for tag in current_tags_str.split(' ') if tag.strip()]))

            if preset_name in self.tag_presets:
                if not messagebox.askyesno("덮어쓰기 확인", f"'{preset_name}' 프리셋이 이미 존재합니다. 덮어쓰시겠습니까?", parent=self):
                    return
            
            self.tag_presets[preset_name] = tags_list
            if save_tag_presets(self.tag_presets):
                messagebox.showinfo("저장 완료", f"태그 프리셋 '{preset_name}'이(가) 저장되었습니다.", parent=self)
                self._load_tag_presets_to_ui() # 드롭다운 업데이트
                self.tag_preset_name_entry.delete(0, tk.END) # 이름 입력칸 비우기
            else:
                messagebox.showerror("저장 실패", "태그 프리셋 저장에 실패했습니다.", parent=self)

        def _apply_tag_preset(self, preset_name_to_apply):
            """선택된 태그 프리셋의 태그들을 현재 태그 입력칸에 추가합니다."""
            if preset_name_to_apply == "태그 프리셋 선택":
                return

            tags_to_apply = self.tag_presets.get(preset_name_to_apply)
            if not tags_to_apply:
                messagebox.showerror("오류", f"'{preset_name_to_apply}' 프리셋을 찾을 수 없습니다.", parent=self)
                return

            current_tags_in_entry = self.entries["tags_entry"].get().strip()
            
            # 기존 태그를 리스트로 변환 (쉼표 또는 공백 기준, 중복 제거)
            existing_tags_list = []
            if current_tags_in_entry:
                if ',' in current_tags_in_entry:
                    existing_tags_list = [tag.strip() for tag in current_tags_in_entry.split(',') if tag.strip()]
                else:
                    existing_tags_list = [tag.strip() for tag in current_tags_in_entry.split(' ') if tag.strip()]
            
            # 추가할 태그 중 이미 있는 태그는 제외
            new_tags_to_add = [tag for tag in tags_to_apply if tag not in existing_tags_list]
            
            if not new_tags_to_add:
                messagebox.showinfo("정보", "선택한 프리셋의 모든 태그가 이미 입력되어 있습니다.", parent=self)
                return

            # 기존 태그 문자열 끝에 공백 추가 (만약 내용이 있다면)
            separator = ""
            if current_tags_in_entry:
                if ',' in current_tags_in_entry: # 기존 태그가 쉼표 구분이면 쉼표로 추가
                    separator = ", "
                else: # 기존 태그가 공백 구분이면 공백으로 추가
                     separator = " "
            
            # 추가할 태그들을 문자열로 변환 (쉼표 또는 공백 기준 - 기존 형식 따름)
            if ',' in current_tags_in_entry or (not current_tags_in_entry and ',' in " ".join(new_tags_to_add)) : # 기존이 쉼표거나, 기존은 없는데 새 태그에 쉼표가 있다면
                 additional_tags_str = ", ".join(new_tags_to_add)
            else:
                 additional_tags_str = " ".join(new_tags_to_add)


            updated_tags_str = current_tags_in_entry + separator + additional_tags_str
            
            self.entries["tags_entry"].delete(0, tk.END)
            self.entries["tags_entry"].insert(0, updated_tags_str.strip().replace("  ", " ")) # 중복 공백 제거
            self.tag_preset_var.set("태그 프리셋 선택") # 드롭다운 초기화


        def show_pixiv_selenium_help_dialog(self):
            # ... (기존과 동일) ...
            help_title = "Pixiv 연결 도움말 (Selenium WebDriver)"
            help_text = """이 프로그램에서 Pixiv에 작품을 업로드하려면 Selenium과 웹 브라우저 드라이버(예: ChromeDriver)가 필요합니다.

**필수 조건:**
1.  **Google Chrome 브라우저 설치:** 최신 버전의 Chrome 브라우저가 설치되어 있어야 합니다.
2.  **ChromeDriver 다운로드 및 설정:**
    * 현재 사용 중인 Chrome 브라우저 버전에 맞는 ChromeDriver를 다운로드해야 합니다.
    * Chrome 버전 확인: Chrome 주소창에 `chrome://version` 입력
    * ChromeDriver 다운로드: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) 또는 [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/) (최신 버전)
    * 다운로드한 ChromeDriver 실행 파일(`chromedriver.exe` 등)을 시스템 PATH에 등록된 디렉터리(예: `C:\Windows\System32`)에 복사하거나, 이 프로그램이 있는 폴더 내에 두거나, 별도 경로에 두고 프로그램 설정에서 해당 경로를 지정해야 합니다. (현재는 PATH에 있거나 프로그램 폴더 내에 있는 것으로 가정)

**연결 방법:**
1.  'API 계정 연결 관리' 창의 'Pixiv' 탭으로 이동합니다.
2.  **'Pixiv 계정 이름 (프로그램 내 식별용)'** 필드에 이 프로그램에서 사용할 Pixiv 계정의 별명을 입력합니다. (예: `MyPixivAccount`)
3.  **'Pixiv 로그인 (브라우저 열기)'** 버튼을 클릭합니다.
4.  새로운 Chrome 브라우저 창이 나타나면서 Pixiv 로그인 페이지가 열립니다.
5.  해당 브라우저 창에서 **직접 Pixiv 계정으로 로그인**합니다. 2단계 인증(2FA)이 설정되어 있다면 해당 절차도 완료합니다.
6.  로그인이 성공적으로 완료되고 **Pixiv 메인 페이지 또는 사용자 대시보드가 완전히 로드된 것을 확인한 후**, 프로그램에 나타난 안내 메시지 창에서 '확인' 버튼을 클릭합니다.
7.  이후 프로그램은 해당 로그인 세션(쿠키)을 사용하여 Pixiv에 작품을 업로드합니다.

**문제 해결 / 주의사항:**
* "WebDriver 오류" 메시지가 나타나면 ChromeDriver가 올바르게 설치되지 않았거나 PATH 설정이 잘못된 것입니다.
* 로그인이 반복적으로 실패하면 Pixiv 웹사이트의 변경 또는 Selenium 프로필 문제일 수 있습니다. 프로그램 폴더 내 `selenium_profiles/{계정_이름}` 디렉터리를 삭제하고 재로그인 시도해볼 수 있습니다.
* Pixiv 로그인 세션은 만료될 수 있습니다. 이 경우 재로그인이 필요합니다."""
            messagebox.showinfo(help_title, help_text, parent=self.api_dialog_instance if hasattr(self, 'api_dialog_instance') and self.api_dialog_instance else self)


        def toggle_navigation_frame(self):
            # ... (기존과 동일) ...
            if self.navigation_frame_expanded:
                self.navigation_frame.configure(width=self.NAV_FRAME_COLLAPSED_WIDTH)
                self.nav_title_label.pack_forget()
                self.nav_content_frame.pack_forget()
                self.nav_bottom_controls_frame.pack_forget()
                self.nav_toggle_button.configure(text="▶") 
            else:
                self.navigation_frame.configure(width=self.NAV_FRAME_EXPANDED_WIDTH)
                self.nav_title_label.pack(side="left", padx=5) 
                self.nav_bottom_controls_frame.pack(side="bottom", fill="x", padx=10, pady=(10, 20)) 
                self.nav_content_frame.pack(pady=(0,0), padx=10, fill="both", expand=True) 
                self.nav_toggle_button.configure(text="⚙") 
            self.navigation_frame_expanded = not self.navigation_frame_expanded


        def _try_set_tumblr_blog(self, site_name, blog_name_to_set):
            # ... (기존과 동일) ...
            if site_name == "tumblr" and blog_name_to_set:
                blog_menu = self.tumblr_blog_menus.get(site_name)
                blog_var = self.tumblr_blog_vars.get(site_name)
                if blog_menu and blog_var:
                    current_blog_options = blog_menu.cget("values")
                    if blog_name_to_set in current_blog_options:
                        blog_var.set(blog_name_to_set)
                    elif current_blog_options and current_blog_options[0] != "블로그 선택": 
                        blog_var.set(current_blog_options[0]) 


        def _toggle_tumblr_blog_menu_state(self, site_name):
            # ... (기존과 동일) ...
            if site_name == "tumblr":
                is_tumblr_enabled_by_checkbox = self.site_vars["tumblr"].get()
                account_selected = self.site_account_vars["tumblr"].get() != "선택 안함"
                
                blog_menu = self.tumblr_blog_menus.get("tumblr")
                blog_var = self.tumblr_blog_vars.get("tumblr")

                if blog_menu and blog_var:
                    if is_tumblr_enabled_by_checkbox and account_selected:
                        self._load_tumblr_blogs_for_account(self.site_account_vars["tumblr"].get())
                        if blog_menu.cget("values") and blog_menu.cget("values")[0] not in ["블로그 선택", "블로그 없음", "블로그 로드 실패"]:
                            blog_menu.configure(state="normal")
                        else:
                            blog_menu.configure(state="disabled")
                    else:
                        blog_menu.configure(state="disabled", values=["블로그 선택"])
                        blog_var.set("블로그 선택")


        def _on_tumblr_account_selected_wrapper(self, site_name_unused, *args): 
            # ... (기존과 동일) ...
            selected_account = self.site_account_vars["tumblr"].get()
            self._load_tumblr_blogs_for_account(selected_account)
            self._toggle_tumblr_blog_menu_state("tumblr")


        def _load_tumblr_blogs_for_account(self, account_username):
            # ... (기존과 동일) ...
            blog_menu = self.tumblr_blog_menus.get("tumblr")
            blog_var = self.tumblr_blog_vars.get("tumblr")
            if not blog_menu or not blog_var: return

            if account_username == "선택 안함":
                blog_menu.configure(values=["블로그 선택"], state="disabled")
                blog_var.set("블로그 선택")
                return

            account_details = self.account_manager.get_account_details("tumblr", account_username)

            if account_details and "blogs" in account_details and account_details["blogs"]:
                blog_names = [blog['name'] for blog in account_details["blogs"]]
                primary_blog = account_details.get("primary_blog_name")

                blog_menu.configure(values=blog_names, state="normal")
                
                current_blog_selection = blog_var.get()
                if current_blog_selection in blog_names and current_blog_selection != "블로그 선택":
                    blog_var.set(current_blog_selection)
                elif primary_blog and primary_blog in blog_names:
                    blog_var.set(primary_blog)
                elif blog_names: 
                    blog_var.set(blog_names[0])
                else: 
                    blog_menu.configure(values=["블로그 없음"], state="disabled")
                    blog_var.set("블로그 없음")
            else:
                blog_menu.configure(values=["블로그 없음"], state="disabled")
                blog_var.set("블로그 없음")


        def _load_scheduled_posts(self):
            # ... (기존과 동일) ...
            try:
                with open(SCHEDULED_POSTS_FILE, 'r', encoding='utf-8') as f:
                    posts = json.load(f)
                    for post_id, post_data in posts.items():
                        if isinstance(post_data.get("scheduled_time"), str):
                            try:
                                post_data["scheduled_time"] = datetime.fromisoformat(post_data["scheduled_time"])
                            except ValueError:
                                print(f"경고: 예약된 포스트 {post_id}의 시간 형식 변환 실패: {post_data.get('scheduled_time')}")
                    return posts
            except FileNotFoundError:
                return {}
            except json.JSONDecodeError:
                print(f"오류: {SCHEDULED_POSTS_FILE} 파일이 손상되었습니다. 새 파일로 시작합니다.")
                return {}
            except Exception as e: 
                print(f"오류: 예약된 포스트 로드 실패 - {e}")
                return {}


        def _save_scheduled_posts(self):
            # ... (기존과 동일) ...
            posts_to_save = {}
            for post_id, post_data in self.scheduled_posts_data.items():
                data_copy = post_data.copy()
                if isinstance(data_copy.get("scheduled_time"), datetime):
                    data_copy["scheduled_time"] = data_copy["scheduled_time"].isoformat()
                posts_to_save[post_id] = data_copy

            try:
                with open(SCHEDULED_POSTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(posts_to_save, f, indent=4, ensure_ascii=False)
                return True
            except Exception as e:
                self.log_message(f"오류: 예약된 포스트 저장 실패 - {e}")
                return False

        def open_schedule_post_dialog(self):
            # ... (기존과 동일) ...
            image_path = self.image_path_var.get()
            if not image_path or not Path(image_path).exists():
                messagebox.showerror("오류", "예약할 이미지 파일을 먼저 선택해주세요.", parent=self)
                return
            
            title = self.entries["title_entry"].get()
            if not title:
                 if not messagebox.askyesno("확인", "제목 없이 예약을 진행하시겠습니까?", parent=self):
                     return

            dialog = SchedulePostDialog(self, self._add_new_scheduled_post)

        def _add_new_scheduled_post(self, scheduled_dt):
            # ... (기존과 동일) ...
            image_path = self.image_path_var.get()
            if not image_path or not Path(image_path).exists():
                self.log_message("오류: 예약 작업 추가 중 이미지 경로가 유효하지 않습니다.")
                messagebox.showerror("예약 오류", "이미지 경로가 유효하지 않아 예약을 추가할 수 없습니다.", parent=self)
                return

            post_details = {
                "image_path": image_path,
                "title": self.entries["title_entry"].get(),
                "description": self.entries["description_text"].get("1.0", tk.END).strip(),
                "tags_str": self.entries["tags_entry"].get(),
                "rating": self.entries["rating_entry"].get(),
                "source_url": self.entries["source_url_entry"].get()
            }

            selected_sites_accounts = {}
            has_selection = False
            for site_name, var in self.site_vars.items():
                if var.get():
                    account = self.site_account_vars[site_name].get()
                    if account != "선택 안함":
                        site_data = {"account": account}
                        if site_name == "tumblr":
                            blog_selection = self.tumblr_blog_vars.get(site_name, tk.StringVar(value="")).get()
                            if blog_selection and blog_selection not in ["블로그 선택", "블로그 없음", "블로그 로드 실패"]:
                                site_data["blog_name"] = blog_selection
                            else: 
                                self.log_message(f"Tumblr 예약: {account} 계정의 블로그가 선택되지 않았거나 유효하지 않습니다. 기본 블로그로 시도합니다.")
                        selected_sites_accounts[site_name] = site_data
                        has_selection = True
            
            if not has_selection:
                messagebox.showerror("예약 오류", "업로드할 사이트와 계정을 하나 이상 선택해야 합니다.", parent=self)
                return

            job_id = uuid.uuid4().hex 
            job_data = {
                "job_id": job_id,
                "scheduled_time": scheduled_dt, 
                "details": post_details,
                "sites_accounts_info": selected_sites_accounts, 
                "status": "pending", 
                "image_name_for_display": Path(image_path).name
            }

            self.scheduled_posts_data[job_id] = job_data

            try:
                self.scheduler.add_job(
                    self._execute_scheduled_post_wrapper,
                    trigger='date',
                    run_date=scheduled_dt,
                    args=[job_id],
                    id=job_id, 
                    misfire_grace_time=3600 
                )
                self._save_scheduled_posts()
                
                formatted_time = scheduled_dt.strftime('%Y년 %m월 %d일 %H시 %M분')
                self.log_message(f"포스팅이 예약되었습니다: {Path(image_path).name} -> {formatted_time}")
                messagebox.showinfo("예약 완료", f"'{Path(image_path).name}' 포스팅이 {formatted_time}에 예약되었습니다.", parent=self)

            except Exception as e:
                self.log_message(f"오류: APScheduler에 작업 추가 실패 - {e}")
                messagebox.showerror("예약 실패", f"스케줄러에 작업을 추가하는 중 오류가 발생했습니다: {e}", parent=self)
                if job_id in self.scheduled_posts_data:
                    del self.scheduled_posts_data[job_id]

        def _execute_scheduled_post_wrapper(self, job_id):
            # ... (기존과 동일) ...
            self.log_message(f"예약 작업 ID '{job_id}' 실행 시도...")
            job_data = self.scheduled_posts_data.get(job_id)

            if not job_data:
                self.log_message(f"오류: 예약 작업 ID '{job_id}' 데이터를 찾을 수 없습니다.")
                return

            if job_data["status"] == "completed":
                self.log_message(f"정보: 예약 작업 ID '{job_id}'는 이미 완료되었습니다.")
                return
            
            sites_to_upload_with_details = {}
            for site, site_info in job_data.get("sites_accounts_info", {}).items():
                sites_to_upload_with_details[site] = site_info 

            threading.Thread(target=self._perform_actual_upload, args=(
                job_data["details"]["image_path"],
                job_data["details"]["title"],
                job_data["details"]["description"],
                job_data["details"]["tags_str"],
                job_data["details"]["rating"],
                job_data["details"]["source_url"],
                sites_to_upload_with_details, 
                job_id 
            ), daemon=True).start()

        def _perform_actual_upload(self, image_path, title, description, tags_str, rating, source_url, sites_info_to_upload, job_id=None):
            # ... (기존과 동일) ...
            self.log_message(f"--- {'예약' if job_id else '즉시'} 업로드 시작 ({Path(image_path).name}) ---")
            
            if not Path(image_path).exists():
                self.log_message(f"오류: 이미지 파일을 찾을 수 없습니다 - {image_path}")
                if job_id:
                    self.scheduled_posts_data[job_id]["status"] = "failed_img_not_found"
                    self._save_scheduled_posts()
                return

            if ',' in tags_str: 
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            else: 
                tags = [tag.strip() for tag in tags_str.split(' ') if tag.strip()]
            
            active_uploads = []
            current_api_config = load_api_config()
            tumblr_ck = current_api_config.get("tumblr_consumer_key")
            tumblr_cs = current_api_config.get("tumblr_consumer_secret")
            twitter_cid = current_api_config.get("twitter_client_id") 
            twitter_cs = current_api_config.get("twitter_client_secret") 
            
            sites_str_for_log = []

            for site_name, site_details in sites_info_to_upload.items(): 
                selected_account = site_details.get("account")
                if not selected_account:
                    self.log_message(f"{site_name.capitalize()}: 계정 정보가 누락되어 건너뜁니다.")
                    continue

                sites_str_for_log.append(f"{site_name.capitalize()}({selected_account})")
                upload_params = {"title": title, "description": description, "tags": list(tags), "rating": rating, "source_url": source_url}
                uploader_instance = None
                specific_params = upload_params.copy()

                if site_name == "e621": uploader_instance = self.e621_uploader
                elif site_name == "tumblr":
                    if not tumblr_ck or not tumblr_cs: self.log_message(f"Tumblr 업로드 건너뜀 ({selected_account}): Consumer Key/Secret 미설정"); continue
                    blog_name_to_use = site_details.get("blog_name") 
                    
                    specific_params.update({"consumer_key": tumblr_ck, "consumer_secret": tumblr_cs, "blog_name": blog_name_to_use})
                    uploader_instance = self.tumblr_uploader
                elif site_name == "twitter":
                    specific_params.update({"client_id": twitter_cid, "client_secret": twitter_cs})
                    uploader_instance = self.twitter_uploader
                elif site_name == "pixiv": 
                    uploader_instance = self.pixiv_uploader 
                elif site_name == "furaffinity": uploader_instance = self.furaffinity_uploader
                elif site_name == "inkbunny": uploader_instance = self.inkbunny_uploader
                
                if uploader_instance:
                    active_uploads.append((uploader_instance, selected_account, site_name, specific_params))
                else:
                    self.log_message(f"{site_name.capitalize()}: 지원되지 않는 사이트이거나 설정 오류입니다.")

            if not active_uploads:
                self.log_message(f"업로드할 대상 사이트가 없습니다. ({Path(image_path).name})")
                if job_id:
                    self.scheduled_posts_data[job_id]["status"] = "failed_no_sites"
                    self._save_scheduled_posts()
                return

            all_successful = True
            for uploader, acc_username, site_display_name, params_for_upload in active_uploads:
                self.log_message(f"{site_display_name.capitalize()} ({acc_username}) 업로드 중...")
                url, err = uploader.upload(acc_username, image_path, **params_for_upload)
                if err:
                    self.log_message(f"{site_display_name.capitalize()} 업로드 실패 ({acc_username}): {err}")
                    all_successful = False
                else:
                    self.log_message(f"{site_display_name.capitalize()} 업로드 성공 ({acc_username}): {url}")
            
            self.log_message(f"--- {'예약' if job_id else '즉시'} 업로드 완료 ({Path(image_path).name}) ---")

            if job_id:
                job_data_ref = self.scheduled_posts_data.get(job_id) 
                if job_data_ref:
                    job_data_ref["status"] = "completed" if all_successful else "completed_with_errors"
                    self._save_scheduled_posts()
                    
                    log_time_obj = job_data_ref.get("scheduled_time")
                    if isinstance(log_time_obj, str) : log_time_obj = datetime.fromisoformat(log_time_obj)
                    
                    time_str_log = log_time_obj.strftime('%Y-%m-%d %H:%M') if log_time_obj else "알 수 없는 시간"
                    image_name_str_log = job_data_ref.get("image_name_for_display", Path(image_path).name)
                    sites_display_str_log = ", ".join(sites_str_for_log) if sites_str_for_log else "선택된 사이트 없음"

                    final_log_msg = f"예약 작업(날짜: {time_str_log}, 이미지: {image_name_str_log}, 사이트: {sites_display_str_log})을 실행했습니다."
                    if not all_successful: final_log_msg += " (일부 오류 발생)"
                    self.log_message(f"최종 실행 로그: {final_log_msg}")
            elif not job_id: 
                 self.after(0, lambda: messagebox.showinfo("업로드 완료", "선택된 사이트에 대한 즉시 업로드가 완료되었습니다. 로그를 확인하세요.", parent=self))

        def _process_startup_scheduled_jobs(self):
            # ... (기존과 동일) ...
            if not hasattr(self, 'scheduler') or not self.scheduler.running:
                self.log_message("경고: 스케줄러가 실행 중이 아니므로 시작 시 예약 작업을 처리할 수 없습니다.")
                return

            now = datetime.now()
            updated_jobs_in_json = False
            
            jobs_to_process = list(self.scheduled_posts_data.items())

            for job_id, job_data in jobs_to_process:
                status = job_data.get("status", "unknown")
                scheduled_time_val = job_data.get("scheduled_time")

                if isinstance(scheduled_time_val, str):
                    try:
                        scheduled_time_val = datetime.fromisoformat(scheduled_time_val)
                        job_data["scheduled_time"] = scheduled_time_val 
                    except ValueError:
                        self.log_message(f"오류: 작업 ID {job_id}의 예약 시간 형식 오류 - {scheduled_time_val}. 건너뜁니다.")
                        continue

                if not isinstance(scheduled_time_val, datetime):
                    self.log_message(f"오류: 작업 ID {job_id}에 유효한 scheduled_time이 없습니다. 건너뜁니다.")
                    continue

                if status == "completed" or status.startswith("failed_") or status == "completed_with_errors":
                    continue

                if scheduled_time_val <= now: 
                    job_data["status"] = "missed" 
                    updated_jobs_in_json = True

                    image_name_disp = job_data.get("image_name_for_display", Path(job_data.get("details", {}).get("image_path", "알 수 없는 이미지")).name)
                    sites_str_parts_disp = []
                    for site, site_info in job_data.get("sites_accounts_info", {}).items():
                        acc_name = site_info.get("account", "??")
                        blog_name = site_info.get("blog_name")
                        display_val = f"{site.capitalize()}({acc_name}"
                        if blog_name: display_val += f" -> {blog_name}"
                        display_val += ")"
                        sites_str_parts_disp.append(display_val)

                    sites_display_disp = ", ".join(sites_str_parts_disp) if sites_str_parts_disp else "선택된 사이트 없음"
                    time_display_disp = scheduled_time_val.strftime('%Y-%m-%d %H:%M')
                    
                    self.after(100, lambda j_id=job_id, j_data_copy=job_data.copy(), img_n=image_name_disp, sites_d=sites_display_disp, time_d=time_display_disp: \
                        self._prompt_missed_job(j_id, j_data_copy, img_n, sites_d, time_d))
                
                elif status == "pending": 
                    try:
                        if self.scheduler.get_job(job_id) is None:
                            self.scheduler.add_job(
                                self._execute_scheduled_post_wrapper,
                                trigger='date',
                                run_date=scheduled_time_val,
                                args=[job_id],
                                id=job_id,
                                misfire_grace_time=3600
                            )
                            self.log_message(f"예정된 작업 ID '{job_id}' ({scheduled_time_val.strftime('%Y-%m-%d %H:%M')})을 스케줄러에 다시 추가했습니다.")
                        else:
                            self.log_message(f"정보: 작업 ID '{job_id}'는 이미 스케줄러에 등록되어 있습니다.")
                    except Exception as e:
                        self.log_message(f"오류: 예정된 작업 ID '{job_id}'를 스케줄러에 다시 추가하는 중 오류 발생 - {e}")
            
            if updated_jobs_in_json:
                self._save_scheduled_posts()

        def _prompt_missed_job(self, job_id, job_data, image_name, sites_display, time_display):
            # ... (기존과 동일) ...
            msg = (f"다음 예약 작업 시간이 지났습니다!\n\n"
                   f"날짜/시간: {time_display}\n"
                   f"이미지: {image_name}\n"
                   f"사이트: {sites_display}\n\n"
                   f"지금 포스팅하시겠습니까?")
            
            if messagebox.askyesno("지난 예약 작업 알림", msg, parent=self):
                self.log_message(f"사용자 확인: 지난 예약 작업 ID '{job_id}'를 지금 실행합니다.")
                self._execute_scheduled_post_wrapper(job_id)
            else:
                self.log_message(f"사용자 취소: 지난 예약 작업 ID '{job_id}'를 실행하지 않습니다. (상태: missed)")

        def _on_preview_frame_configure(self, event=None):
            # ... (기존과 동일) ...
            if self.original_image_for_preview:
                if not self._preview_configure_scheduled:
                    self._preview_configure_scheduled = True
                    self.after(50, self._process_preview_resize) 

        def _process_preview_resize(self):
            # ... (기존과 동일) ...
            self._preview_configure_scheduled = False
            if self.original_image_for_preview:
                current_frame_height = self.preview_frame.winfo_height()
                if abs(self._last_rendered_preview_height - current_frame_height) > 1:
                    try:
                        self._render_preview_image(self.original_image_for_preview)
                        self._last_rendered_preview_height = current_frame_height
                    except Exception as e:
                        self.log_message(f"Error during scheduled preview resize: {e}")
            else: 
                self.preview_frame.configure(height=self.DEFAULT_PREVIEW_FRAME_HEIGHT)
                self._last_rendered_preview_height = self.preview_frame.winfo_height() 


        def _render_preview_image(self, pil_image_to_render):
            # ... (기존과 동일) ...
            new_ctk_img_obj = None
            try:
                original_width, original_height = pil_image_to_render.size
                if original_height == 0 or original_width == 0:
                    raise ValueError("렌더링을 위한 이미지 크기가 유효하지 않습니다 (0 dimension).")
                img_aspect_ratio = original_width / original_height

                preview_frame_current_width = self.preview_frame.winfo_width()
                preview_frame_current_height = self.preview_frame.winfo_height() 

                content_width_available = preview_frame_current_width - 2 * self.PREVIEW_FRAME_PADDING
                content_height_available = preview_frame_current_height - 2 * self.PREVIEW_FRAME_PADDING

                if content_width_available <= 0: content_width_available = 1 
                if content_height_available <= 0: content_height_available = 1

                img_h = content_height_available
                img_w = int(img_h * img_aspect_ratio) if img_aspect_ratio > 0 else content_height_available

                if img_w > content_width_available:
                    img_w = content_width_available
                    img_h = int(img_w / img_aspect_ratio) if img_aspect_ratio > 0 else content_width_available
                
                final_img_w = max(1, int(img_w))
                final_img_h = max(1, int(img_h))
                
                resized_pil_image = pil_image_to_render.copy().resize((final_img_w, final_img_h), Image.Resampling.LANCZOS)
                new_ctk_img_obj = ctk.CTkImage(light_image=resized_pil_image,
                                             dark_image=resized_pil_image,
                                             size=(final_img_w, final_img_h))
                
                self.preview_label.configure(image=new_ctk_img_obj, text="")
                self.loaded_image_tk = new_ctk_img_obj
                self.original_image_for_preview = pil_image_to_render

            except Exception as e:
                self.log_message(f"이미지 미리보기 렌더링 중 내부 오류: {e}")
                self.preview_frame.configure(height=self.DEFAULT_PREVIEW_FRAME_HEIGHT)
                self.preview_label.configure(image=None, text="미리보기 렌더링 오류")
                self.loaded_image_tk = None


        def select_image_file(self):
            # ... (기존과 동일) ...
            self.preview_label.configure(text="이미지 선택 중...")
            self.update_idletasks()
            file_path_selected = filedialog.askopenfilename(
                title="이미지 파일 선택",
                filetypes=(("이미지 파일", "*.jpg *.jpeg *.png *.gif"), ("모든 파일", "*.*"))
            )
            if file_path_selected:
                try:
                    pil_image = Image.open(file_path_selected)
                    self._last_rendered_preview_height = 0 
                    initial_preview_height = max(self.PREVIEW_MIN_FRAME_HEIGHT_WITH_IMAGE, self.DEFAULT_PREVIEW_FRAME_HEIGHT)
                    self.preview_frame.configure(height=initial_preview_height)
                    self.update_idletasks() 
                    self._render_preview_image(pil_image)
                    self.image_path_var.set(file_path_selected)
                except Exception as e:
                    self.log_message(f"이미지 파일 선택 또는 미리보기 처리 실패: {e}")
                    self.preview_label.configure(image=None, text=f"미리보기 오류:\n{Path(file_path_selected).name if file_path_selected else '파일 오류'}")
                    self.loaded_image_tk = None
                    self.original_image_for_preview = None
                    self.image_path_var.set("")
                    self.preview_frame.configure(height=self.DEFAULT_PREVIEW_FRAME_HEIGHT)
                    self._last_rendered_preview_height = self.preview_frame.winfo_height() 
            else: 
                if not self.loaded_image_tk: 
                    self.preview_label.configure(image=None, text="선택된 이미지 미리 보기")
                    self.image_path_var.set("")
                    self.original_image_for_preview = None 
                    self.preview_frame.configure(height=self.DEFAULT_PREVIEW_FRAME_HEIGHT)
                    self._last_rendered_preview_height = self.preview_frame.winfo_height()

        def _load_posting_inputs(self):
            # ... (기존과 동일) ...
            last_inputs = self.post_preset_config.get("last_posting_inputs", {}) 
            if not last_inputs:
                return
            
            if "title" in last_inputs and "title_entry" in self.entries:
                self.entries["title_entry"].delete(0, tk.END) 
                self.entries["title_entry"].insert(0, last_inputs["title"])
            if "description" in last_inputs and "description_text" in self.entries:
                self.entries["description_text"].delete("1.0", tk.END) 
                self.entries["description_text"].insert("1.0", last_inputs["description"])
            if "tags" in last_inputs and "tags_entry" in self.entries:
                self.entries["tags_entry"].delete(0, tk.END) 
                self.entries["tags_entry"].insert(0, last_inputs["tags"])
            if "rating" in last_inputs and "rating_entry" in self.entries:
                self.entries["rating_entry"].delete(0, tk.END)
                self.entries["rating_entry"].insert(0, last_inputs["rating"])
            if "source_url" in last_inputs and "source_url_entry" in self.entries:
                self.entries["source_url_entry"].delete(0, tk.END) 
                self.entries["source_url_entry"].insert(0, last_inputs["source_url"])

        def _save_posting_inputs(self, save_to_file=False): 
            # ... (기존과 동일) ...
            current_inputs = {
                "title": self.entries["title_entry"].get() if "title_entry" in self.entries else "",
                "description": self.entries["description_text"].get("1.0", tk.END).strip() if "description_text" in self.entries else "",
                "tags": self.entries["tags_entry"].get() if "tags_entry" in self.entries else "",
                "rating": self.entries["rating_entry"].get() if "rating_entry" in self.entries else "s",
                "source_url": self.entries["source_url_entry"].get() if "source_url_entry" in self.entries else ""
            }
            self.post_preset_config["last_posting_inputs"] = current_inputs 
            
            if save_to_file: 
                if save_post_preset_config(self.post_preset_config): 
                    self.log_message("현재 입력된 포스팅 내용이 저장되었습니다.")
                    messagebox.showinfo("저장 완료", "현재 입력된 포스팅 내용이 저장되었습니다.", parent=self)
                else:
                    self.log_message("오류: 포스팅 내용 저장에 실패했습니다. 콘솔 로그를 확인하세요.")
                    messagebox.showerror("저장 실패", "포스팅 내용 저장에 실패했습니다. 자세한 내용은 로그를 확인하세요.", parent=self)

        def toggle_all_sites(self):
            # ... (기존과 동일) ...
            select_all = self.select_all_sites_var.get()
            for site_name, checkbox_var in self.site_vars.items():
                if self.site_checkboxes[site_name].cget('state') == ctk.NORMAL: 
                     checkbox_var.set(select_all)

        def show_help(self):
            # ... (기존과 동일) ...
            messagebox.showinfo("도움말", "사이트 계정 / API 설정: 각 사이트 API 연결 관리\n"
                                       "업로드할 사이트: 체크된 사이트에 이미지를 업로드합니다.\n"
                                       "계정 선택: 각 사이트별로 연결된 계정 중 업로드할 계정을 선택합니다.\n"
                                       "즉시 포스팅: 입력된 정보로 즉시 업로드를 시작합니다.\n"
                                       "예약 포스팅: 지정된 시간에 포스팅을 예약합니다.\n\n"
                                       "Pixiv 연동 시 ChromeDriver가 필요할 수 있습니다. 자세한 내용은 Pixiv 연결 도움말을 참조하세요.", parent=self)


        def update_account_option_menus(self):
            # ... (기존과 동일) ...
            for site_name in self.supported_sites:
                menu_widget = self.site_account_menus.get(site_name)
                checkbox_widget = self.site_checkboxes.get(site_name)
                if not menu_widget: continue
                accounts = self.account_manager.get_connected_accounts(site_name)
                usernames = ["선택 안함"] + [acc['username'] for acc in accounts]
                has_accounts = len(accounts) > 0
                
                current_account_selection = self.site_account_vars[site_name].get()
                menu_widget.configure(values=usernames, state=ctk.NORMAL if has_accounts else ctk.DISABLED)
                if current_account_selection not in usernames:
                    self.site_account_vars[site_name].set(usernames[0])
                
                if checkbox_widget:
                    checkbox_widget.configure(state=ctk.NORMAL if has_accounts else ctk.DISABLED)
                    if not has_accounts: self.site_vars[site_name].set(False)
                
                if site_name == "tumblr":
                    self._toggle_tumblr_blog_menu_state(site_name)


        def start_upload_process(self):
            # ... (기존과 동일) ...
            image_path = self.image_path_var.get()
            if not image_path or not Path(image_path).exists():
                messagebox.showerror("오류", "업로드할 이미지 파일을 먼저 선택해주세요.", parent=self)
                return
            
            title = self.entries["title_entry"].get()
            description = self.entries["description_text"].get("1.0", tk.END).strip()
            tags_str = self.entries["tags_entry"].get()
            rating = self.entries["rating_entry"].get()
            source_url = self.entries["source_url_entry"].get()

            sites_info_to_upload = {} 
            has_selection = False
            for site_name, var in self.site_vars.items():
                if var.get():
                    account = self.site_account_vars[site_name].get()
                    if account != "선택 안함":
                        site_data = {"account": account}
                        if site_name == "tumblr":
                            blog_selection = self.tumblr_blog_vars.get(site_name, tk.StringVar(value="")).get()
                            if blog_selection and blog_selection not in ["블로그 선택", "블로그 없음", "블로그 로드 실패"]:
                                site_data["blog_name"] = blog_selection
                            else: 
                                acc_details = self.account_manager.get_account_details("tumblr", account)
                                if acc_details and acc_details.get("primary_blog_name"):
                                    site_data["blog_name"] = acc_details["primary_blog_name"]
                                elif acc_details and acc_details.get("blogs"):
                                    site_data["blog_name"] = acc_details["blogs"][0]['name'] 
                                else:
                                    self.log_message(f"Tumblr 즉시 포스팅: {account} 계정의 블로그 정보를 찾을 수 없습니다. 기본 블로그로 시도합니다.")
                        sites_info_to_upload[site_name] = site_data
                        has_selection = True
            
            if not has_selection:
                messagebox.showwarning("업로드 중단", "업로드할 대상 사이트와 계정을 하나 이상 선택해야 합니다.", parent=self)
                return

            threading.Thread(target=self._perform_actual_upload, args=(
                image_path, title, description, tags_str, rating, source_url, sites_info_to_upload
            ), daemon=True).start()

        def log_message(self, message):
            if not hasattr(self, 'log_textbox') or not self.log_textbox.winfo_exists(): return
            
            self.log_textbox.configure(state="normal")
            
            # URL 패턴 (http, https)
            url_pattern = r"https?://[^\s]+"
            
            # 메시지에서 URL 찾기
            urls_found = re.findall(url_pattern, message)
            
            if not urls_found: # URL이 없으면 일반 텍스트로 추가
                self.log_textbox.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            else:
                # 시간 정보 먼저 추가
                self.log_textbox.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ")
                
                last_end = 0
                for url in urls_found:
                    start_index = message.find(url, last_end)
                    if start_index != -1:
                        # URL 앞부분 텍스트 추가
                        self.log_textbox.insert(tk.END, message[last_end:start_index])
                        # URL 하이퍼링크로 추가
                        link_start = self.log_textbox.index(tk.INSERT)
                        self.log_textbox.insert(tk.INSERT, url, "hyperlink")
                        link_end = self.log_textbox.index(tk.INSERT)
                        # self.log_textbox.tag_add("hyperlink", link_start, link_end) # 이미 tag_config에서 설정됨
                        last_end = start_index + len(url)
                
                # URL 뒷부분 나머지 텍스트 추가
                self.log_textbox.insert(tk.END, message[last_end:] + "\n")

            self.log_textbox.see(tk.END)
            self.log_textbox.configure(state="disabled") 
            print(message)


        def open_api_connection_dialog(self):
            # ... (기존과 동일) ...
            self.api_dialog_instance = ApiConnectionDialog(self, self.account_manager)
            self.api_dialog_instance.grab_set()

        def reload_api_config_and_update_ui(self):
            # ... (기존과 동일) ...
            self.api_config = load_api_config()
            self.account_manager.accounts = self.api_config.get("connected_accounts", {})
            self.update_account_option_menus()

        def change_appearance_mode(self, new_mode):
            # ... (기존과 동일) ...
            ctk.set_appearance_mode(new_mode)
            self.post_preset_config["appearance_mode"] = new_mode

        def change_color_theme(self, new_theme):
            # ... (기존과 동일) ...
            self.post_preset_config["color_theme"] = new_theme
            try:
                messagebox.showinfo("테마 변경", f"UI 색상이 '{new_theme}'(으)로 설정되었습니다. 프로그램 재시작 시 완벽히 적용됩니다.", parent=self)
            except Exception as e:
                print(f"Error changing color theme: {e}")
                messagebox.showwarning("테마 변경 오류", f"색상 테마 변경 중 오류 발생: {e}", parent=self)

        def on_closing(self):
            # ... (기존과 동일) ...
            self._save_posting_inputs(save_to_file=False) 

            selected_accounts_ui = {}
            for site_name_key, var_obj in self.site_account_vars.items():
                account_selection = var_obj.get()
                site_info_to_save = {"account": account_selection}
                if site_name_key == "tumblr" and self.tumblr_blog_vars.get(site_name_key):
                    blog_selection = self.tumblr_blog_vars[site_name_key].get()
                    if blog_selection and blog_selection not in ["블로그 선택", "블로그 없음", "블로그 로드 실패"]:
                        site_info_to_save["selected_blog"] = blog_selection
                selected_accounts_ui[site_name_key] = site_info_to_save

            self.post_preset_config["selected_accounts_ui"] = selected_accounts_ui
            
            if not save_post_preset_config(self.post_preset_config):
                print("ERROR: Final post preset configuration save failed on closing.")

            if hasattr(self, 'scheduler') and self.scheduler.running:
                try:
                    self.scheduler.shutdown()
                    self.log_message("예약 스케줄러가 종료되었습니다.")
                except Exception as e:
                    self.log_message(f"스케줄러 종료 중 오류 발생: {e}")

            if hasattr(self, 'api_dialog_instance') and self.api_dialog_instance and self.api_dialog_instance.winfo_exists():
                 if hasattr(self.api_dialog_instance, '_stop_local_server'):
                      self.api_dialog_instance._stop_local_server()
            self.destroy()

    # App 인스턴스 생성 및 실행
    app = App()
    app.mainloop()


# --- 메인 실행 부분 ---
if __name__ == "__main__":
    print("DEBUG: Script execution started in __main__.")
    
    # 패키지 설치 확인 및 설치 시도
    if ensure_packages_installed(): 
        # 모든 패키지가 준비되었으므로 애플리케이션 로직 실행
        print("DEBUG: Proceeding to run main application logic.")
        run_main_application()
    else:
        # 이 부분은 ensure_packages_installed 내부에서 sys.exit가 호출되므로 이론적으로 도달하지 않음
        print("CRITICAL: Package installation check failed or user aborted. Exiting.")
        sys.exit("패키지 문제로 프로그램 종료")