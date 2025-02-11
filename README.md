# 🚀 Inserção de Dados da API do LinkedIn no Google BigQuery  

## 📌 Introdução  

Este projeto fornece um **script automatizado** para extrair dados de campanhas do LinkedIn Ads e inseri-los no Google BigQuery.  

## ⚙️ Configuração  

### 1️⃣ Criar um tópico Pub/Sub  
Antes de implantar a função na nuvem, crie um tópico no Pub/Sub:  

```bash
gcloud pubsub topics create linkedin_run
```

### 2️⃣ Publicar a Cloud Function  

Implante a função no Google Cloud Functions para processar os dados:  

```bash
gcloud functions deploy get_linkedin_data \
  --runtime python39 \
  --trigger-topic linkedin_run \
  --timeout=540 \
  --memory=256MB
```

---

## 🔄 Extração de Dados  

A extração pode ser feita com diferentes intervalos de tempo. Para os últimos 90 dias, utilize `past_90`.  

### 🔹 Comando para Extração  
No **Cloud Shell**, execute:  

```bash
gcloud pubsub topics publish linkedin_run \
  --message="get_linkedin" \
  --attribute=project_id=PROJECT_ID,dataset_id=DATASET_ID,table_id=TABLE_ID,account_id=ACCOUNT_ID,date_preset=DATE_PRESET
```

### 🔹 Parâmetros  

| Parâmetro      | Descrição |
|---------------|--------------|
| **PROJECT_ID**  | Nome do projeto no GCP |
| **DATASET_ID**  | Nome do banco de dados |
| **TABLE_ID**    | Nome da tabela no BigQuery |
| **ACCOUNT_ID**  | ID da conta de anúncios no LinkedIn |
| **MESSAGE**     | `"get_linkedin"` (fixo) |
| **DATE_PRESET** | Período da extração (`"past_90"` ou `"yesterday"`) |

📌 **Importante:**  
- O **ACCESS_TOKEN** e **REFRESH_TOKEN** são necessários para a API do LinkedIn e devem estar no arquivo `ln_cred.json`.  
- Tokens podem ser obtidos seguindo a [documentação oficial do LinkedIn](https://docs.microsoft.com/en-us/linkedin/marketing/getting-access).  

---

## 🔑 Renovação do Access Token  

A renovação do **ACCESS_TOKEN** ocorre **automaticamente** caso um erro de token inválido seja detectado.  
Se a renovação automática falhar, siga estes passos:  

### 🔹 Renovação Manual  
1. Execute o script de renovação:  

   ```bash
   python refresh_tokens.py
   ```

2. Substitua as credenciais no arquivo **ln_cred.json** da Cloud Functions.  
3. Confirme que o arquivo está no **bucket** correto (`extractors-ads`).  

---

## 📅 Agendamento Diário da Extração  

Podemos automatizar a extração diária dos dados criando um **Cloud Scheduler Job**.  

### 🔹 Criando um Job Diário  
```bash
gcloud beta scheduler jobs create pubsub job_name \
  --time-zone "America/Sao_Paulo" \
  --schedule "1 5 * * *" \
  --topic linkedin_run \
  --message-body "get_linkedin" \
  --attributes project_id=PROJECT_ID,dataset_id=DATASET_ID,table_id=TABLE_ID,account_id=ACCOUNT_ID,date_preset="yesterday"
```

### 🔹 Parâmetros Explicados  
- **job_name** → Nome do job, personalizar conforme necessário.  
- **time-zone** → Define o fuso horário (ex: `America/Sao_Paulo`).  
- **schedule** → Define a frequência da extração (`1 5 * * *` = todos os dias às 5AM).  
- **date_preset="yesterday"** → Extração diária apenas do **dia anterior**.  

---

## 🆘 Solução de Problemas  

Caso algo saia errado e a tabela precise ser corrigida, siga estas etapas:  

1️⃣ **Limpar a tabela antes de uma nova carga:**  
```sql
TRUNCATE TABLE `meu_projeto.meu_dataset.minha_tabela`
```

2️⃣ **Rodar a extração novamente com `past_90`** para recuperar os dados dos últimos 90 dias.  

---

## ✍️ Autor  
👤 **Carlos Junior**  

---
