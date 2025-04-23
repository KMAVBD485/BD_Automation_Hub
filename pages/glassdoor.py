import streamlit as st
import pandas as pd
import time
import re
import requests
from bs4 import BeautifulSoup
import json

st.set_page_config(page_title="Payreto Glassdoor Review Scraper", layout="centered")
st.title("💼 Payreto Glassdoor Review Scraper")

URL = st.text_input("Enter Glassdoor Review URL", 
    "https://www.glassdoor.com/Reviews/PAYRETO-Services-Reviews-E1292599.htm"
)

def scrape_data(url):
    try:
        # Use requests instead of Selenium
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Make request to get main page
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Failed to access URL. Status code: {response.status_code}")
            return []
            
        st.info("Successfully accessed Glassdoor page. Processing data...")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract review data
        reviews = []
        review_containers = soup.select("div[data-test='review-details-container']")
        
        # If we can't find reviews with the selector, it might be behind JavaScript
        if not review_containers:
            st.warning("Could not find reviews with basic selectors. Glassdoor likely requires JavaScript.")
            st.info("Attempting to extract data from page source JSON...")
            
            # Try to find Apollo state in the HTML
            apollo_state_pattern = re.compile(r'apolloState":(.*?),"gdGlobal', re.DOTALL)
            match = apollo_state_pattern.search(response.text)
            
            if match:
                try:
                    apollo_data = json.loads(match.group(1))
                    
                    # Extract review data from Apollo state
                    for key, value in apollo_data.items():
                        if isinstance(value, dict) and "rating" in value and "reviewBody" in value:
                            try:
                                reviews.append({
                                    "Reviewee Position": value.get("jobTitle", ""),
                                    "Employee Status": value.get("employmentStatus", ""),
                                    "Reviewee Location": value.get("location", ""),
                                    "Rating": value.get("rating", ""),
                                    "Date of Review": value.get("reviewDateTime", ""),
                                    "Content Headline": value.get("headline", ""),
                                    "Pros": value.get("pros", ""),
                                    "Cons": value.get("cons", ""),
                                    "Recommended": value.get("recommendToFriend", "No Answer"),
                                    "CEO Approval": value.get("ceoApproval", "No Answer"),
                                    "Business Outlook": value.get("businessOutlook", "No Answer")
                                })
                            except Exception as e:
                                st.warning(f"Error processing a review from Apollo data: {e}")
                except Exception as e:
                    st.error(f"Error parsing Apollo data: {e}")
        else:
            st.info(f"Found {len(review_containers)} review containers")
            
            # Process each review container
            for container in review_containers:
                try:
                    # Extract data from HTML
                    rating_elem = container.select_one("span[data-test='review-rating-label']")
                    date_elem = container.select_one("span.timestamp_reviewDate__dsF9n")
                    title_elem = container.select_one("h3[data-test='review-details-title']")
                    author_elem = container.select_one("span.review-avatar_avatarLabel__P15ey")
                    
                    # Extract additional data
                    pros_elem = container.select_one("span[data-test='review-text-PROS']")
                    cons_elem = container.select_one("span[data-test='review-text-CONS']")
                    
                    reviews.append({
                        "Reviewee Position": author_elem.text if author_elem else "",
                        "Employee Status": container.select_one("div[data-test='review-avatar-tag']:first-child .text-with-icon_LabelContainer__xbtB8").text if container.select_one("div[data-test='review-avatar-tag']:first-child .text-with-icon_LabelContainer__xbtB8") else "",
                        "Reviewee Location": "",  # Hard to get reliably with BS4
                        "Rating": rating_elem.text if rating_elem else "",
                        "Date of Review": date_elem.text if date_elem else "",
                        "Content Headline": title_elem.text if title_elem else "",
                        "Pros": pros_elem.text if pros_elem else "",
                        "Cons": cons_elem.text if cons_elem else "",
                        "Recommended": "No Answer",  # Hard to determine without JavaScript execution
                        "CEO Approval": "No Answer",
                        "Business Outlook": "No Answer"
                    })
                except Exception as e:
                    st.warning(f"Error processing a review container: {e}")
        
        return reviews

    except Exception as e:
        import traceback
        st.error(f"Error processing data: {e}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return []

if st.button("Scrape Glassdoor Reviews"):
    with st.spinner("Scraping reviews... Please wait."):
        data = scrape_data(URL)
        if data:
            df = pd.DataFrame(data)
            st.success(f"Scraped {len(df)} reviews!")
            st.dataframe(df)
            
            # Add download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="glassdoor_reviews.csv",
                mime="text/csv",
            )
        else:
            st.error("No data scraped. Please check the URL or try again later.")
            
            # Add alternative approach suggestion
            st.info("""
            **Alternative Approach:**
            
            Since Glassdoor may be blocking scraping attempts, you might want to:
            
            1. Install the required packages on your server:
               ```
               pip install selenium-wire
               apt-get update && apt-get install -y chromium-browser
               ```
            
            2. Or switch to using a Selenium-based scraper on your local machine instead of the cloud deployment.
            """)
