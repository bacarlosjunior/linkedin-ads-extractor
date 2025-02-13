# 🚀 LinkedIn API Data Insertion into Google BigQuery  

## 📌 Introduction  
This project provides an **automated script** to extract campaign data from LinkedIn Ads and insert it into Google BigQuery.  

## ⚙️ Setup  

### 1️⃣ Create a Pub/Sub Topic  
Before deploying the function to the cloud, create a topic in Pub/Sub:  

```bash
gcloud pubsub topics create linkedin_run
```

### 2️⃣ Deploy the Cloud Function  
Deploy the function on Google Cloud Functions to process the data:  

```bash
gcloud functions deploy get_linkedin_data \
  --runtime python39 \
  --trigger-topic linkedin_run \
  --timeout=540 \
  --memory=256MB
```

---

## 🔄 Data Extraction  
Extraction can be done with different time intervals. For the last 90 days, use `past_90`.  

### 🔹 Extraction Command  
In **Cloud Shell**, run:  

```bash
gcloud pubsub topics publish linkedin_run \
  --message="get_linkedin" \
  --attribute=project_id=PROJECT_ID,dataset_id=DATASET_ID,table_id=TABLE_ID,account_id=ACCOUNT_ID,date_preset=DATE_PRESET
```

### 🔹 Parameters  

| Parameter      | Description |
|---------------|--------------|
| **PROJECT_ID**  | GCP project name |
| **DATASET_ID**  | Database name |
| **TABLE_ID**    | BigQuery table name |
| **ACCOUNT_ID**  | LinkedIn Ads account ID |
| **MESSAGE**     | `"get_linkedin"` |
| **DATE_PRESET** | Extraction period (`"past_90"` or `"yesterday"`) |

📌 **Important:**  
- **ACCESS_TOKEN** and **REFRESH_TOKEN** are required for the LinkedIn API and must be in the `ln_cred.json` file.  
- Tokens can be obtained by following the [official LinkedIn documentation](https://docs.microsoft.com/en-us/linkedin/marketing/getting-access).  

---

## 🔑 Access Token Renewal  

The **ACCESS_TOKEN** is automatically renewed if an invalid token error is detected.  
If automatic renewal fails, follow these steps:  

### 🔹 Manual Renewal  
1. Run the renewal script:  

   ```bash
   python refresh_tokens.py
   ```

2. Replace the credentials in the **ln_cred.json** file in Cloud Functions.  
3. Ensure the file is in the correct **bucket** (`extractors-ads`).  

---

## 📅 Daily Extraction Scheduling  

Data extraction can be automated daily by creating a **Cloud Scheduler Job**.  

### 🔹 Creating a Daily Job  
```bash
gcloud beta scheduler jobs create pubsub job_name \
  --time-zone "America/Sao_Paulo" \
  --schedule "1 5 * * *" \
  --topic linkedin_run \
  --message-body "get_linkedin" \
  --attributes project_id=PROJECT_ID,dataset_id=DATASET_ID,table_id=TABLE_ID,account_id=ACCOUNT_ID,date_preset="yesterday"
```

### 🔹 Parameter Explanation  
- **job_name** → Job name, customize as needed.  
- **time-zone** → Defines the time zone (e.g., `America/Sao_Paulo`).  
- **schedule** → Defines the extraction frequency (`1 5 * * *` = every day at 5 AM).  
- **date_preset="yesterday"** → Daily extraction of **the previous day only**.  

---

## 🆘 Troubleshooting  

If something goes wrong and the table needs to be fixed, follow these steps:  

1️⃣ **Clear the table before reloading:**  
```sql
TRUNCATE TABLE `my_project.my_dataset.my_table`
```

2️⃣ **Run the extraction again with `past_90`** to retrieve the last 90 days of data.  

---

## ✍️ Author  
👤 **Carlos Junior**  

---

