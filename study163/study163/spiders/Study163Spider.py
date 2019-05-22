# -*- coding: utf-8 -*-
import time

from scrapy.utils.project import get_project_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from study163.common.SeleniumSpider import SeleniumSpider


class Study163Spider(SeleniumSpider):
    name: str = 'study163'
    allowed_domains: list = ['study.163.com']
    start_url: str = 'https://study.163.com/member/login.htm'

    settings = None

    def __init__(self, *a, **kw):
        super(Study163Spider, self).__init__(*a, **kw)
        self.settings = get_project_settings()

    def start_requests(self):
        self.browser.get(self.start_url)
        try:
            is_login_frame_present = WebDriverWait(self.browser, 20).until(
                EC.frame_to_be_available_and_switch_to_it((By.XPATH, "//iframe[contains(@src,'dl.reg.163.com')]"))
            )
            if is_login_frame_present:
                user_input = self.browser.find_element_by_xpath("//input[@name='email' and @type='tel']")
                user_input.send_keys(self.settings.get('USER_NAME'))
                pwd_input = self.browser.find_element_by_xpath("//input[@name='email' and @type='password']")
                pwd_input.send_keys(self.settings.get('PASSWORD'))
                self.browser.find_element_by_xpath("//a[@id='submitBtn']").click()
                is_search_box_present = WebDriverWait(self.browser, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@type='text' and @class='j-input j-searchInput']"))
                )
                time.sleep(2)
                if is_search_box_present:
                    self.browser.get('https://study.163.com/course/courseMain.htm?courseId=1005359012')
                    WebDriverWait(self.browser, 30).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, "//a[span[contains(text(),'继续学习')]]"))
                    )
                    cont_stydy_btn_element = self.browser.find_element_by_xpath("//a[span[contains(text(),'继续学习')]]")
                    self.browser.execute_script('arguments[0].click();', cont_stydy_btn_element)
                    is_chap_list_present = WebDriverWait(self.browser, 20).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[@class='m-chapterList']"))
                    )
                    if is_chap_list_present:
                        section_element_list = self.browser.find_elements_by_xpath("//div[contains(@class,'section')]")
                        lesson_idx_list = list(map(lambda section: section.get_attribute('data-lesson'), section_element_list))
                        for lesson_idx in lesson_idx_list:
                            section = self.browser.find_element_by_xpath(f"//div[@data-lesson='{lesson_idx}']")
                            self.browser.execute_script('arguments[0].click();', section)
                            is_main_video_present = WebDriverWait(self.browser, 20).until(
                                EC.visibility_of_element_located(
                                    (By.XPATH, "//div[contains(@class,'u-edu-h5player-mainvideo')]")
                                )
                            )
                            time.sleep(5)
                            if is_main_video_present:
                                print(f'Extracting {lesson_idx} url')
                                if lesson_idx == 3:
                                    print('please wait here')
                                video_url = self.browser.find_element_by_xpath(
                                    "//div[contains(@class,'u-edu-h5player-mainvideo')]"
                                ).find_element_by_xpath(
                                    "//video/source"
                                ).get_attribute('src')
                                print(video_url)
            else:
                raise Exception(f'{self.start_url} is not loaded correctly.')


        finally:
            print('llllll')

    def parse(self, response):
        pass
