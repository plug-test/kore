import os
import time
import random
import sys
import json
from datetime import datetime as dt
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# --- 設定の読み込み ---
def load_settings():
    # GitHub Secrets（環境変数）から取得するか、ローカルの config.json を参照する
    config_env = os.getenv('RAKUTEN_CONFIG_JSON')
    if config_env:
        try:
            return json.loads(config_env)
        except json.JSONDecodeError:
            print("Error: GitHub Secrets の形式が正しくありません。")
            sys.exit(1)
    else:
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: config.json または GitHub Secrets が設定されていません。")
            sys.exit(1)

config = load_settings()

# --- WebDriver設定 ---
options = webdriver.chrome.options.Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# ユーザーデータディレクトリの設定
if config.get("user_data_dir") and os.path.exists(config["user_data_dir"]):
    options.add_argument(f'--user-data-dir={config["user_data_dir"]}')

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(10)

def login():
    try:
        print("ログインを開始します...")
        driver.get('https://room.rakuten.co.jp/common/login?redirectafterlogin=/items')
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(config["email"])
        driver.find_element(By.ID, 'cta001').click()
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(config["password"])
        driver.find_element(By.ID, 'cta011').click()
        time.sleep(5)
    except Exception as e:
        print(f"ログインエラー: {e}")

def search():
    try:
        # config.jsonの keyword から取得
        tag = config.get("keyword", "楽天")
        print(f"検索ワード: {tag}")
        search_url = f'https://room.rakuten.co.jp/search/item?keyword={tag}&original_photo=0'
        driver.get(search_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.item-navigation.ng-scope')))
    except Exception as e:
        print(f"検索エラー: {e}")
        return None
    return tag

def kore(set_num):
    cnt = 0
    num = 0
    while set_num > cnt:
        try:
            # スクロールして要素を読み込み
            scroll_check = 0
            while len(driver.find_elements(By.CSS_SELECTOR, '.item-navigation.ng-scope')) <= num:
                if scroll_check >= 6: return cnt
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                scroll_check += 1
                time.sleep(5)

            items = driver.find_elements(By.CSS_SELECTOR, '.item-navigation.ng-scope')
            target = items[num].find_elements(By.TAG_NAME, 'a')[0]

            # 「コレ！」ボタンが押せるかチェック
            if target.get_attribute('class') == 'icon-hand left':
                target.click()
                
                # モーダル待ち
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.item-name.ng-binding')))
                
                # 上限チェック
                if len(driver.find_elements(By.CSS_SELECTOR, '.dialog-container.modal-popup')) > 0:
                    print("「コレ！」の上限に達しました。")
                    break
                
                # すでにコレ！済みの場合
                if len(driver.find_elements(By.CLASS_NAME, 'ok')) > 0:
                    driver.find_element(By.CLASS_NAME, 'ok').click()
                else:
                    # メモとハッシュタグを入力
                    memo = config.get("memo", "")
                    title = driver.find_element(By.CSS_SELECTOR, '.item-name.ng-binding').text + "\n" + memo
                    hashtags = "\n\n【タグ検索用】\n#39ショップ #おすすめ #買ってよかった #おしゃれ #人気 #ランキング #ずっと欲しかった #あったら便利 #ポイント消化 #買い回り #買いまわり #お買い物マラソン #楽天スーパーSALE #お買い物メモ"
                    
                    driver.find_element(By.ID, 'collect-content').send_keys(title + hashtags)
                    time.sleep(1)
                    
                    # 完了ボタン
                    driver.find_element(By.CSS_SELECTOR, '.button.button-red.collect-btn').click()
                    
                    # 完了後の×ボタン
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-cross-normal')))
                    driver.find_element(By.CLASS_NAME, 'icon-cross-normal').click()
                    
                    cnt += 1
                    print(f"コレ！完了: {cnt}件目")
                    # ランダム待機
                    time.sleep(random.randint(15, 30))
            else:
                time.sleep(1)
            num += 1
        except Exception as e:
            print(f"ループ中にエラー（スキップします）: {e}")
            num += 1
            continue
    return cnt

if __name__ == '__main__':
    print(f"--- 実行開始: {dt.now()} ---")
    try:
        login()
        tag_used = search()
        if tag_used:
            # 実行件数（今回は1件に設定されていますが適宜変更してください）
            result_cnt = kore(1)
            print(f"結果: 「{tag_used}」で {result_cnt} 商品を「コレ！」しました。")
    finally:
        driver.quit()
        print(f"--- 終了: {dt.now()} ---")
