# 🪄 Backend Wizards - Stage 1: String Analyzer Service

A RESTful API service for analyzing strings and storing their computed properties.


## 🛠️ Tech Stack

  Component | Technology                                             

  Language  | Python 3.10+                                           
  Framework | Flask                                                  
  Database  | In-memory dictionary (SHA-256 hash used as unique key) 
  Testing   | Manual (Postman)                                       

> **Note:** For production, consider replacing the in-memory dictionary with a persistent store like PostgreSQL or MongoDB.



## 🚀 Setup Instructions (Windows OS)

### 🧾 Prerequisites

* Python 3.10+
* `pip` package manager
* Git (optional, for cloning)



### 🔧 1. Clone the Repository

```bash
git clone [YOUR_GITHUB_REPO_LINK]
cd string-analyzer-service


### 🧪 2. Create & Activate Virtual Environment (Windows)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate
```

---

### 📦 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### ▶️ 4. Run the Application Locally

```bash
# Option 1: Use Flask CLI
flask run

# Option 2: Run the app directly
python app.py
```

The application should now be running at:

```
http://127.0.0.1:5000
```

---

## 🗺️ API Documentation

### 🔹 Base URL (Local)

```
http://127.0.0.1:5000
```

---

## 💻 API Endpoints

### 1. **Analyze/Create String**

* **Endpoint:** `POST /strings`
* **Content-Type:** `application/json`
* **Request Body:**

```json
{
  "value": "string to analyze"
}
```

* **Responses:**

  * ✅ `201 Created`
  * ❌ `400 Bad Request`, `422 Unprocessable Entity`, `409 Conflict`

---

### 2. **Get Specific String**

* **Endpoint:** `GET /strings/<string_value>`
* **Note:** `<string_value>` must be URL-encoded.
* **Responses:**

  * ✅ `200 OK`
  * ❌ `404 Not Found`

---

### 3. **Get All Strings with Filtering**

* **Endpoint:** `GET /strings`

* **Query Parameters:**

    Parameter            | Type    | Example | Description                               

    `is_palindrome`      | boolean | true    | Palindromic strings                       
    `min_length`         | integer | 5       | Min string length                         
    `max_length`         | integer | 20      | Max string length                         
    `word_count`         | integer | 2       | Exact word count                          
    `contains_character` | string  | a       | Strings that contain a specific character 

* **Responses:**

  * ✅ `200 OK`
  * ❌ `400 Bad Request`



### 4. **Natural Language Filtering**

* **Endpoint:** `GET /strings/filter-by-natural-language`

* **Query Parameter:** `query=<natural language query>`

* **Examples:**

  * `?query=strings longer than 5 characters`
  * `?query=palindromic strings that have three words`

* **Responses:**

  * ✅ `200 OK`
  * ❌ `400 Bad Request`, `422 Unprocessable Entity`


### 5. **Delete String**

* **Endpoint:** `DELETE /strings/<string_value>`
* **Note:** `<string_value>` must be URL-encoded.
* **Responses:**

  * ✅ `204 No Content`
  * ❌ `404 Not Found`


## 🧪 Testing with Postman

### 🔸 Postman Collection

A pre-configured Postman collection is included:

* **File:** `String_Analyzer_Service.postman_collection.json`

### 🔹 Recommended Test Steps

1. **Analyze (POST /strings):**

   * Try:

     * A palindrome → `"Madam I'm Elijah"`
     * A single word → `"hello"`
     * A long string → `"This is a much longer test string"`

2. **Get Specific (GET /strings/{string_value})**

   * Retrieve one of the strings above.

3. **Filtered Get (GET /strings):**

   * `?is_palindrome=true`
   * `?min_length=10&max_length=25`
   * `?word_count=1&contains_character=a`

4. **Natural Language (GET /strings/filter-by-natural-language):**

   * `?query=strings longer than 5 characters`
   * `?query=palindromic strings that have three words`

5. **Delete (DELETE /strings/{string_value}):**

   * Delete a string, then try fetching it again (should return 404).


## 🌍 Deployment

* **Deployment URL:**
 https://stringanalyzerservice-production-5cbd.up.railway.app/strings


## 📌 Submission Details
                  
  API Base URL:      https://stringanalyzerservice-production-5cbd.up.railway.app/strings
  GitHub Repo Link:  https://github.com/Kpellehboy/String_Analyzer_Service/tree/master
  Full Name :        Elijah M. Flomo
  Email:             elijahmflomo@gmail.com


