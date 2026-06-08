# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- Student Technology Survival Guide

The Student Technology Survival Guide focuses on helping students solve common technology challenges encountered during their academic experience. Information about Wi-Fi access, Microsoft 365, learning management systems, password resets, MFA, printing, device recommendations, and campus technology policies is often scattered across multiple websites and support documents. This system centralizes that knowledge into a searchable guide that provides fast and accurate answers to student technology questions. -->

---

## Documents

The table below reflects the **documents actually collected and indexed** (in `documents/`,
52 chunks total). Where an originally-planned source was unreachable (dead URL, 404, or a
JavaScript-only / scraper-blocked page), a documented substitute was used — noted in the
"Notes" column. Each saved file also records its real source URL in a header at the top.

| #  | File (in `documents/`)        | Source / Publisher                          | Description                                                       | URL                                                                                                                                   | Notes |
| -- | ----------------------------- | ------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| 1  | `xula-password-guide.pdf`     | Xavier University of Louisiana (official)   | Password reset via the Xavier Password Management Tool (OTP flow).| https://www.xula.edu/assets/passwordmanagementtoolguide.pdf                                                                           | Real XULA PDF |
| 2  | `xula-student-resources.txt`  | XULA Office of Technology Administration    | Student IT resources / help desk overview.                        | https://www.xula.edu/itc/student-resources.html                                                                                       | Real XULA page |
| 3  | `xula-network-use-policy.txt` | Xavier University of Louisiana (official)   | Acceptable-use / network use policy (the planned Student Tech Policy). | https://www.xula.edu/centerforequityjustice/network-use-policy.html                                                              | Real XULA page; fills planned source #6 |
| 4  | `mfa-setup.txt`               | Microsoft (official)                        | Setting up Microsoft 365 sign-in for multi-factor authentication. | https://support.microsoft.com/en-us/office/set-up-your-microsoft-365-sign-in-for-multi-factor-authentication-ace1d096-61e5-449b-a875-58eb3d74de14 | Deep link replacing support.microsoft.com homepage |
| 5  | `mfa-authenticator.txt`       | Microsoft (official)                        | Adding accounts to the Microsoft Authenticator app.               | https://support.microsoft.com/en-us/authenticator/how-to-add-your-accounts-to-microsoft-authenticator                                 | |
| 6  | `microsoft365-install.txt`    | Brown University OIT (representative)        | Installing Microsoft 365 / Office apps with a student account.    | https://ithelp.brown.edu/kb/articles/install-microsoft-365-office-apps-for-students-faculty-and-staff                                 | Substitute: M365 education homepage was marketing-only |
| 7  | `canvas-student-guide.txt`    | Brown University OIT (representative)        | Canvas student guide — logging in and coursework basics.          | https://ithelp.brown.edu/kb/articles/canvas-student-guide                                                                             | Substitute: community.canvaslms.com is JS-rendered |
| 8  | `canvas-faq-students.txt`     | UW–Madison KnowledgeBase (representative)   | Canvas FAQ for students (assignments, login, troubleshooting).    | https://kb.wisc.edu/luwmad/93957                                                                                                      | |
| 9  | `phishing-protect.txt`        | Microsoft (official)                        | Recognizing phishing and what to do if you clicked a bad link.    | https://support.microsoft.com/en-us/windows/protect-yourself-from-phishing-0c7ea947-ba98-3bd9-7184-430e1f860a44                       | |
| 10 | `phishing-report.txt`         | Microsoft (official)                        | How to report phishing or junk email in Outlook.                  | https://support.microsoft.com/en-us/office/how-do-i-report-phishing-or-junk-email-e8d1134d-bb16-4361-8264-7f44c853dc6b                | |

**Not yet collected (planned but unreachable / pending manual capture):**
- **XULA Wi-Fi / eduroam connection guide** — no reachable XULA page with actual connection
  steps exists (`password.xula.edu` and `www2.xula.edu` don't resolve; the ITC pages only have
  navigation text). A Brown OIT eduroam guide was tried as a substitute but **removed** because
  it told students to choose "Brown University" and log in with `@brown.edu` — too misleading.
  *Affects eval Q2 (campus Wi-Fi), which now correctly returns "I don't have enough information."*
- **Reddit community sources** (originally rows 11–15: laptop recommendations, Office 365 issues,
  Canvas tips) — Reddit blocks automated fetching; these need manual copy-paste of specific
  `/comments/` threads. *Affects eval Q5 (laptop recommendations).*
- **Campus printing resources** — no reachable source captured yet. *Affects eval Q9.*
- **Student Handbook technology section** — `https://www.xula.edu/student-handbook/` returned 404.


---

## Chunking Strategy

<!-- Chunking Analysis (For Milestone 2)

Small Chunks (200–300 words)

Use for:
FAQs
Password guides
Wi-Fi instructions
MFA setup

Medium Chunks (400–600 words)

Use for:
Student handbook
Technology policies
Canvas documentation

Large Chunks (600–800 words)

Use for:
Reddit discussions
Forum posts
Long troubleshooting guides -->

**Chunk size:** 180 words (fixed, applied to all sources)

**Overlap:** 30 words (~17%)

**Reasoning:** The embedding model `all-MiniLM-L6-v2` truncates any input longer than
256 tokens (roughly 180–200 words). Chunks larger than that would have their tails
silently dropped before embedding, so a fixed 180-word chunk keeps the *entire* chunk
within the model's context window — nothing is lost. A 30-word overlap (~17%) carries a
sentence or two across chunk boundaries so facts that straddle a split (e.g. a password
reset step continuing into the next chunk) are still retrievable. I chose a single fixed
size over the variable per-type sizing in the analysis above because the 400–800 word
"medium/large" tiers would exceed the model's limit and be truncated anyway, which would
defeat the purpose of making them larger.

