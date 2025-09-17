import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the main scraping module
from scrape import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from parse import parse_with_ollama
from crawler import WebCrawler

# Get scraping mode for display
SCRAPING_MODE = os.getenv("SCRAPING_MODE", "local")

# Streamlit UI
st.title("PageMiner")

# Show current backend
st.sidebar.info(f"🔧 Mode: {SCRAPING_MODE.title()}")

url = st.text_input("Enter Website URL")

# Sidebar for crawling options
st.sidebar.header("Crawling Options")
crawl_mode = st.sidebar.radio(
    "Select Mode:",
    ["Single Page", "Crawl Multiple Pages"]
)

if crawl_mode == "Crawl Multiple Pages":
    max_pages = st.sidebar.slider("Max Pages to Crawl", 1, 50, 10)
    delay = st.sidebar.slider("Delay Between Requests (seconds)", 0, 10, 2)
    same_domain_only = st.sidebar.checkbox("Same Domain Only", value=True)

# Step 1: Scrape the Website
if st.button("Scrape Website"):
    if url:
        if crawl_mode == "Single Page":
            st.write("Scraping the website...")
            
            # Scrape single page
            dom_content = scrape_website(url)
            body_content = extract_body_content(dom_content)
            cleaned_content = clean_body_content(body_content)
            
            # Store the DOM content in Streamlit session state
            st.session_state.dom_content = cleaned_content
            st.session_state.scraped_urls = [url]
            
        else:
            st.write(f"Starting recursive crawl (max {max_pages} pages)...")
            
            # Create progress display elements
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_container = st.container()
            
            # Real-time stats display
            with stats_container:
                col1, col2, col3, col4 = st.columns(4)
                pages_metric = col1.empty()
                links_metric = col2.empty()
                queue_metric = col3.empty()
                current_metric = col4.empty()
            
            # Progress callback function
            def update_progress(progress_data):
                # Update progress bar
                progress_percentage = progress_data['progress_percentage']
                progress_bar.progress(progress_percentage / 100)
                
                # Update status
                status_text.text(f"🔄 {progress_data['message']}")
                
                # Update metrics
                pages_metric.metric("Pages Scraped", f"{progress_data['visited_count']}/{progress_data['max_pages']}")
                links_metric.metric("Total Links Found", progress_data['total_links_found'])
                queue_metric.metric("Queue Size", progress_data['queue_size'])
                
                if progress_data['current_url']:
                    # Truncate long URLs for display
                    display_url = progress_data['current_url']
                    if len(display_url) > 50:
                        display_url = display_url[:47] + "..."
                    current_metric.text(f"Current: {display_url}")
            
            # Initialize crawler with progress callback
            crawler = WebCrawler(
                max_pages=max_pages,
                delay=delay,
                same_domain_only=same_domain_only,
                progress_callback=update_progress
            )
            
            # Start crawling
            scraped_data = crawler.crawl_website(url)
            
            # Get final results
            all_content = crawler.get_all_content()
            crawl_stats = crawler.get_crawl_stats()
            
            # Store in session state
            st.session_state.dom_content = all_content
            st.session_state.scraped_urls = crawl_stats['visited_urls']
            st.session_state.crawl_stats = crawl_stats
            
            # Final status
            progress_bar.progress(1.0)
            status_text.text(f"Crawling completed! Scraped {crawl_stats['pages_scraped']} pages, discovered {crawl_stats['total_links_discovered']} links")
            
            # Show detailed stats
            st.success(f"Successfully crawled {crawl_stats['pages_scraped']} pages")
            
            with st.expander("Crawling Statistics"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pages Scraped", crawl_stats['pages_scraped'])
                    st.metric("Completion %", f"{crawl_stats['completion_percentage']:.1f}%")
                with col2:
                    st.metric("Total Links Found", crawl_stats['total_links_discovered'])
                    st.metric("Remaining in Queue", crawl_stats['pages_in_queue'])

        # Display the scraped content
        with st.expander("View Scraped Content"):
            if crawl_mode == "Crawl Multiple Pages" and "crawl_stats" in st.session_state:
                # Show content from multiple pages with navigation
                if st.session_state.crawl_stats['pages_scraped'] > 1:
                    st.info(f"Content from {st.session_state.crawl_stats['pages_scraped']} pages combined")
                
            st.text_area("Content", st.session_state.dom_content, height=400)
        
        # Show scraped URLs
        if "scraped_urls" in st.session_state and len(st.session_state.scraped_urls) > 0:
            with st.expander(f"Scraped URLs ({len(st.session_state.scraped_urls)})"):
                for i, scraped_url in enumerate(st.session_state.scraped_urls, 1):
                    st.write(f"{i}. {scraped_url}")
        
        # Show crawling queue (if available)
        if "crawl_stats" in st.session_state and st.session_state.crawl_stats['pages_in_queue'] > 0:
            with st.expander(f"Remaining URLs in Queue ({st.session_state.crawl_stats['pages_in_queue']})"):
                for i, queued_url in enumerate(st.session_state.crawl_stats['remaining_queue'][:10], 1):  # Show first 10
                    st.write(f"{i}. {queued_url}")
                if len(st.session_state.crawl_stats['remaining_queue']) > 10:
                    st.write(f"... and {len(st.session_state.crawl_stats['remaining_queue']) - 10} more")


# Step 2: Ask Questions About the DOM Content
if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse")

    if st.button("Parse Content"):
        if parse_description:
            st.write("Parsing the content...")

            # Parse the content with Ollama
            dom_chunks = split_dom_content(st.session_state.dom_content)
            parsed_result = parse_with_ollama(dom_chunks, parse_description)
            st.write(parsed_result)
