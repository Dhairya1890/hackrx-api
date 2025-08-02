import requests

# ✅ API Endpoint
url = "https://hackrx-api-sycy.onrender.com/query"

# ✅ File Path
file_path = r"C:\Users\Priyanka Shahani\OneDrive\Desktop\HackRx\documents\BAJHLIP23020V012223.pdf"


# ✅ Request Payload
data = {
    "query": "46-year-old male, knee surgery in Pune, 3-month-old insurance policy",
    "session_id": "session1"
}

# ✅ Send Request with File Upload
with open(file_path, "rb") as f:  # <-- Use "rb" for binary
    files = {"files": (file_path.split("/")[-1], f, "application/pdf")}
    response = requests.post(url, data=data, files=files)

# ✅ Print Result
print("Status Code:", response.status_code)
print("Response:")
print(response.text)
