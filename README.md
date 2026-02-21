# EVM Blockchain Audit System (Digital Twin)

[![Django Version](https://img.shields.io/badge/Django-4.2-green)](https://www.djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Active-success)](https://github.com/yourusername/evm-blockchain-django)

## Overview

The **EVM Blockchain Audit System** is a high-fidelity "Digital Twin" simulator of the Indian Electronic Voting Machine (EVM) ecosystem. It accurately models the interaction between the **Control Unit (CU)**, **Ballot Unit (BU)**, and **Voter Verifiable Paper Audit Trail (VVPAT)**.

Beyond simulation, this project introduces a **Ballot Audit Module (BAM)** concept—a mechanism to capture and cryptographically verify the raw signals sent between the Ballot Unit and Control Unit, providing a third layer of verification alongside the electronic count and paper trail.

## Features

- **Realistic Simulation**:
  - **Control Unit (CU)**: Manages the flow of voting (Ballot button logic).
  - **Ballot Unit (BU)**: Interactive UI for casting votes with candidate lamps.
  - **VVPAT**: Visual simulation of the paper slip printer (7-second display rule).
- **Cryptographic Security**:
  - Every vote is timestamped and hashed (`SHA-256`) to ensure data integrity.
  - Generates unique Voter Tokens and Signal Hashes.
- **Audit Dashboard**:
  - Real-time comparison of **EVM Electronic Count**, **VVPAT Paper Count**, and **BAM Signal Count**.
  - Visual indicators for discrepancy detection.
- **REST API**:
  - Fully exposed API endpoints for external hardware sensors (like Raspberry Pi) to interact with the simulator.

## 🚀 Blockchain Integration (v2.0)

This version introduces a robust **Immutable Audit Layer** using Hyperledger Fabric. 

- **Smart Contract (Chaincode)**: Records every vote signal as a unique receipt on the ledger.
- **BAM Simulator**: A Python-based bridge that monitors the EVM signals and commits them to the blockchain in real-time.
- **Immutable Log**: Ensures that once a vote is cast, it cannot be altered or deleted from the audit history.

**For setup instructions and technical details, see [README_BLOCKCHAIN.md](./README_BLOCKCHAIN.md).**


## Tech Stack

- **Backend**: Python, Django 4.2, Django REST Framework (DRF)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (No heavy frameworks for speed/realism)
- **Database**: SQLite (Default) / PostgreSQL (Production ready)
- **Security**: Python `hashlib` for signal verification

## Installation & Setup

### Prerequisites
- Python 3.9+ installed.
- Git installed.

### Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Sooryachandiran-git/evm-blockchain-django.git
    cd evm-blockchain-django
    ```

2.  **Create Custom Virtual Environment (Optional)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize Database**
    Run the migration command to set up the SQLite database schema.
    ```bash
    python manage.py migrate
    ```

5.  **Load Simulation Data**
    This script wipes the DB and populates it with a sample Booth (TN-01-001) and Candidates.
    ```bash
    python load_data.py
    ```

6.  **Run the Server**
    ```bash
    python manage.py runserver
    ```

7.  **Access the Dashboard**
    Open your browser and navigate to: `http://127.0.0.1:8000/`

## API Endpoints

The system exposes several REST API endpoints for the simulator:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Main Dashboard Interface |
| `POST` | `/cast-vote/<booth_id>/` | Records a vote, generates VVPAT, and logs signal |
| `GET` | `/status/<booth_id>/` | Returns real-time counts for EVM, VVPAT, and BAM |
| `GET` | `/api/signals/<booth_id>/` | (API) Returns raw BAM signals for external audit |
| `GET` | `/api/results/<booth_id>/` | (API) Returns final candidate vote tallies |

## Project Structure

```bash
evm-blockchain-django/
├── evm/                 # Main Application App
│   ├── models.py        # Database Architecture (Booth, Vote, Signal)
│   ├── views.py         # Business Logic & API Handlers
│   ├── urls.py          # Routing
│   └── templates/       # Frontend UI (HTML)
├── evm_project/         # Django Project Configuration
├── load_data.py         # Data Seeding Script
├── manage.py            # Django Utility
└── requirements.txt     # Dependency List
```
