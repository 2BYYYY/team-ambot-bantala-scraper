
# The web scraper for Bantala

This automates the scraping of volcano bulletin data from PHIVOLCS using Google Cloud services and Selenium.

🛠️ Technologies Used:

- Google Cloud Scheduler – Triggers the scraping process daily at 12:00 PM via a cron job.

- Google Cloud Run Jobs – Hosts and executes the scraper in a Dockerized environment.

- BigQuery – Stores the extracted data for easy access to the RAG Chatbot.

- Vertex AI – Generates embeddings from the scraped data to be used in the RAG Chatbot.

- Selenium + Headless Chrome – Performs the actual scraping of bulletin data from the PHIVOLCS website.


⚙️ Architecture Overview:

Cloud Scheduler triggers the job on a daily schedule (12:00 PM).

Cloud Run Job runs the containerized Selenium scraper.

The scraper fetches the latest bulletin data from the PHIVOLCS website using headless Chrome.

Embedded and Cleaned data is loaded into BigQuery for RAG.

![Frame 47](https://github.com/user-attachments/assets/16f8d2c1-0426-41f4-87c8-691e119d5b57)


🚀 Purpose:

This setup ensures reliable, automated, and scalable scraping of volcanic data for monitoring and real-time reporting through Bantala’s RAG Chatbot.