---

## Retrieval Approach

**Embedding model:**
Embedding model:
all-MiniLM-L6-v2 using sentence-transformers

**Top-k:**
5 chunks per query

**Production tradeoff reflection:**
Production tradeoff reflection:
If this system were deployed for real Xavier University students and cost was not a constraint, I would consider using a more powerful embedding model with better accuracy and longer context support. I would weigh tradeoffs such as retrieval accuracy, response speed, support for technical language, multilingual support, and latency. Since this guide focuses on student technology support, accuracy on IT-related terms like MFA, Wi-Fi, Microsoft 365, Canvas, and password resets would be especially important.
---

## Evaluation Plan

| #  | Question                                                      | Expected Answer                                                                                                                       |
| -- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | How do I reset my school password?                            | Step-by-step instructions for resetting a student account password, including self-service options and help desk contact information. |
| 2  | How do I connect my laptop to campus Wi-Fi?                   | Instructions for joining the campus wireless network, including required credentials, certificates, and troubleshooting tips.         |
| 3  | How do I install Microsoft 365 using my student account?      | Guidance on accessing Microsoft 365, downloading Office applications, activation requirements, and login procedures.                  |
| 4  | What should I do if I receive a phishing email?               | Explanation of common phishing indicators, how to report suspicious messages, and actions to take if a link was clicked.              |
| 5  | What laptop is recommended for college students?              | Recommendations based on academic programs, minimum hardware requirements, operating systems, and budget considerations.              |
| 6  | How do I enroll in Multi-Factor Authentication (MFA)?         | Instructions for setting up MFA using Microsoft Authenticator or other approved methods.                                              |
| 7  | Why can't I log into Canvas or my learning management system? | Troubleshooting steps for login issues, password synchronization problems, and browser-related issues.                                |
| 8  | How do I access my student email account?                     | Instructions for logging into Outlook, configuring mobile devices, and troubleshooting email access issues.                           |
| 9  | Where can I print documents on campus?                        | Information about campus printing locations, printing costs, and available computer labs.                                             |
| 10 | What should I do if my account becomes locked?                | Steps for unlocking an account, contacting support, and preventing future lockouts.                                                   |

---

## Anticipated Challenges

The Student Technology Survival Guide will rely on information gathered from a variety of sources, including official IT documentation, student handbooks, knowledge base articles, and online discussion forums. One challenge is that some documents may contain outdated or conflicting information, particularly community-generated content such as Reddit discussions. This could result in the retrieval system returning inconsistent answers if the most relevant source is not also the most accurate.

Another challenge is chunking large documents effectively. Important information may be spread across multiple sections of a guide or handbook, causing key details to be split across chunk boundaries. If chunks are too small, the retrieval system may miss important context; if they are too large, retrieval accuracy may decrease. Additionally, some queries may retrieve off-topic content if keywords overlap across different technology topics such as email, Wi-Fi, and account management.

A third challenge is maintaining source attribution. Since information will come from multiple documents, it is important that the system correctly identifies which source provided the answer so users can verify the information and trust the results.

---

## Architecture

[Document Ingestion]
Python + BeautifulSoup (.html) + pdfplumber (.pdf) + plain reads (.txt/.md)
        ↓
[Chunking]
Python custom chunk_text() — fixed 180-word window, 30-word overlap
        ↓
[Embedding + Vector Store]
sentence-transformers (all-MiniLM-L6-v2) + ChromaDB
        ↓
[Retrieval]
Similarity search using ChromaDB (top-k = 5)
        ↓
[Generation]
Groq API produces final answer with sources

Short explanation

Your pipeline starts by collecting student technology documents, webpages, PDFs, and FAQs. The documents are cleaned and split into chunks, then converted into embeddings and stored in a vector database. When a student asks a question, the system retrieves the most relevant chunks and sends them to the AI model to generate an answer with source references.

---

## AI Tool Plan

I plan to use ChatGPT to assist with several stages of the project implementation while maintaining responsibility for testing and validating all outputs.

Document Analysis and Planning

Input: Domain summary, source document list, and project requirements from the assignment.
Expected Output: Recommendations for document organization, chunking strategies, retrieval design, and evaluation questions.

Document Chunking

Input: The document structure analysis and chunking strategy section from this planning document.
Expected Output: Python code implementing a chunk_text() function that creates appropriately sized chunks while preserving context and avoiding splitting important information.

Data Processing and Cleaning

Input: Sample documents collected for the project and assignment requirements regarding retrieval quality.
Expected Output: Python scripts for extracting text, cleaning formatting issues, removing unnecessary content, and preparing documents for indexing.

Retrieval System Development

Input: Project requirements, source documents, and chunked data.
Expected Output: Python code for building the retrieval pipeline, generating embeddings, storing vectors, and returning the most relevant chunks for a user query.

Testing and Evaluation

Input: The list of expected questions and anticipated challenges identified in this planning document.
Expected Output: Test cases, evaluation queries, and recommendations for measuring retrieval accuracy and identifying retrieval failures.

Documentation

Input: Completed implementation details, project requirements, and milestone deliverables.
Expected Output: Draft sections for the README file, system architecture descriptions, usage instructions, and project summaries.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
