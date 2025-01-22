import requests
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
import csv

# SEC-API and OpenAI API keys
SEC_API_KEY = input("Enter your SEC API key: ").strip()
OPENAI_API_KEY = input("Enter your OpenAI API key: ").strip()

# Headers for SEC filings
HEADERS = {
    "User-Agent": "swing_trader/1.0 (mizelleaustin@gmail.com)"  # Replace with your app name and email
}

# SEC-API Base URL
BASE_URL = "https://api.sec-api.io"

# Fetch SEC filings
def fetch_sec_filings(ticker, form_type="10-K"):
    """Fetch SEC filings for a specific ticker and form type."""
    query = {
        "query": {
            "query_string": {
                "query": f"ticker:{ticker} AND formType:{form_type}"
            }
        }
    }
    url = f"{BASE_URL}?token={SEC_API_KEY}"
    response = requests.post(url, json=query)
    response.raise_for_status()
    data = response.json()

    # Debugging: Summarize the response
    filings = data.get("filings", [])
    print(f"Number of filings fetched: {len(filings)}")
    if filings:
        for i, filing in enumerate(filings[:5]):  # Show details of the first 5 filings
            print(f"Filing {i+1}:")
            print("  Form Type:", filing.get("formType"))
            print("  Filing Date:", filing.get("filingDate"))
            print("  URL:", filing.get("linkToFilingDetails"))
    return data

# Extract filing text
def extract_filing_text(filing_url):
    """Extract text from the filing URL."""
    try:
        response = requests.get(filing_url, headers=HEADERS)
        response.raise_for_status()
        filing_text = response.text
        print(f"Fetched text from {filing_url}, length: {len(filing_text)}")
        # Limit the amount of text processed for performance
        return filing_text[:5000]
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError for {filing_url}: {e}")
        return None
    except Exception as e:
        print(f"Error fetching filing text from {filing_url}: {e}")
        return None

# LangChain setup for analysis
llm = OpenAI(temperature=0.7, openai_api_key=OPENAI_API_KEY)

# Prompt template for summarization
prompt = PromptTemplate(
    input_variables=["filing_text"],
    template=(
        "Analyze the following SEC filing for trade-relevant insights:\n\n{filing_text}\n\n"
        "Identify financial risks, opportunities, and any significant changes "
        "that might affect stock performance. Provide actionable trade recommendations."
    )
)

# Runnable sequence replaces LLMChain
summarization_chain = RunnableSequence(prompt | llm)

def analyze_filing(filing_text):
    """Analyze the filing text using LangChain."""
    try:
        print("Analyzing filing text...")
        return summarization_chain.invoke({"filing_text": filing_text})
    except Exception as e:
        print(f"Error during analysis: {e}")
        return "Analysis failed."
    
# Save summaries to a CSV file
def save_summaries_to_csv(summaries, output_file="sec_summaries.csv"):
    """Save filing summaries to a CSV file."""
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Filing Number", "Form Type", "Filing URL", "Summary"])
        for i, summary in enumerate(summaries, start=1):
            writer.writerow([i, summary["form_type"], summary["url"], summary["text"]])
    print(f"Summaries saved to {output_file}")

# Process SEC filings
def process_sec_filings(ticker):
    filings = fetch_sec_filings(ticker)
    summaries = []
    if "filings" in filings:
        print("Processing filings:")
        for i, filing in enumerate(filings["filings"][:5]):  # Process up to 5 filings
            filing_url = filing.get("linkToFilingDetails")
            form_type = filing.get("formType")
            print(f"Filing {i+1} URL: {filing_url}")
            if filing_url:
                filing_text = extract_filing_text(filing_url)
                if filing_text:
                    print(f"Analyzing Filing {i+1}...")
                    summary_text = analyze_filing(filing_text)
                    print(f"Summary for Filing {i+1}:\n{summary_text}\n")
                    summaries.append({
                        "form_type": form_type,
                        "url": filing_url,
                        "text": summary_text
                    })
        save_summaries_to_csv(summaries)
    else:
        print("No filings found.")

# Main function
if __name__ == "__main__":
    ticker = "MSFT"  # Replace with the ticker of your choice
    process_sec_filings(ticker)
