import streamlit as st
import pandas as pd
import time
import re
import undetected_chromedriver as uc
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

st.set_page_config(page_title="Payreto Glassdoor Review Scraper", layout="centered")
st.title("💼 Payreto Glassdoor Review Scraper")

URL = st.text_input("Enter Glassdoor Review URL", 
    "https://www.glassdoor.com/Reviews/PAYRETO-Services-Reviews-E1292599.htm"
)

def scrape_data(url):
    try:
        options = uc.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        driver.get(url)
        time.sleep(30)

        def scroll_reviews():
            try:
                for _ in range(10):
                    driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
                    time.sleep(2)
            except:
                pass

        scroll_reviews()

        def extract_reviews():
            reviews = []
            review_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-test='review-details-container']")
            for review in review_elements:
                try:
                    rating = review.find_element(By.CSS_SELECTOR, "span[data-test='review-rating-label']").text
                    date = review.find_element(By.CSS_SELECTOR, "span.timestamp_reviewDate__dsF9n").text
                    title = review.find_element(By.CSS_SELECTOR, "h3[data-test='review-details-title']").text
                    author = review.find_element(By.CSS_SELECTOR, "span.review-avatar_avatarLabel__P15ey").text

                    try:
                        employment_status = review.find_element(By.CSS_SELECTOR, "div[data-test='review-avatar-tag']:first-child .text-with-icon_LabelContainer__xbtB8").text
                    except:
                        employment_status = ""

                    try:
                        location = review.find_element(By.CSS_SELECTOR, 
                            "div[data-test='review-avatar-tag'] .text-with-icon_TextWithIcon__5ZZqT:has(svg) .text-with-icon_LabelContainer__xbtB8").text
                    except:
                        location = ""

                    try:
                        pros = review.find_element(By.XPATH, ".//span[@data-test='review-text-PROS']").text
                    except:
                        pros = ""

                    try:
                        cons = review.find_element(By.XPATH, ".//span[@data-test='review-text-CONS']").text
                    except:
                        cons = ""

                    try:
                        experience_container = review.find_element(By.CSS_SELECTOR, "div.review-details_experienceContainer__2W06X")

                        def get_status(div):
                            class_attr = div.get_attribute("class")
                            if "positive" in class_attr:
                                return "Yes"
                            elif "negative" in class_attr:
                                return "No"
                            elif "neutral" in class_attr:
                                return "Neutral"
                            else:
                                return "No Answer"

                        recommended = get_status(experience_container.find_element(By.CSS_SELECTOR, "div:nth-child(1)"))
                        ceo_approval = get_status(experience_container.find_element(By.CSS_SELECTOR, "div:nth-child(2)"))
                        business_outlook = get_status(experience_container.find_element(By.CSS_SELECTOR, "div:nth-child(3)"))

                    except:
                        recommended = ceo_approval = business_outlook = "No Answer"

                    reviews.append({
                        "Reviewee Position": author,
                        "Employee Status": employment_status,
                        "Reviewee Location": location,
                        "Rating": rating,
                        "Date of Review": date,
                        "Content Headline": title,
                        "Pros": pros,
                        "Cons": cons,
                        "Recommended": recommended,
                        "CEO Approval": ceo_approval,
                        "Business Outlook": business_outlook
                    })
                except:
                    continue
            return reviews

        reviews_data = extract_reviews()
        driver.quit()
        return reviews_data

    except Exception as e:
        st.error(f"Error initializing browser: {e}")
        return []

if st.button("Scrape Glassdoor Reviews"):
    with st.spinner("Scraping reviews... Please wait."):
        data = scrape_data(URL)
        if data:
            df = pd.DataFrame(data)
            st.success(f"Scraped {len(df)} reviews!")
            st.dataframe(df)
        else:
            st.error("No data scraped. Please check the URL or try again later.")
