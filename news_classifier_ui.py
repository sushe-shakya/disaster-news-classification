from classifier import classify_news
import streamlit as st

news = st.text_area("Enter the news here")
if st.button("Classify"):
    result = classify_news(news)
    st.success(f"Predicted Category: {result}")
