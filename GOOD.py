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

# タイムアウト設定（10分で強制終了）
START_TIME = time.time()
LIMIT_TIME = 600 

def load_settings():
    config_env = os.getenv('RAKUTEN_CONFIG_JSON')
    if config_env:
        return json.loads(config_env)
    else:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)

config = load_settings()

options = webdriver.chrome.options.Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(5)

def login():
    try:
        print("ログイン開始...")
        driver.get('https://room.rakuten.co.jp/common/login?redirectafterlogin=/items')
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(config["email"])
        driver.find_element(By.ID, 'cta001').click()
        time.sleep(2)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(config["password"])
        driver.find_element(By.ID, 'cta011').click()
        time.sleep(5)
        print("ログイン完了")
    except Exception as e:
        print(f"ログイン失敗: {e}")

def good_job(target_num):
    cnt = 0
    checked_num = 0
    print(f"目標件数: {target_num}件")
    
    while cnt < target_num:
        # タイムアウトチェック
        if time.time() - START_TIME > LIMIT_TIME:
            print("!!! 制限時間（10分）に達したため終了します !!!")
            break

        try:
            items = driver.find_elements(By.CSS_SELECTOR, '.item-navigation.ng-scope')
            
            # 商品が足りなければスクロール
            if len(items) <= checked_num:
                print("スクロールして商品を追加読み込み中...")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(3)
                items = driver.find_elements(By.CSS_SELECTOR, '.item-navigation.ng-scope')
                if len(items) <= checked_num:
                    print("これ以上商品が見つかりません。")
                    break

            target_item = items[checked_num]
            like_btn = target_item.find_elements(By.TAG_NAME, 'a')[2] # いいねボタン
            
            # 未いいねか確認
            if 'isLiked' not in like_btn.get_attribute('class'):
                driver.execute_script("arguments[0].click();", like_btn)
                cnt += 1
                print(f"【進捗】{cnt}件目のいいね完了 (チェック済み合計: {checked_num + 1}件)")
                time.sleep(random.uniform(2, 5)) # サーバー向けに短縮
            else:
                # すでにいいね済みならスルー
                pass
            
            checked_num += 1

        except Exception as e:
            checked_num += 1
            continue
    return cnt

if __name__ == '__main__':
    print(f"--- 実行開始: {dt.now()} ---")
    try:
        login()
        driver.get('https://room.rakuten.co.jp/items')
        time.sleep(3)
        # サーバー負荷を考え、1回の目標を控えめに設定（30-50件など）
        result = good_job(random.randint(40, 50))
        print(f"最終結果: {result} 商品に「いいね」しました。")
    finally:
        driver.quit()
        print(f"--- 終了: {dt.now()} ---")
