#!/usr/bin/env python3
# encoding=utf-8


import os
import platform
import random
import subprocess
from time import sleep
from random import choice
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

import seckill.settings as utils_settings
from utils.utils import get_useragent_data

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



# 抢购失败最大次数
max_retry_count = 30


def default_chrome_path():

    driver_dir = getattr(utils_settings, "DRIVER_DIR", None)
    if platform.system() == "Windows":
        if driver_dir:
            return os.path.abspath(os.path.join(driver_dir, "chromedriver.exe"))

        raise Exception("The chromedriver drive path attribute is not found.")
    else:
        if driver_dir:
            return os.path.abspath(os.path.join(driver_dir, "chromedriver"))

        raise Exception("The chromedriver drive path attribute is not found.")



class ChromeDrive:

    def __init__(self, chrome_path=default_chrome_path(), seckill_time=None, password=None):
        self.chrome_path = chrome_path
        self.seckill_time = seckill_time
        self.seckill_time_obj = datetime.strptime(self.seckill_time, '%Y-%m-%d %H:%M:%S.%f')
        self.password = password

    def start_driver(self):
        try:
            # shell = True表示直接在解释器中运行，即不会弹出黑的命令行。这句话很关键，可以防止淘宝检测到elenum
            subprocess.Popen('chrome.exe --remote-debugging-port=9999 --user-data-dir="C:\selenum\AutomationProfile')
            driver = self.find_chromedriver()
            # os.system(r'C:\Users\Administrator\AppData\Local\Google\Chrome\Application/chrome.exe --remote-debugging-port=9999 --user-data-dir="C:\selenum\AutomationProfile"')

            # wait = WebDriverWait(driver, 5)
            # print(driver.title)
            #
            # # 当前句柄
            # current_handle = driver.current_window_handle
            #
            # # browser.execute_script('window.open("https://login.taobao.com/member/login.jhtml")')
            # driver.execute_script('window.open("http://www.baidu.com")')
            #
            # # 所有句柄
            # all_handle = driver.window_handles
            # second_handle = all_handle[-1]
            #
            # # 切回first
            # driver.switch_to.window(current_handle)

        except WebDriverException:
            print("Unable to find chromedriver, Please check the drive path.")
        else:
            return driver

    def find_chromedriver(self):
        try:
            driver = webdriver.Chrome()

        except WebDriverException:
            try:
                driver = webdriver.Chrome(executable_path=self.chrome_path, chrome_options=self.build_chrome_options())

            except WebDriverException:
                raise
        return driver

    def build_chrome_options(self):
        """配置启动项"""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.accept_untrusted_certs = True
        chrome_options.assume_untrusted_cert_issuer = True
        arguments = ['--no-sandbox', '--disable-impl-side-painting', '--disable-setuid-sandbox', '--disable-seccomp-filter-sandbox',
                     '--disable-breakpad', '--disable-client-side-phishing-detection', '--disable-cast',
                     '--disable-cast-streaming-hw-encoding', '--disable-cloud-import', '--disable-popup-blocking',
                     '--ignore-certificate-errors', '--disable-session-crashed-bubble', '--disable-ipv6',
                     '--allow-http-screen-capture', '--start-maximized']
        for arg in arguments:
            chrome_options.add_argument(arg)
        chrome_options.add_argument(f'--user-agent={choice(get_useragent_data())}')

        chrome_debug_port = 9999
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{chrome_debug_port}")
        return chrome_options

    def _login(self, login_url: str="https://www.taobao.com"):
        if login_url:
            self.driver = self.start_driver()
        else:
            print("Please input the login url.")
            raise Exception("Please input the login url.")

        self.driver.get(login_url)
        try:
            if self.driver.find_element_by_link_text("亲，请登录"):
                print("没登录，请及时扫码登录！")
                self.driver.find_element_by_link_text("亲，请登录").click()
                # print("请在30s内扫码登陆!!")
        except NoSuchElementException as e:
            self.driver.get('https://www.taobao.com/')
            user_name_xpath = '//div[@class="site-nav-user"]/a'
            user_name = self.driver.find_element_by_xpath(user_name_xpath).text
            print("登陆成功:{}".format(user_name))
            return
        except Exception as e:
            print('登陆发生异常,请先登陆!', e)
            return

        while True:
            try:
                # if self.driver.find_element_by_link_text("亲，请登录"):
                #     print("没登录，开始点击登录按钮...")
                #     self.driver.find_element_by_link_text("亲，请登录").click()
                #     print("请在30s内扫码登陆!!")
                #     sleep(30)
                if self.driver.find_element_by_xpath('//*[@id="J_SiteNavMytaobao"]/div[1]/a/span'):
                    print("登陆成功")
                    break
                else:
                    print("登陆失败, 刷新重试, 请尽快登陆!!!")
                    continue
            except Exception as e:
                # print(str(e))
                continue

    def keep_wait(self):
        self._login()
        now = datetime.now()
        if now >= self.seckill_time_obj:
            return
        print("等待到点抢购...")
        while True:
            last = (self.seckill_time_obj - datetime.now()).seconds
            if last > 180:
                self.driver.get("https://cart.taobao.com/cart.htm")
                print("随机刷新一次界面，防止登录超时...距离开抢{}秒".format(last))
                sec = random.randint(50, 100)
                sleep(sec)
            else:
                print("抢购时间点将近，停止自动刷新，准备进入抢购阶段...")
                break

    def sec_kill(self):
        self.keep_wait()
        submit_succ = False
        retry_count = 0

        while True:
            self.driver.get("https://cart.taobao.com/cart.htm")
            sleep(1)

            try:
                if self.driver.find_element_by_id("J_SelectAll1"):
                    self.driver.find_element_by_id("J_SelectAll1").click()
                    print("已经选中全部商品！！！")
            except Exception as e:
                print("登陆可能已经失效，请重新登陆后再试！")
                return
            now = datetime.now()
            if now >= self.seckill_time_obj:
                print(f"开始抢购, 尝试次数： {str(retry_count)}")
                if submit_succ:
                    print("订单已经提交成功，无需继续抢购...")
                    break
                if retry_count > max_retry_count:
                    print("重试抢购次数达到上限，放弃重试...")
                    break

                retry_count += 1

                try:
                    if self.driver.find_element_by_id("J_Go"):
                        self.driver.find_element_by_id("J_Go").click()
                        print("已经点击结算按钮...")
                        click_submit_times = 0
                        while True:
                            try:
                                if click_submit_times < 10:
                                    self.driver.find_element_by_link_text('提交订单').click()
                                    print("已经点击提交订单按钮")
                                    submit_succ = True
                                    break
                                else:
                                    print("提交订单失败...")
                                    break
                            except Exception as e:

                                print("没发现提交按钮, 页面未加载, 重试...")
                                click_submit_times = click_submit_times + 1
                                sleep(0.1)
                except Exception as e:
                    # print(e)
                    print("可能出了点问题!!!", e)

            sleep(0.1)
        if submit_succ:
            if self.password:
                self.pay()


    def pay(self):
        try:
            element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'sixDigitPassword')))
            element.send_keys(self.password)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'J_authSubmit'))).click()
            print("付款成功")
        except:
            print('付款失败')
        finally:
            sleep(60)
            self.driver.quit()
