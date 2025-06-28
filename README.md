# 🧠 Alex – Experimental Multilingual Chatbot

**Alex** is an experimental, conversational assistant built to explore how modern large language models — such as **Gemini 2.0 Flash** and **Gemini 2.5 Flash** — handle **difficult, low-resource languages like Greek** in chatbot applications.

> ⚠️ **Note:** This project is **not deployed** and is intended solely as a **practice and experimentation tool**. It is not designed for production use.

---

## 🎯 Purpose

The primary goal of **Alex** is to test the capabilities of advanced LLMs in:

* Understanding bilingual or Greek-language queries.
* Using structured tools and data sources in context-aware conversations.
* Synthesizing accurate, natural-sounding responses using both AI and external data.

> ℹ️ Publicly available data from **[ThessalonikiGuide.gr](https://thessalonikiguide.gr)** is used solely for experimentation and testing purposes in this project.

---

## 🧠 What Alex *Could* Do (If Deployed)

* 🛠️ Answer queries about **power & water outages**
* 🎭 List **musical and theatrical performances**
* 🎬 Share current **movie screenings**
* 🏥 Provide **hospital shift schedules**
* 🏛️ Retrieve **Thessaloniki history** via semantic search

---

## 🔧 Tech Stack Overview

| Component             | Technology                                                      |
| --------------------- | --------------------------------------------------------------- |
| **Backend**           | FastAPI (Async Python Web Framework)                            |
| **LLM**               | Gemini 2.0 & 2.5 Flash via `google-generativeai` + `instructor` |
| **Database**          | PostgreSQL + `pgvector` (for semantic search)                   |
| **ORM**               | SQLAlchemy (Async) + SQLModel                                   |
| **Session Memory**    | Redis (Async) via cookie-based sessions                         |
| **Embeddings**        | OpenAI                                                          |
| **Rate Limiting**     | `fastapi-limiter`                                               |
| **Security**          | HTTP security headers middleware                                |
| **Testing**           | `pytest` (unit & integration tests)                             |
| **Dependency Mgmt**   | Poetry                                                          |
| **Deployment Target** | Docker (DigitalOcean-ready, but **not deployed**)               |

---

## 🧪 Key Experiments

* Testing LLM **comprehension of Greek** and bilingual queries.
* Evaluating **agent-style behavior** using tool selection and structured queries.
* Simulating real-world constraints like **session memory**, **rate limiting**, and **data access**.

---

## 📦 Deployment Status

> **Not deployed.** This is a **local, sandbox-style project** for exploring multilingual chatbot workflows using advanced AI models.