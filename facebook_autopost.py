import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from configparser import RawConfigParser
import pathlib
import google.generativeai as genai
import sys
import hashlib
import json


class FacebookAutoPost:
    def __init__(self, email, password, gemini_api_key, post_prompt, post_interval, profile_name="default"):
        self.email = email
        self.password = password
        self.profile_name = profile_name
        self.post_prompt = post_prompt
        self.post_interval = post_interval
        self.profile_path = self._setup_profile_path()
        self.driver = self._setup_driver()
        self.wait = WebDriverWait(self.driver, 3)
        self.setup_gemini(gemini_api_key)
        self.previous_posts = self.load_previous_posts()

    def _setup_profile_path(self):
        base_path = pathlib.Path(__file__).parent.absolute()
        profile_path = base_path / "browser_profiles" / self.profile_name
        profile_path.mkdir(parents=True, exist_ok=True)
        return str(profile_path)

    def _setup_driver(self):
        options = Options()

        #options.add_argument(f'user-data-dir={self.profile_path}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-notifications")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        options.add_argument('--log-level=3')

        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1920, 1080)

        return driver

    def login(self):
        try:
            print(f"Attempting to log in with email: {self.email}")
            self.driver.get("https://www.facebook.com")
            time.sleep(random.uniform(3, 5))

            try:
                self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Create a post']")))
                print("Already logged in!")
                return True
            except:
                print("Need to login...")

            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
            password_field = self.driver.find_element(By.ID, "pass")

            for char in self.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.uniform(0.5, 1.5))

            for char in self.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))

            time.sleep(random.uniform(0.5, 1.5))
            password_field.send_keys(Keys.RETURN)

            return self.wait_for_login_completion()

        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def wait_for_login_completion(self, timeout=300):
        print(f"Waiting for login completion (timeout: {timeout} seconds)...")
        end_time = time.time() + timeout

        while time.time() < end_time:
            try:
                for indicator in [
                    "//div[@aria-label='Create a post']",
                    "//div[@aria-label='Create Post']",
                    "//span[text()='Create post']",
                    "//div[contains(@class, 'x1lliihq')]//div[@role='button']"
                ]:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.XPATH, indicator)))
                        print("Login successful!")
                        return True
                    except:
                        continue

                for captcha_text in ["Security check", "Prove you're not a robot", "Enter Security Code"]:
                    try:
                        if self.driver.find_element(By.XPATH,
                                                    f"//h2[contains(text(), '{captcha_text}')]").is_displayed():
                            print("CAPTCHA detected! Please solve it manually...")
                            input("Press Enter after solving the CAPTCHA...")
                            break
                    except:
                        pass

            except Exception as e:
                print(f"Waiting for login... ({str(e)})")

            time.sleep(5)

        print("Login completion timeout reached")
        return False

    def create_post(self, content):
        try:
            print(f"Attempting to create post on your timeline: {content[:50]}...")
            self.driver.get("https://www.facebook.com")
            time.sleep(random.uniform(4, 6))

            create_post_selectors = [
                "//span[contains(text(), \"What's on your mind\")]",
                "//div[@aria-label='Create a post']",
                "//div[@role='button']//span[contains(text(), \"What's on your mind\")]",
                "[aria-label='Create a post']",
                "//div[contains(@class, 'x1lliihq')]//div[@role='button']"
            ]

            post_input = None
            for selector in create_post_selectors:
                try:
                    post_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    post_input.click()
                    break
                except:
                    continue

            if not post_input:
                raise Exception("Could not find the post creation area")

            time.sleep(random.uniform(2, 3))

            input_field_selectors = [
                "//div[@role='textbox' and @contenteditable='true']",
                "//div[@aria-label=\"What's on your mind?\"]",
                "//div[contains(@class, 'notranslate')][@role='textbox']"
            ]

            input_field = None
            for selector in input_field_selectors:
                try:
                    input_field = self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    break
                except:
                    continue

            if not input_field:
                raise Exception("Could not find the post input field")

            input_field.clear()
            for char in content:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.01, 0.05))

            time.sleep(random.uniform(2, 3))

            post_button_selectors = [
                "//div[@aria-label='Post']",
                "//span[text()='Post']//ancestor::div[@role='button']",
                "[aria-label='Post']"
            ]

            post_button = None
            for selector in post_button_selectors:
                try:
                    post_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    post_button.click()
                    break
                except:
                    continue

            if not post_button:
                raise Exception("Could not find the post button")

            time.sleep(5)
            print(f"Successfully posted to your timeline: {content[:30]}...")
            return True

        except Exception as e:
            print(f"Failed to create post: {str(e)}")
            return False

    def create_comment(self, content, url):
        try:
            print(f"Attempting to reply to a comment  {content[:50]}...")
            self.driver.get(url)
            time.sleep(random.uniform(4, 6))

            create_post_selectors = [
                "//div[@role='textbox' and contains(@class, 'notranslate')]",  # Editable reply box
                ''' 
                "//span[contains(text(), \"What's on your mind\")]",
                "//div[@aria-label='Create a post']",
                "//div[@role='button']//span[contains(text(), \"What's on your mind\")]",
                "[aria-label='Create a post']",
                "//div[contains(@class, 'x1lliihq')]//div[@role='button']",

                ">Write a comment…</div>",
                '"comment_composer_placeholder":"Write a comment"',
                'aria - label = "Write a comment…"',
                'aria-placeholder="Write a comment…"></div>',
                "//div[@aria-label='Write a reply…']",  # Most common reply input field
                "//div[@role='textbox' and contains(@class, 'notranslate')]",  # Editable reply box
                "//div[contains(@class, 'x1i10hfl') and @role='textbox']",  # New Facebook UI structure
                "//div[contains(@data-testid, 'ufi_reply_composer')]",
                '''

            ]

            # Scroll down to load posts
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(3)

            # Find and click the first "Reply" button (expands reply box)
            reply_buttons = self.driver.find_elements(By.XPATH, "//span[text()='Reply']")
            if reply_buttons:
                reply_buttons[0].click()
                time.sleep(2)

            # Locate and interact with the reply box
            for selector in create_post_selectors:
                try:
                    reply_box = self.driver.find_element(By.XPATH, selector)
                    reply_box.click()
                    time.sleep(1)
                    reply_box.send_keys(content)  # Type the reply
                    time.sleep(1)
                    reply_box.send_keys(Keys.RETURN)  # Submit reply
                    print("Reply posted successfully!")
                    break
                except:
                    print(f"Selector {selector} did not work, trying next...")
        except Exception as e:
            print(f"Failed to create post: {str(e)}")
            return False

    
    def create_post_with_retry(self, content, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                if self.create_comment(content, url):  #create post
                    return True
                else:
                    print(f"Post attempt {attempt + 1} failed. Retrying...")
                    time.sleep(5)
            except Exception as e:
                print(f"Error during post attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)
                else:
                    print("Max retries reached. Moving to next post.")
        return False

    def setup_gemini(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def load_previous_posts(self):
        try:
            with open('previous_posts.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()

    def save_previous_posts(self):
        with open('previous_posts.json', 'w') as f:
            json.dump(list(self.previous_posts), f)

    def generate_wrap_complaint(self, original_complaint):
        print("Generating new post content using Gemini AI")
        return self.model.generate_content(original_complaint).text.strip()

    def generate_post_content(self):
        print("Generating new post content using Gemini AI")
        max_attempts = 10
        for attempt in range(max_attempts):
            response = self.model.generate_content(self.post_prompt)
            new_post = response.text.strip()
            post_hash = hashlib.md5(new_post.encode()).hexdigest()

            if post_hash not in self.previous_posts:
                self.previous_posts.add(post_hash)
                print(f"Generated new unique post (attempt {attempt + 1}): {new_post[:50]}...")
                return new_post
            else:
                print(f"Generated post was similar to a previous one (attempt {attempt + 1}), regenerating...")

        print(f"Failed to generate a unique post after {max_attempts} attempts.")
        return None

    def countdown_timer(self, seconds):
        for remaining in range(seconds, 0, -1):
            sys.stdout.write(f"\rNext post in: {remaining:2d} seconds")
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write("\rPreparing to post now!            \n")
        sys.stdout.flush()

    def run(self):
        print("Starting Facebook AutoPost script for timeline posts")
        if not self.login():
            print("Could not login. Stopping automation.")
            return

        post_count = 0
        print("Entering main posting loop for timeline posts")
        try:
            while True:
                print(f"Generating timeline post {post_count + 1}")
                post_content = self.generate_post_content()
                if post_content is None:
                    print("Failed to generate unique content. Waiting before next attempt.")
                    self.countdown_timer(self.post_interval)
                    continue

                print(f"Attempting to post content to your timeline: {post_content[:100]}...")
                if self.create_post_with_retry(post_content):
                    post_count += 1
                    print(f"Timeline post {post_count} completed successfully.")
                    print(f"\nTimeline post {post_count} completed. Content: {post_content[:100]}...")
                    self.save_previous_posts()
                    print("Starting countdown for next timeline post.")
                else:
                    print("Timeline post failed after multiple attempts.")
                    print("\nTimeline post failed. Moving to next post after countdown.")
                self.countdown_timer(self.post_interval)

        except KeyboardInterrupt:
            print("\nScript stopped by user")
        finally:
            print("Closing browser and ending script")
            self.driver.quit()

    def make_a_comment_on_facebook(self, original_complaint, url):
        print("Starting Facebook AutoPost script for comments for url=" + url)
        if not self.login():
            print("Could not login. Stopping automation.")
            return

        post_count = 0
        print("Entering main posting loop for timeline posts")
        try:
            while True:
                print(f"Generating timeline post {post_count + 1}")
                post_content = self.generate_wrap_complaint(original_complaint)
                if post_content is None:
                    print("Failed to generate unique content. Waiting before next attempt.")
                    self.countdown_timer(self.post_interval)
                    continue

                if post_count ==1:
                    break
                post_count += 1

                print(f"Attempting to post content to your timeline: {post_content[:100]}...")
                if self.create_post_with_retry(post_content, url):
                    print(f"Timeline post {post_count} completed successfully.")
                    print(f"\nTimeline post {post_count} completed. Content: {post_content[:100]}...")
                    self.save_previous_posts()
                    print("Starting countdown for next timeline post.")
                else:
                    print("Timeline post failed after multiple attempts.")
                    print("\nTimeline post failed. Moving to next post after countdown.")
                self.countdown_timer(self.post_interval)

        except KeyboardInterrupt:
            print("\nScript stopped by user")
        finally:
            print("Closing browser and ending script")
            self.driver.quit()


if __name__ == "__main__":
    config = RawConfigParser()
    config.read('config.ini')

    email = config.get('Facebook', 'email')
    password = config.get('Facebook', 'password')
    gemini_api_key = config.get('Gemini', 'api_key')
    post_prompt = config.get('PostGeneration', 'prompt')
    post_interval = config.getint('Automation', 'post_interval')
    profile_name = config.get('Automation', 'profile_name')

    bot = FacebookAutoPost(
        email=email,
        password=password,
        gemini_api_key=gemini_api_key,
        post_prompt=post_prompt,
        post_interval=post_interval,
        profile_name=profile_name
    )

    bot.make_a_comment_on_facebook("I got a voucher and tried to use but website is faulty",
                                   "https://www.facebook.com/SouthwestAir")
    # .run())
