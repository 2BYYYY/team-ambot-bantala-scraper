import re
import os
import pandas as pd
from typing import Any
from google import genai
from tenacity import retry, stop_after_attempt, wait_random_exponential
from google.cloud import bigquery
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# --- Configuration ---
PHIVOLCS_URL = "https://wovodat.phivolcs.dost.gov.ph/bulletin/list-of-bulletin?vdId=565&type=bulletin&sdate=2021-01-01&edate=&page=1"
PROJECT_ID = "gdg-team-ambot"
REGION = "us-central1"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", REGION)
TEXT_EMBEDDING_MODEL = "text-embedding-005"
TABLE_ID = "gdg-team-ambot.spf_69.bb-main-data-solcha"

# --- Google Clients ---
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
client_bigquery = bigquery.Client()

def setup_driver() -> webdriver.Chrome:
    """Set up and return a headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service("/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_volcano_data(driver: webdriver.Chrome) -> tuple[dict, list]:
    """
    Extract volcano bulletin data from PHIVOLCS website.
    Args:
        driver: The Chrome Webdriver instance used for scraping.
    Returns:
        - data: A dictionary with volcano info.
        - window_handles: A list of browser window handles (the instance of driver.window_handles).
    """
    data = {
        "TYPE_VOLCANO": "NO DATA",
        "BULLETIN_DATE": "NO DATA",
        "ALERT_LEVEL": "NO DATA",
        "ERUPTION": "NO DATA",
        "ACTIVITY": "NO DATA",
        "SEISMICITY": "NO DATA",
        "SULFUR_DIOXIDE_FLUX": "NO DATA",
        "PLUME": "NO DATA",
        "GROUND_DEFORMATION": "NO DATA",
    }

    driver.get(PHIVOLCS_URL)
    wait = WebDriverWait(driver, 20)

    # Get Volcano Type
    try:
        VOLCANO = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[1]")
            )
        )
        data["TYPE_VOLCANO"] = VOLCANO.text
    except Exception as e:
        print(f"Error getting Volcano: {e}")

    # Get Bulletin Date
    try:
        DATE = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[3]")
            )
        )
        data["BULLETIN_DATE"] = DATE.text
    except Exception as e:
        print(f"Error getting Bulletin Date: {e}")

    # Get First Row and Click
    try:
        FIRST_ROW = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[2]/div[3]/div/div/div[2]/form/div/div[3]/div[4]/table/tbody/tr[1]/td[5]")
            )
        )
        FIRST_ROW.click()
    except Exception as e:
        print(f"Error clicking first row: {e}")

    # Switch to New Window
    window_handles = driver.window_handles
    driver.switch_to.window(window_handles[1])

    # Get Parameters
    try:
        PARAMS = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr")
            )
        )
    except Exception as e:
        print(f"Error getting parameters: {e}")
        PARAMS = []

    # Get Alert Level
    try:
        div_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div/div/div[3]/div[2]/div[1]/div[1]/div[2]/table/tbody/tr/td[2]/div")
            )
        )
        data["ALERT_LEVEL"] = div_element.text
    except Exception as e:
        print(f"Error getting alert level: {e}")

    # Loop through Parameters
    for index_params in range(1, len(PARAMS) + 1):
        try:
            TYPE_PARAMS = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr[{index_params}]/td[1]")
                )
            )
            CLEAN = str(TYPE_PARAMS.text.strip().lower())
            TYPE_PARAMS_CLEAN = " ".join(CLEAN.split())

            # The text form each parameters
            DESCRIPTION_PARAMS = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"/html/body/div/div/div[3]/div[2]/div[3]/div/table/tbody/tr[{index_params}]/td[2]/p")
                )
            )

            if TYPE_PARAMS_CLEAN == "eruption":
                data["ERUPTION"] = DESCRIPTION_PARAMS.text
            elif TYPE_PARAMS_CLEAN == "activity":
                data["ACTIVITY"] = DESCRIPTION_PARAMS.text
            elif TYPE_PARAMS_CLEAN == "seismicity":
                data["SEISMICITY"] = DESCRIPTION_PARAMS.text
            elif TYPE_PARAMS_CLEAN == "sulfur dioxide flux":
                data["SULFUR_DIOXIDE_FLUX"] = DESCRIPTION_PARAMS.text
            elif TYPE_PARAMS_CLEAN == "plume":
                data["PLUME"] = DESCRIPTION_PARAMS.text
            elif TYPE_PARAMS_CLEAN == "ground deformation":
                data["GROUND_DEFORMATION"] = DESCRIPTION_PARAMS.text
        except Exception as e:
            print(f"Error processing parameter {index_params}: {e}")

    return data, window_handles

def build_raw_text(data: dict) -> str:
    """
    Format the extracted volcano data into a summary string.
    Args:
        data: A dictionary containing volcano information.
    Returns:
        A formatted string summarizing the volcano bulletin data.
    """
    return (
        f"On {data['BULLETIN_DATE']}, the {data['TYPE_VOLCANO']} volcano had an Alert Level of {data['ALERT_LEVEL']} "
        f"with {data['ERUPTION']} on Eruption and {data['ACTIVITY']} on Activity, the Seismicity recorded {data['SEISMICITY']}, "
        f"a Sulfur Dioxide Flux of {data['SULFUR_DIOXIDE_FLUX']}, the Plume observation was {data['PLUME']} and the status of "
        f"Ground Deformation was {data['GROUND_DEFORMATION']}."
    )

def close_driver(driver: webdriver.Chrome, window_handles: list):
    """Close browser windows and quit driver."""
    driver.close()
    driver.switch_to.window(window_handles[0])
    driver.quit()
    print("Browser closed, beginning to build index")

@retry(wait=wait_random_exponential(multiplier=1, max=120), stop=stop_after_attempt(10))
def get_embeddings(
    embedding_client: Any, embedding_model: str, text: str
) -> list[float]:
    """
    Generate embeddings for text with retry logic for API quota management.
    Args:
        embedding_client: The client object used to generate embeddings.
        embedding_model: The name of the embedding model to use.
        text: The text for which to generate embeddings.
        output_dim: The desired dimensionality of the output embeddings (default is 768).
    Returns:
        A list of floats representing the generated embeddings. Returns None if a "RESOURCE_EXHAUSTED" error occurs.
    Raises:
        Exception: Any exception encountered during embedding generation, excluding "RESOURCE_EXHAUSTED" errors.
    """
    try:
        response = embedding_client.models.embed_content(
            model=embedding_model,
            contents=[text],
        )
        return response.embeddings[0].values
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            return None
        print(f"Error generating embeddings: {str(e)}")
        raise

def clean_text(text: str) -> str:
    """
    Clean text for embedding generation by:
    - Removing non-printable/control characters
    - Normalizing Unicode characters
    - Removing excessive whitespace
    - Lowercasing
    - Optionally removing extra punctuation
    Args:
        text: The input string to be cleaned.
    Returns:
        A cleaned string suitable for embedding generation.
    """
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.lower()
    text = re.sub(r'[\"\'\\]+', '', text)
    return text

def build_index_from_raw_text(
    raw_text: str,
    embedding_client: Any,
    embedding_model: str
) -> pd.DataFrame:
    """
    Build a searchable index from the scraped data.
    Args:
        raw_text: the data scraped.
        embedding_client: The client object used to generate embeddings.
        embedding_model: The name of the embedding model to use.
    Returns:
        A Pandas DataFrame where each row represents a text chunk. The DataFrame includes columns for:
            - 'chunk_text': The text content of the chunk.
            - 'embeddings': The embedding vector for the chunk. (via the embedding model: text-embedding-005)
    Raises:
        ValueError: If no chunks are created from the input document.
        Exception: Any exceptions encountered during file processing are printed to the console and the function continues to the next document.
    """
    all_chunks = []
    try:
        text_done = clean_text(raw_text)
        # Split the text into chunks by a dot
        chunks = [
            sentence.strip() + '.'
            for sentence in text_done.strip().split('.')
            if sentence.strip()
        ]

        for chunk_num, chunk_text in enumerate(chunks):
            embeddings = get_embeddings(
                embedding_client, embedding_model, chunk_text
            )
            # Important to know what chunks did not embed
            if embeddings is None:
                print(f"Error generating embeddings for chunk {chunk_text}")
                continue

            chunk_info = {
                "chunk_text": chunk_text,
                "embeddings": embeddings,
            }
            all_chunks.append(chunk_info)

    except Exception as e:
        print(f"Error processing document: {str(e)}")

    if not all_chunks:
        raise ValueError("No chunks were created from the document")

    return pd.DataFrame(all_chunks)

def upload_to_bigquery(df: pd.DataFrame, table_id: str):
    """
    Upload DataFrame to BigQuery.
    Args:
        df: The dataframe containing text chunks and embeddings.
        table_id: The BigQuery table ID.
    """
    # Ensure the 'embeddings' column contains lists of floats (BigQuery needs arrays of FLOAT)
    # Without this transformation, there will be errors
    df['embeddings'] = df['embeddings'].apply(lambda x: [float(i) for i in x])

    # Set job configuration for BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("chunk_text", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embeddings", "FLOAT64", mode="REPEATED"),
        ],
        write_disposition="WRITE_APPEND",  # NEEDED!!!!: Append data use. OPTIONAL: WRITE_TRUNCATE to overwrite
    )

    job = client_bigquery.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    print(f"Successfully uploaded {len(df)} rows to {table_id}")

def main():
    driver = setup_driver()
    data, window_handles = extract_volcano_data(driver)
    raw_text = build_raw_text(data)
    print(raw_text)
    print("Data Extracted")
    close_driver(driver, window_handles)
    index_df = build_index_from_raw_text(raw_text, embedding_client=client, embedding_model=TEXT_EMBEDDING_MODEL)
    upload_to_bigquery(index_df, TABLE_ID)

if __name__ == "__main__":
    main()